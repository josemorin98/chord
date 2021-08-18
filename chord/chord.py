from flask import Flask, request
from flask import Response
from flask import jsonify
# from flask_script import Manager, Server
import json
import threading
import requests
import sys
# import queue
import time
import pandas as pd
from threading import Thread
from csv import writer
# import pandas as pd
import numpy as np
from utils_chord import *
from concurrent.futures import ThreadPoolExecutor
import os

class nodeChord:
    def __init__(self,ip_nodo,porto,total,antesesor,sucesor):
        self.name = conc(ip_nodo, str(porto))
        self.id_nodo = hash(self.name,total)
        self.ip_nodo = ip_nodo
        self.port_nodo = porto
        self.antesesor = antesesor
        self.sucesor = sucesor
        self.sucesor_port = 0
        self.antesesor_port = 0
        
    def url_request(self):
        url = 'http://'+self.name
        return url
    
    def set_antesesor(self,ante,port):
        self.antesesor = ante
        self.antesesor_port = port
        
    def set_sucesor(self,suce,port):
        self.sucesor = suce
        self.sucesor_port = port

# Recibe parametros
arg = sys.argv

# 1 - M         3 - Puerto     5 - Port Base
# 2 - IP        4 - Estatus    6 - workers

# IP - lenovo 192.168.0.4

# Numero de nodos en el anillo
m_nodos = int(arg[1])
# Ip (Estatica por el momento)
ip_nodo = arg[2]
# Puerto
port_nodo = int(arg[3])
port_base = int(arg[5])
# Chord node local
tota = np.power(2,m_nodos)-1
node_local = nodeChord(ip_nodo=ip_nodo,
                       porto=port_nodo,         
                       total=tota,
                       antesesor=0,
                       sucesor=0)
# Total de nodos
nodos_in_m = list()
# Nodos activos
nodos_online = list()
# Estado del nodo
estatus = boolean(arg[4])
# Finger Table
finger_table_list = list()
ref=False
stop_monitor = False

app = Flask(__name__)
app.debug = True


# Monitoreo
def monitoreo():
    global monitor
    monitor.start()

# Funcion infinita para monitoreo
def fun_verificar():
    global node_local
    global nodos_online
    global stop_monitor
    while True:
        try:
            # tiempo de mensajes
            time.sleep(3)
            if (stop_monitor==True):
                break
            else:
                req = envio_request(url=node_local.ip_nodo+':'+str(node_local.sucesor_port),comand='/VERIFICAR')
                app.logger.info('------ ACTIVO ------')
        except requests.exceptions.ConnectionError:
            # Fallo la conexion
            ref = False
            nodos_online = info_all_nodos(nodos_in_m)
            # Se confgura el sucesor y antesesor
            set_sucesor_antesesor(nodos_online)
                      
# global monitor 
monitor = threading.Thread(target=fun_verificar)                       

# Verificacion de actividad
@app.route('/VERIFICAR',methods = ['POST'])
def prueba():
    app.logger.error('------ Verificacion ------')
    return jsonify({'response':'SI'})

# Cambiar de Estado
@app.route('/ESTADO',methods = ['POST'])
def estatus_node():
    global estatus
    global ref
    # Esta activo
    if (estatus==True):
        estatus==False
    else:
        estatuss=True
        init()
        req = envio_request(url=node_local.ip_nodo+':'+str(node_local.sucesor_port),comand='/REFRESH')
        ref = False
    return jsonify({'response':'SI'})

# Actualizar sus datos
@app.route('/REFRESH',methods = ['POST'])
def refresh():
    global ref
    global monitor
    global stop_monitor
    if (monitor.is_alive()):
        stop_monitor = True
    # Fallo la conexion
    nodos_online = info_all_nodos(nodos_in_m)
    # Se confgura el sucesor y antesesor
    set_sucesor_antesesor(nodos_online)
    if (ref == True):
        ref = False
        req = envio_request(url=node_local.ip_nodo+':'+str(node_local.sucesor_port),comand='/REFRESH')
        stop_monitor=False
        app.logger('Hizo su jale')
        time.sleep(5)
        monitoreo()
    return jsonify({'response':'SI'})

