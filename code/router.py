#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import socket
from threading import Thread
from threading import Timer
import json

def startRouting():
    t1 = Thread(target = readInput)
    t2 = Thread(target = receiveMsgs)
    update()
    updateRoutes()
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
def readInput():
    for line in sys.stdin:
        command = line.split()
        if command[0] == 'add':
            print("Creating link...")
            destIP = command[1]
            weight = command[2]
            addLink(destIP, weight)
        elif command[0] == 'del':
            print("Removing link...")
            destIP = command[1]
            weight = command[2]
            delLink(destIP, weight)
        elif command[0] == 'trace':
            print("Sending trace message...")
            destIP = command[1]
            sendTraceMsg(destIP)
        elif command[0] == 'table':
            print("Sending table request message...")
            destIP = command[1]
            sendTableRequestMsg(destIP)
        elif command[0] == 'quit':
            print("Exiting...")
            break
        else:
            print("Invalid command.")
    
def receiveMsgs():
    while True:
        msgJSON, senderIP = s.recvfrom(1024)
        msg = json.loads(msgJSON)
        
        msgType = msg['type']
        source = msg['source']
        dest = msg['destination']
        
        if msgType == 'data':
            print("Type: data")
            # Se ele é o destino
            if dest == IP:
                # Imprime o payload
                print(msg['payload'])
            else:
                # Encontra melhor rota para dest na tabela 
                # e envia
                sendMsg(msg, dest)
        elif msgType == 'trace':
            print("Type: trace")
            msg['hops'].append(IP)
            # Se ele é o destino
            if dest == IP:
                print(msg['hops'])
            else:
                # Envia para proximo na rota
                sendMsg(msg, dest)
        elif msgType == 'table':
            print("Type: table")
            # Se ele é o destino
            if dest == IP: 
                # Envia DATA para source com payload
                sendDataMsg(source)
            else:
                sendMsg(msg, dest)
        elif msgType == 'update':
            print("Type: update")
            # Atualiza tabela
            updateTable(source, msg['distances'])            
        else:
            print("Invalid message received.")
            
def addLink(dest, weight):
    dt[dest] = weight
    neighbours.append(dest)
    
def delLink(dest):
    dt[dest] = float('inf')
    neighbours.remove(dest)
    
def sendTableRequestMsg(dest):
    trMsg = {'type': 'table', 'source': IP, 'destination': dest}
    sendMsg(trMsg)
    
def sendTraceMsg(dest):
    traceMsg = {'type': 'trace', 'source': IP, 'destination': dest, 'hops': [IP]}
    sendMsg(traceMsg)
    
def sendUpdateMsg():
    for key in neighbours:
        distL = createDistancesList(key)
        updateMsg = {'type': 'update', 'source': IP, 'destination': key, 'distances': distL}
        sendMsg(updateMsg, key)
        
def sendDataMsg(address):
    pl = createPayload()
    dataMsg = {'type': 'data', 'source': IP, 'destination': address, 'payload': pl}
    sendMsg(dataMsg, address)
        
def createDistancesList(dest):
    dl = []
    for key, value in dt:
        # Não inclui o destino, evitando split horizon
        if key != dest:
            dl.append((key,value))
    return dl
        
def sendMsg(msg, dest):
    msgJSON = json.dumps(msg)
    print("Message sent: "+str(msgJSON))
    router = findNextHop(dest)
    s.sendto(msgJSON, (router,PORT))
    
def update():
    print("Sending update...")
    sendUpdateMsg()
    Timer(pi, update).start()
    

# Cria uma tabela de vetor de distâncias com IPs
# de 127.0.1.1 até 127.0.1.16
def createDistanceTable():
    addressList = ['127.0.1.' for i in range(0,16)]
    
    for i in range(0,16):
        addressList[i] += str(i+1)
    
    dt = {key:float('inf') for key in addressList}
    # Para ele mesmo, o custo é zero
    dt[IP] = 0
    
    return dt

def updateTable(source, distances):
    # Toda vez que atualizar a tabela,
    # Atualiza o tempo?
    # Talvez um contador +1 para que
    # Na hora que der 4pi saiba que a 
    # Rota foi atualizada
    pass
    
def findNextHop(dest):
    # Lembrar de fazer balanceamento de carga aqui
    # Uma hora vai numa rota, outra hora vai na outra
    # Suponha: duas rotas no máximo com mesmo custo
    pass
    
def createPayload():
    # Tuplas com (destino, próx. hop, custo)
    pass
    
def updateRoutes():
    print("Removing old routes...")
    removeOldRoutes()
    Timer(4*pi, updateRoutes).start()
    
def removeOldRoutes():
    # Encontra rotas que não foram atualizadas por 4pi s...?
    # Zera o contador de atualização?
    pass
    
    '''
    Ideia para implementar aquele trem de rotas desatualizadas: 
    coloca um contador pra cada rota, a cada update soma +1 no contador, 
    quando der 4pi, se tiver 4 na rota, ela está atualizada, se não, ela 
    será removida. Aí também todos os contadores serão zerados. 
    Só que isso tem que ser MUITO rápido... Ou para tudo até terminar.
    '''

'''
Inicializaçao 
'''
IP = sys.argv[1]
pi = int(sys.argv[2])
print("IP: "+str(IP)+", PI: "+str(pi))

# Criação do Soquete
HOST = IP
PORT = 55151
address = (HOST,PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(address)

# Criação da Tabela de Distancias e lista de vizinhos
dt = {}
neighbours = []
createDistanceTable()

# Startup
if len(sys.argv) > 3:
    inputFile = sys.argv[3]
    print("Startup: "+str(inputFile))

# Roteamento
try: 
    startRouting()
except KeyboardInterrupt:
    print("Finalizando o programa...")
    s.close()
