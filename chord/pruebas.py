import hashlib
import numpy as np
import requests
import json
import time
import sys

from threading import Thread


arg = sys.argv

def envio_request(url,comand):
        headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
        req = requests.post(url+comand, headers=headers)
        return req.json() 
    
        
if(arg[1]=='1'):
    url = 'http://148.247.201.222:'
    # url = 'http://192.168.0.4:'
    # Envio a otro nodo sin datos
    for x in range(13):
        p = 2300+x
        print(url+str(p))
        rec = envio_request(url+str(p),'/INICIAR')
        print(rec)
        
    time.sleep(5)

datas = {
        'K':[3],
        'data_balance':'D',
        'type_balance':'RR',
        'name':'DataPreproces',
        'type_cluster':'Kmeans',
        'workers':int(arg[2])
        }
url = '148.247.201.222:2300/RECIBIR_BALAANCE'
# url = '192.168.0.4:2300/RECIBIR_BALAANCE'
print(url)
nodos = [1,2,3,6,9,12]
# nodos = [1,2]
for n in range(1,13):
    print(n)
    for x in range(2):
        print(x)
        datas = {
            'K':[3],
            'data_balance':'D',
            'type_balance':'RR',
            'name':'DataPreproces',
            'type_cluster':'Kmeans',
            'workers':n
            }
        headers = {'PRIVATE-TOKEN': '<your_access_token>', 'Content-Type':'application/json'}
        req = requests.post('http://'+url,data=json.dumps(datas), headers=headers)
        time.sleep(5)


# envio_request(url+'3','/ESTADO')