# Funcion para obtener puertos
def init_nodos(m):
    global port_base
    nodos = list()
    total = np.power(2,m)-1
    for x in range(2**m):
        if (x<=workers+1):
            aux = nodeChord(ip_nodo,(port_base+x),total,0,0)
            nodos.append(aux)
        else:
            break
    return nodos

# Envio a otro nodo sin datos
def envio_request_witout_return(url,comand,datas):
    headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
    req = requests.post(url+comand, data=json.dumps(datas), headers=headers)
    return 1

# Envio a otro nodos con datos
def envio_request_with_datas(url,comand,datas):
    headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
    req = requests.post(url+comand,data=json.dumps(datas), headers=headers)
    return req.json() 

# Notificacion de los nodos activos
def nodos_online_request(nodos):
    global port_nodo
    # Convierte la lista de objetos a string
    json_string_online = json.dumps([ob.__dict__ for ob in nodos])
    datas = {
        'NODOS': json_string_online
    }
    for x in nodos:
        if (x.port_nodo != port_nodo):
            req = envio_request_with_datas(url=x.url_request(),
                                           comand='/ONLINE',
                                           datas=datas)
    app.logger.info('------ NOTIFICADO ------')
    return 'NOTIFICADO'

# Saber que nodos estan activos
def info_all_nodos(nodos):
    global port_nodo
    nodos_online_= list()
    #  Convierte lista de json to string
    # json_string = json.dumps([ob.__dict__ for ob in nodos])
    datas = {
        'MSJ': 'INCIO'
    }
    for x in nodos:
        if (x.port_nodo != node_local.port_nodo):
            try:
                # app.logger.error('entroooo' + x.url_request())
                req = envio_request_with_datas(url=x.url_request(),
                                           comand='/NODOS',
                                           datas=datas)
                # app.logger.error(req['response'])
                if (req['response']=='OK'): # Guardo los nodos que respondan con un OK
                    # Ultimo nodo añadido es el antesesor
                    nodos_online_.append(x)
                    
            except :
                pass
    app.logger.info('------ RECIBIDOS ------')
    nodos_online_.append(node_local)
    # app.logger.info(nodos_online_)
    nodos_online_ = sorted(nodos_online_, key=lambda chord_node : chord_node.id_nodo)
    return nodos_online_

# Configuramos los nodos antesesores y sucesores
def set_sucesor_antesesor(nodos_online):
    global node_local
    pos = [x.name for x in nodos_online].index(node_local.name)
    app.logger.info('POSICION - ' + str(pos))
    if(pos == 0):
        # Soy el primero
        node_local.set_antesesor(nodos_online[-1].id_nodo, nodos_online[-1].port_nodo)   # Antesesor
        node_local.set_sucesor(nodos_online[1].id_nodo, nodos_online[1].port_nodo)        # Sucesor
    elif(pos == len(nodos_online)-1):
        # Soy el ultimo
        node_local.set_antesesor(nodos_online[pos-1].id_nodo, nodos_online[pos-1].port_nodo)    # Antesesor
        node_local.set_sucesor(nodos_online[0].id_nodo, nodos_online[0].port_nodo)              # Sucesor
    else:
        # Estoy en el intermedio
        node_local.set_antesesor(nodos_online[pos-1].id_nodo, nodos_online[pos-1].port_nodo)    # Antesesor
        node_local.set_sucesor(nodos_online[pos+1].id_nodo, nodos_online[pos+1].port_nodo)      # Sucesor
    
