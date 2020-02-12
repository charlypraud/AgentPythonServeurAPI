import flask
from flask import request
import json
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import mysql.connector
import sys

with open("config.conf","r") as fichier:
    ip = fichier.read()



# import socket
# import os
# gw = os.popen("ip -4 route show default").read().split()
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# s.connect((gw[2], 0))
# ipaddr = s.getsockname()[0]
# gateway = gw[2]
# host = socket.gethostname()
# print ("IP:", ipaddr, " GW:", gateway, " Host:", host)


# ip = socket.gethostbyname(socket.gethostname())

app = flask.Flask(__name__)
app.config['DEBUG'] = True

conn = mysql.connector.connect(host="localhost",user="tests4",password="4NqGjgkZ", database="tests4")
cursor = conn.cursor()

# création de l'objet logger qui va nous servir à écrire dans les logs
loggerClient = logging.getLogger()
loggerClient.setLevel(logging.DEBUG)

# création d'un formateur qui va ajouter le temps, le niveau
# de chaque message quand on écrira un message dans le log
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

# création d'un handler qui va rediriger une écriture du log vers
# un fichier en mode 'append', avec 1 backup et une taille max de 1Mo
file_handler = RotatingFileHandler('./logs/clients.log', 'a', 1000000, 1)        
# on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
# créé précédement et on ajoute ce handler au logger
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
loggerClient.addHandler(file_handler)


@app.route('/api', methods=['POST'])
def home():
    # some JSON:
    x = request.data
    print(x)
    try:
        y = json.loads(x)
