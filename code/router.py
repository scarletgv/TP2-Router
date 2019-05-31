#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import socket
from threading import Thread
from threading import Timer
import json
import operator

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
            addLink(destIP, int(weight))
        elif command[0] == 'del':
            print("Removing link...")
            destIP = command[1]
            weight = command[2]
            delLink(destIP, int(weight))
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
        msg = (json.loads(msgJSON.decode('utf-8')))
        
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
                # Tem que enviar de volta pra source
                # Com o payload = hops
                #print(msg['hops'])
                sendDataMsg(source, msg['hops'])
            else:
                # Envia para proximo na rota
                sendMsg(msg, dest)
        elif msgType == 'table':
            print("Type: table")
            # Se ele é o destino
            if dest == IP: 
                # Envia DATA para source com payload
                payload = createPayload
                sendDataMsg(source, payload)
            else:
                sendMsg(msg, dest)
        elif msgType == 'update':
            print("Type: update")
            # Atualiza tabela
            updateTable(msg['distances'], source)     
            print(dt)
        else:
            print("Invalid message received.")
            
def addLink(neighbour, weight):
    dt[neighbour].append({'nxtHop': neighbour, 'weight': weight, 'update': True})
    neighbours.append(neighbour)
    
def delLink(neighbour):
    # Remove todas as rotas que passam pelo vizinho deletado
    # Incluindo todas as rotas do vizinho
    dt[neighbour] = []
    neighbours.remove(neighbour)
    for router in dt:
        if dt[router]:
            for route in dt[router]:
                print(route)
                if route['nxtHop'] == neighbour:
                    dt[router].remove(route)
    
def sendTableRequestMsg(dest):
    trMsg = {'type': 'table', 'source': IP, 'destination': dest}
    nxtH = findNextHop(dest)
    sendMsg(trMsg, nxtH)
    
def sendTraceMsg(dest):
    traceMsg = {'type': 'trace', 'source': IP, 'destination': dest, 'hops': [IP]}
    nxtH = findNextHop(dest)
    sendMsg(traceMsg, nxtH)
    
def sendUpdateMsg():
    for neighbour in neighbours:
        distL = createDistancesList(neighbour)
        nextHop = findNextHop(neighbour)
        updateMsg = {'type': 'update', 'source': IP, 'destination': neighbour, 'distances': distL}     
        sendMsg(updateMsg, nextHop)     
        
def sendDataMsg(dest, payload):
    dataMsg = {'type': 'data', 'source': IP, 'destination': dest, 'payload': payload}
    nxtH = findNextHop(dest)
    sendMsg(dataMsg, nxtH)
        
def createDistancesList(dest):   
    dl = {}
    minWeight = 10000
    for router in dt:
        if router != dest: # Split horizon
            if dt[router]:
                for route in dt[router]:
                    if route['nxtHop'] != dest: # Split horizon
                        if route['weight'] < minWeight:
                            minWeight = route['weight']
                if minWeight < 10000: # Se existe uma rota com menor custo
                    dl[router] = minWeight
                minWeight = 10000
    return dl
        
def sendMsg(msg, dest):
    if dest != '':
        msgJSON = json.dumps(msg)
        print("Message sent: "+str(msgJSON))
        router = findNextHop(dest)
        s.sendto(msgJSON.encode('utf-8'), (router,PORT))
    
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
    
    dt = {key:[] for key in addressList}
    dt[IP] = [{'nxtHop': IP, 'weight': 0, 'update': True}]
    
    return dt

def addNewRoute(router, nextHop, weightNeighbour, weightDest):
    weight = weightNeighbour + weightDest
    dt[router].append({'nxtHop': nextHop, 'weight': weight, 'update': True})
    
        
def updateTable(distances, source):
    neighbourWeight = 0
    
    for route in dt[source]:
        if route['nxtHop'] == source: # É uma rota do vizinho para ele mesmo
            neighbourWeight = route['weight']
            break
        
    for newRoute in distances:
        if dt[newRoute]:
            routes = dt[newRoute].copy()
            for route in routes:
                if newRoute in route:
                    # Existe a rota na lista de rotas
                    if route['nxtHop'] == newRoute: # É uma rota
                        if route['weight'] != distances[newRoute]: 
                            addNewRoute(newRoute, source, neighbourWeight, distances[newRoute])
                        else: # Mesmo peso = Mesma rota
                            # Atualiza a rota
                            # Isto não funciona porque não é a tabela real
                            route['update'] = True
                else:
                    # Não existe a rota na lista, adiciona ela
                    addNewRoute(newRoute, source, neighbourWeight, distances[newRoute])                    
        else:
            #Adiciona nova rota para o destino, usando o vizinho
            addNewRoute(newRoute, source, neighbourWeight, distances[newRoute])  
    

    # Lembrar de fazer balanceamento de carga aqui
    # Uma hora vai numa rota, outra hora vai na outra
    # Suponha: duas rotas no máximo com mesmo custo
def findNextHop(dest):
    minWeight = 10000
    nxtHop = ''
    
    if dt[dest]:
        for route in dt[dest]:
            if route['weight'] < minWeight:
                minWeight = route['weight']
                nxtHop = route['nxtHop']
    return nxtHop    
    
def createPayload():
    pl = []
    for router in dt:
        if dt[router]:
            for route in dt[router]:
                pl.append((router, route['nxtHop'], route['weight']))  
    pl.sort(key = operator.itemgetter(0, 1))
    return pl  

def resetUpdate():
    for router in dt:
        if dt[router]:
            for route in dt[router]:
                route['update'] = False
                '''
                Nova ideia: colocar FALSE só nas rotas
                de update recebidas que não foram 
                informadas
                '''
                    
def removeOldRoutes():
    for router in dt:
        if dt[router]:
            for route in dt[router]:
                if route['update'] == False: # Se a rota não foi atualizada
                    dt[router].remove(route)
    resetUpdate()
    
def updateRoutes():
    print("Removing old routes...")
    removeOldRoutes()
    Timer(4*pi, updateRoutes).start()

def createTopology(file):
    with open(file, "r") as topology:
        for line in topology:
            command = line.split()
            if command[0] == 'add':
                print("Creating link...")
                destIP = command[1]
                weight = command[2]
                addLink(destIP, int(weight))
            elif command[0] == 'del':
                print("Removing link...")
                destIP = command[1]
                weight = command[2]
                delLink(destIP, int(weight))
            else:
                print("Invalid command.")

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
dt = createDistanceTable()
print(dt)

# Startup
if len(sys.argv) > 3:
    inputFile = sys.argv[3]
    print("Startup: "+str(inputFile))
    createTopology(inputFile)

# Roteamento
try: 
    startRouting()
except KeyboardInterrupt:
    print("Ending execution.")
    s.close()