# @app.route('/NOTIFICAR',methods = ['POST'])
def init():
    global nodos_in_m
    global m_nodos
    global nodos_online
    # Obtiene los nodos para m
    nodos_in_m = init_nodos(m_nodos)
    # Se realiza un request a cada nodos para saber si estan activos
    nodos_online = info_all_nodos(nodos_in_m)
    # Se confgura el sucesor y antesesor
    set_sucesor_antesesor(nodos_online)
    # app.logger.error(len(nodos_online))
        
# Recibe los online
@app.route('/ONLINE',methods = ['POST'])
def nodos_linea():
    global nodos_online
    message = request.get_json()
    nodos_online = json.loads(message['NODOS'])
    # Creamos finger table
    app.logger.info(nodos_online)
    return jsonify({'response':'OK'})

# Recibe todos los nodos en m
@app.route('/NODOS',methods = ['POST'])
def nodos_recibidos():
    global nodos_in_m
    global estatus
    message = request.get_json()
    aux_nodos = message['MSJ']
    # app.logger.info(estatus)
    if (estatus == True):
        return jsonify({'response':'OK'})
    else:
        return jsonify({'response':'NO'})

# Clase Finger Table
class fingerTable():
    def __init__(self,llave,valor):
        self.llave = llave
        self.valor = valor

# Crea la tabla finger
def crate_fingerTable():
    global nodos_online
    global m_nodos
    global finger_table_list
    global node_local
    # Creamos finger table
    for pot in range(m_nodos-1):
        # Obtenemos la llave
        llave = node_local.id_nodo + np.power(2,pot)
        # Obtenemos el nodo al que pertenece y este activo
        for nodo in nodos_online:
            if (nodo.id_nodo > node_local.id_nodo):
                if (llave <= (nodo.id_nodo)):
                    valor = (nodo.id_nodo)
                    break
            if (llave > nodos_online[-1].id_nodo):
                valor = nodos_online[0].id_nodo
        aux = fingerTable(llave,valor)
        finger_table_list.append(aux)

# revisa el estatus del nodo
@app.route('/VER_NODO',methods = ['POST'])
def info_nodo():
    global node_local
    # app.logger.info('ID - ' + str(node_local.id_nodo))
    # app.logger.info('Name - ' + str(node_local.name))
    # app.logger.info('IP - ' + str(node_local.ip_nodo))
    # app.logger.info('Port - ' + str(node_local.port_nodo))
    # app.logger.info('Sucesor - ' + str(node_local.sucesor) + ' Port - ' + str(node_local.sucesor_port))
    # app.logger.info('Antesesor - ' + str(node_local.antesesor) + ' Port - ' + str(node_local.antesesor_port))
    datas = {
        'response':'OK',
        'id' : node_local.id_nodo,
        'name': node_local.name,
        'ip':node_local.ip_nodo,
        'port':node_local.port_nodo,
        'sucesor':node_local.sucesor,'sucesor_port':node_local.sucesor_port,
        'antesesor':node_local.antesesor,'antesesor_port':node_local.antesesor_port
    }
    return jsonify(datas)
    
# Muestra la tabla Finger 
@app.route('/VER_FINGER',methods = ['POST'])
def ver_fingerTable():
    global finger_table_list
    global node_local
    app.logger.info('Nodo - ' + str(node_local.id_nodo) + ' Name - ' + node_local.name)
    for obj in finger_table_list:
        app.logger.info('Llave - ' + str(obj.llave) + ' Valor - ' + str(obj.valor))
    return jsonify({'response':'OK'})

# Muestra los nodos
@app.route('/VER_NODOS',methods = ['POST'])
def nodos():
    global nodos_online
    all_nodos = list()
    for x in nodos_online:
        app.logger.info('Nodo - ' + str(x.id_nodo) + ' Name - ' + x.name)
        datas = {
            'id' : x.id_nodo,
            'name': x.name,
            'ip': x.ip_nodo,
            'port': x.port_nodo
        }
        all_nodos.append(datas)
    return jsonify({'response':'OK','info':all_nodos})
        