#         conn = mysql.connector.connect(host="localhost",user="tests4",password="4NqGjgkZ", database="tests4")
#         cursor = conn.cursor()
        sql = "SELECT idHote from hote where idHote=%s"
        val = (y['id'],)        
        
        cursor.execute(sql,val)
        rows = cursor.fetchall()
        print(rows)
        if not rows:     
            loggerClient.error("L'hote n'existe pas")   
            return json.dumps({'error':"ERREUR : L'hote n'existe pas"})
        else:
            sql = """UPDATE hote SET nom=%s, OS=%s, uptime=%s, noyaux=%s WHERE idHote=%s"""
            val = (y['nomhost'],y['os'],y['uptime'],y['noyau'],y['id'])
            cursor.execute(sql, val)
            conn.commit()
            
            
            sql = """INSERT INTO cpu(idHote, frequence,frequenceMax, type) VALUES (%s, %s, %s, %s)"""
            val = (y['id'],y['cpufrequence'],y['cpufrequencemax'],y['cputype'])
            cursor.execute(sql, val)
            conn.commit()
            cpuId = cursor.lastrowid
            
    
            sql = """INSERT INTO disque(idHote,memoireTotal,memoireLibre,memoireOccupe,buffer,cache) VALUES (%s,%s,%s,%s,%s,%s)"""
            val = (y['id'],y['total'],y['mlibre'],y['moccupe'],y['mbuffer'],y['mcached'])
            cursor.execute(sql, val)
            conn.commit()
            partitionId = cursor.lastrowid
    
            for partition in y['metrique']:
                sql = """INSERT INTO typepartition(idDisque,available,fileSystem,mounted,pourcentage,size,used) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
                val = (partitionId,partition['available'],partition['fileSystem'],partition['mounted'],partition['pourcentage'],partition['size'],partition['used'])
                cursor.execute(sql, val)
                conn.commit()
            
            
            for service in y['service']:
                sql = """SELECT nom FROM service WHERE nom=%s"""
                val = (service['name'])
                cursor.execute(sql, val)
                rows = cursor.fetchall()
                if not rows:
                    sql = """INSERT INTO service(nom) VALUES (%s)"""
                    val = (service['name'],)
                    cursor.execute(sql, val)
                    conn.commit()
                    if service['etat'].lower() == "true":
                        etat = 1
                    else:
                        etat = 0
                    sql = """INSERT INTO servicehote(idHote,idService,etat) VALUES (%s,%s,%s)"""
                    val = (y['id'],cursor.lastrowid,etat)
                    cursor.execute(sql, val)
                    conn.commit()
    
            return y
        
        
    except (RuntimeError, TypeError, NameError, ValueError) as error:
        # création de l'objet logger qui va nous servir à écrire dans les logs
        loggerServeur = logging.getLogger()
        loggerServeur.setLevel(logging.DEBUG)
        
        # création d'un formateur qui va ajouter le temps, le niveau
        # de chaque message quand on écrira un message dans le log
        formatterServeur = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
        # création d'un handler qui va rediriger une écriture du log vers
        # un fichier en mode 'append', avec 1 backup et une taille max de 1Mo
        file_handlerServeur = RotatingFileHandler('./logs/serveur.log', 'a', 1000000, 1)        
        # on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
        # créé précédement et on ajoute ce handler au logger
        file_handlerServeur.setLevel(logging.DEBUG)
        file_handlerServeur.setFormatter(formatterServeur)
        loggerServeur.addHandler(file_handlerServeur)
         
        # Après 3 heures, on peut enfin logguer
        # Il est temps de spammer votre code avec des logs partout :
        loggerServeur.error(error)
        print (error)


@app.route('/api/init', methods=['POST'])
def init():
 
    
    x = request.data
    try:
        y = json.loads(x)
        sql = """SELECT nom from hote where nom=%s"""
        val = (y['nom'],)
        cursor.execute(sql,val)
        rows = cursor.fetchall()
            

        try:
            if not rows:        
                sql = """INSERT INTO hote(nom, OS, uptime, noyaux) VALUES (%s,%s,"","")"""
                val = (y['nom'],y['os'])
                cursor.execute(sql,val)
                conn.commit()
                id = cursor.lastrowid
        
                sql = """SELECT nom from hote where nom=%s"""
                val = (y['nom'],)
                cursor.execute(sql,val)
                rows = cursor.fetchall()
                print(rows)
#                 return json.dumps({'id':id, 'services':[{'name':'bluetooth.service'},{'name':'cron.service'},{'name':'alsa-store.service'}]})
            else:
                sql = """SELECT idHote from hote where nom=%s"""
                val = (y['nom'],)
                cursor.execute(sql,val)
                id = cursor.fetchall()
#                 return json.dumps({'id':rows,'services':[{'name':'bluetooth.service'},{'name':'cron.service'},{'name':'alsa-store.service'}]})
            for i in id:
                idStr = i
            if y['os'] == "Linux":
                return json.dumps({'id':idStr[0], 'services':[{'name':'bluetooth.service'},{'name':'cron.service'},{'name':'alsa-store.service'}]})
            else:
                return json.dumps({'id':idStr[0], 'services':[{'name':'cmd.exe'},{'name':'mpssvc'},{'name':'WSearch'}]})

                
        except:
            loggerClient.error("Mauvaises données")
 


    #     for row in rows:
    #         r = row[0]
#         if not rows:        
#             sql = """INSERT INTO hote(nom, OS, uptime, noyaux) VALUES (%s,"","","")"""
#             val = (x,)
#             cursor.execute(sql,val)
#             conn.commit()
#             id = cursor.lastrowid
#     
#             sql = """SELECT nom from hote where nom=%s"""
#             val = (x,)
#             cursor.execute(sql,val)
#             rows = cursor.fetchall()
#             print(rows)
#             return json.dumps({'id':id, 'services':[{'name':'bluetooth.service'},{'name':'cron.service'},{'name':'alsa-store.service'}]})
#         else:
#             sql = """SELECT idHote from hote where nom=%s"""
#             val = (x,)
#             cursor.execute(sql,val)
#             rows = cursor.fetchall()
#             return json.dumps({'id':rows,'services':[{'name':'bluetooth.service'},{'name':'cron.service'},{'name':'alsa-store.service'}]})
  
    except:
        loggerClient.error("Aucune données envoyées")

        
        
#     if x is not None:    
#         logger.error(x)
#     
# #         print(x)
# #         sql = """SELECT nom from hote where nom=%s"""
# #         val = (x,)
# #         cursor.execute(sql,val)
# #         rows = cursor.fetchall()
# #     #     for row in rows:
# #     #         r = row[0]
# #         if not rows:        
# #             sql = """INSERT INTO hote(nom, OS, uptime, noyaux) VALUES (%s,"","","")"""
# #             val = (x,)
# #             cursor.execute(sql,val)
# #             conn.commit()
# #             id = cursor.lastrowid
# # 
# #             sql = """SELECT nom from hote where nom=%s"""
# #             val = (x,)
# #             cursor.execute(sql,val)
# #             rows = cursor.fetchall()
# #             print(rows)
# #             return json.dumps({'id':id, 'services':[{'name':'bluetooth.service'},{'name':'cron.service'},{'name':'alsa-store.service'}]})
# #         else:
# #             sql = """SELECT idHote from hote where nom=%s"""
# #             val = (x,)
# #             cursor.execute(sql,val)
# #             rows = cursor.fetchall()
# #             return json.dumps({'id':rows,'services':[{'name':'bluetooth.service'},{'name':'cron.service'},{'name':'alsa-store.service'}]})
#     else:
#         logger.error("Aucune donnée envoyée")


# @app.route('/api/id', methods=['GET'])
# def getId():
#     conn = mysql.connector.connect(host="localhost",user="root",password="rtlry", database="ServeurAPI")
#     cursor = conn.cursor()
#     cursor.execute("select idHote from hote where idHote=(select MAX(idHote) from hote)")
#     rows = cursor.fetchall()
#     for row in rows:
#         r = row[0]+1
#     conn.close()
#     return json.dumps({'id':r})


app.run(host = ip)