# Si es el nodo 0 notifica a todos los puertos
@app.route('/INICIAR',methods = ['POST'])
def iniciar():
    init()
    crate_fingerTable()
    # if (estatus == True):
    #     monitoreo()
    # else:
    #     monitoreo()
    return jsonify({'response':'INICIO COMPLETO'})


# --------------------------------------------------------------------------
# CARGA DE TRABAJO

workers = int(arg[6])

@app.route('/IP_NODO',methods=['POST'])
def ip_port_nodo():
    global node_local
    message = request.get_json()
    id_manager = message['id_solicitante']
    num = message['num']-1
    puertos_dis = message['ids']
    id_dis = message['puertos']
    tipo = message['tipo']
    
    # Si mi vecino es el utlimo
    if(num <= 0.0):
        # Me añado
        puertos_dis.append(node_local.port_nodo)
        id_dis.append(node_local.id_nodo)
        # Retorno la lista de id y puertos
        datas = {
            'ids':id_dis,
            'puertos':puertos_dis
        }
        return jsonify(datas)
    else:
    # No soy el ultimo
        datas = {
            'id_solicitante': id_manager,
            'ids':id_dis,
            'puertos':puertos_dis,
            'tipo':tipo,
            'num':num
        }
        if(tipo=='S'):
            req = envio_request_with_datas('http://'+node_local.ip_nodo+':'+str(node_local.sucesor_port),'/IP_NODO',datas)
        elif(tipo=='A'):
            req = envio_request_with_datas('http://'+node_local.ip_nodo+':'+str(node_local.antesesor_port),'/IP_NODO',datas)
        # guardar lo que retorne de listas llenas
        puertos_dis = req['puertos']
        id_dis = req['ids']
        # Me almaceno yo
        puertos_dis.append(node_local.port_nodo)
        id_dis.append(node_local.id_nodo)
        # Hago json de salida
        datas = {
            'ids':id_dis,
            'puertos':puertos_dis
        }
        # retorno actualizados
        return jsonify(datas)


def dame_n_nodos(peers):
    global node_local
    global workers
    global nodos_online
    if (peers<workers):
        # peers necesarios son menos o igual a los disponibles
        if(peers==1):
            puertos = list()
            ids = list()
            puertos.append(node_local.sucesor_port)
            ids.append(node_local.sucesor)
            return puertos, ids
        # mis dos vecinos
        elif(peers==2):
            puertos = list()
            ids = list()
            puertos.append(node_local.sucesor_port)
            puertos.append(node_local.antesesor_port)
            ids.append(node_local.sucesor)
            ids.append(node_local.antesesor)
            return puertos, ids
        # si es par
        elif (par(peers)):
            dib = peers/2
            # Se envia al nodo suscesor y antesesor
            puertos_suc = list()
            puertos_ante = list()
            id_suc = list()
            id_ante = list()
            datas = {
                'id_solicitante': node_local.id_nodo,
                'num':dib,
                'ids':id_suc,
                'puertos':puertos_suc,
                'tipo':'S'
            }
            # sucesor
            req = envio_request_with_datas('http://'+node_local.ip_nodo+':'+str(node_local.sucesor_port),'/IP_NODO',datas)
            puertos_suc = req['puertos']
            id_suc=req['ids']
            # antesesor
            datas = {
                'id_solicitante': node_local.id_nodo,
                'num':dib,
                'ids':id_ante,
                'puertos':puertos_ante,
                'tipo':'A'
            }
            req = envio_request_with_datas('http://'+node_local.ip_nodo+':'+str(node_local.antesesor_port),'/IP_NODO',datas)
            puertos_ante = req['puertos']
            id_ante = req['ids']            
            return (puertos_suc+puertos_ante),(id_suc+id_ante)
        # Es impar
        elif(par(peers)==False):
            dib = (peers-1)/2
            # Se envia al nodo suscesor y antesesor
            puertos_suc = list()
            puertos_ante = list()
            id_suc = list()
            id_ante = list()
            datas = {
                'id_solicitante': node_local.id_nodo,
                'num':dib+1,
                'ids':id_suc,
                'puertos':puertos_suc,
                'tipo':'S'
            }
            # sucesor
            req_suc = envio_request_with_datas('http://'+node_local.ip_nodo+':'+str(node_local.sucesor_port),'/IP_NODO',datas)
            puertos_suc = req_suc['puertos']
            id_suc = req_suc['ids']
            # app.logger.error('Sucesor')
            # app.logger.error(puertos_suc)
            # antesesor
            datas = {
                'id_solicitante': node_local.id_nodo,
                'num':dib,
                'ids':id_ante,
                'puertos':puertos_ante,
                'tipo':'A'
            }
            req_ante = envio_request_with_datas('http://'+node_local.ip_nodo+':'+str(node_local.antesesor_port),'/IP_NODO',datas)
            puertos_ante = req_ante['puertos']
            id_ante = req_ante['ids']
            # app.logger.error('Antesesor')
            # app.logger.error(puertos_ante)
            # app.logger.error((puertos_suc+puertos_ante))
            return (puertos_suc+puertos_ante),(id_suc+id_ante)
    else:
        puertos = list()
        ids = list()
        for x in nodos_online:
            if(node_local.id_nodo!=x.id_nodo):
                puertos.append(x.port_nodo)
                ids.append(x.id_nodo)
        return puertos,ids
    
    
@app.route('/RECIBIR_BALAANCE',methods = ['POST'])
def k_dividir():
    global node_local
    message = request.get_json()

    # Recibe los datos    
    k_ = message['K']
    data_balance = message['data_balance']
    type_balance = message['type_balance']
    type_cluster = message['type_cluster']
    need_peers = message['workers']
    # tiempo inicial
    inicio = time.time()
    # Atrae lo puertos
    puertos_o,ids = dame_n_nodos(need_peers)
    # timpo final
    fin = time.time()
    # añadir tiempos a csv
    append_list_as_row('./data/tiempos_busqueda.csv', [need_peers,(fin-inicio)])
    app.logger.error(fin-inicio)
    
    init_data = init_workres_array(need_peers)
    data_clus = read_CSV(message['name']) # DataPreprocess
    
    # numero AÑOS DIAS O MESES
    type_balance_str = type_blane_cond(data_balance)
    list_balance = data_clus[type_balance_str].unique()
    
    if (type_balance=='RR'): # Balanceador Round Robin
        init_data = RaoundRobin(init_data,list_balance,need_peers)
    elif (type_balance=='PS'):# Balanceador PseudoRandom
        init_data = PseudoRandom(init_data,list_balance,need_peers)
    elif (type_balance=='TC'):# Balanceador TwoChoices
        init_data = TwoChoices(init_data,list_balance,need_peers)
    else:# Balanceador Round Robin
        init_data = RaoundRobin(init_data,list_balance,need_peers)
    
    # app.logger.error(puertos_online)
    peticiones = []
    # inicio=time.time()
    
    # with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
    for x in range(need_peers):
        if (len(init_data[x])>0):
            concac=[]
            for val in init_data[x]:
                # app.logger.info(val)
                concac.append(data_clus[data_clus[type_balance_str]==val])
            data_fin = pd.concat(concac)
            name = "ID_"+str(ids[x])+"_Port_"+str(puertos_o[x])+"_LD="+type_balance+"_DLB="+data_balance
            data_fin.to_csv("./data/"+name+".csv")
            data_clus_n = {"K": k_,
                "name": name,
                "type_cluster":type_cluster,
                "need":need_peers
                }
                
            url = "http://"+node_local.ip_nodo+":"+str(puertos_o[x])
            req = envio_request_witout_return(url,"/CLUSTERING",data_clus_n)
                # process = Thread(target=envio_request_witout_return,args=(url,"/CLUSTERING",data_clus_n))
                # process.start()
                # peticiones.append(process)
                # peticiones.append(multiprocessing.Process(target=envio_request_witout_return,args=(url,"/CLUSTERING",data_clus_n)))
                # executor.submit(envio_request_witout_return,url,"/CLUSTERING",data_clus_n)
            app.logger.error('-----'+str(fin-inicio))
        # for pet in peticiones:        
        #     pet.join()
    return jsonify({'response':'SI'}) 


def prueba_clus(k_,type_cluster,data_clima,name,wor):
    # app.logger.error(k_)
    data_p =data_clima.iloc[:,[7,8,9,10]]
    for k in k_:
        # KMEANS
        if (type_cluster=="Kmeans"):
            # llamado del clustering
            inicio = time.time()
            k_labels,it = K_means(k,data_p)
            cluster="Kmeans"
            fin = time.time()
            app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' ------')
        elif (type_cluster=="GM"):
            inicio = time.time()
            k_labels = MixtureModel(k,data_p)
            cluster="GaussianMixture"
            fin = time.time()
            app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' ------')
        else:
            inicio = time.time()
            k_labels,it = K_means(k,data_p)
            cluster="Kmeans"
            fin = time.time()
            app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' ------')
        # data send
        append_list_as_row('./data/tiempos_carga.csv', [wor,cluster,(fin-inicio)])
        data_clima['clase']=k_labels
        data_clima.to_csv("./data/results/Clus_"+name+"_DataClust_K="+str(k)+"_"+str(cluster)+".csv")
        return 1
        
# cLustering
@app.route('/CLUSTERING',methods = ['POST'])
def clustering():
    message = request.get_json()
    # recibir K
    k_ = message['K']
    name = message['name']
    type_cluster = message['type_cluster']
    wor = message['need']
    
    data_clima = read_CSV(name)
    # data_p =data_clima.iloc[:,[7,8,9,10]]
    # prueba_clus(k_,type_cluster,data_p,name,wor)
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        # app.logger.info('executoooooor')
        executor.submit(prueba_clus,k_,type_cluster,data_clima,name,wor)
        # app.logger.info(executor.result())
    # multi = multiprocessing.Process(target=prueba_clus,args=(k_,type_cluster,data_clima,name))
    # multi.start()
    # for k in k_:
    #     # KMEANS
    #     if (type_cluster=="Kmeans"):
    #         # llamado del clustering
    #         inicio = time.time()
    #         k_labels,it = K_means(k,data_p)
    #         cluster="Kmeans"
    #         fin = time.time()
    #         app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' - '+str(it) +' ------')
    #     elif (type_cluster=="GM"):
    #         inicio = time.time()
    #         k_labels = MixtureModel(k,data_p)
    #         cluster="GaussianMixture"
    #         fin = time.time()
    #         app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' ------')
    #     else:
    #         inicio = time.time()
    #         k_labels,it = K_means(k,data_p)
    #         cluster="Kmeans"
    #         fin = time.time()
    #         app.logger.error('------ '+str(cluster)+" = "+str(fin-inicio) + ' - '+str(it) +' ------')
    #     # data send
    #     append_list_as_row('./data/tiempos_carga.csv', [wor,cluster,(fin-inicio)])
    #     data_clima["clase"]=k_labels
    #     data_clima.to_csv("./data/results/Clus_"+name+"_DataClust_K="+str(k)+"_"+str(cluster)+".csv")
    
    return jsonify({'response':'CLUSTERING TERMINADO'})



def append_list_as_row(file_name, list_of_elem):
    # Open file in append mode
    with open(file_name, 'a+', newline='') as write_obj:
        # Create a writer object from csv module
        csv_writer = writer(write_obj)
        # Add contents of list as last row in the csv file
        csv_writer.writerow(list_of_elem)
if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True)
    