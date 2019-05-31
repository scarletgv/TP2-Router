#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
# =============================================================================
# UFMG - ICEx - DCC - Redes de Computadores - 2019/1
# 
# TP1: DCCRIP -- Protocolo de Roteamento por Vetor de Distância
# 
# Aluna: Scarlet Gianasi Viana
# Matrícula: 2016006891
# 
# Versão utilizada: Python 3.6.7
# =============================================================================

'''

from threading import Thread, Timer
import sys, socket, json, operator, random, signal, os

'''  Inicia as threads de leitura e recebimento de dados
     Assim como as threads de timer para atualizações
     periódicas '''
def startRouting():
    t1 = Thread(target = readInput)
    t1.daemon = True
    t2 = Thread(target = receiveMsgs)
    t2.daemon = True
    update()
    updateRoutes()
    t1.start()
    t2.start()
    
''' Lê cada comando do usuário e realiza a ação requerida.
    Commandos possíveis:
       - add <address> <weight>
       - del <address>
       - trace <address>
       - table <address>
       - quit
'''    
def readInput():
    for line in sys.stdin:
        command = line.split()
        if command[0] == 'add':
            destIP = command[1]
            weight = command[2]
            logging.write("Creating link - IP: "+str(destIP)+", Weight: "+str(weight)+'\n')
            addLink(destIP, int(weight))
        elif command[0] == 'del':
            destIP = command[1]
            logging.write("Removing link - IP: "+str(destIP)+'\n')
            delLink(destIP)
        elif command[0] == 'trace':
            destIP = command[1]
            logging.write("Sending trace message to IP: "+str(destIP)+'\n')
            sendTraceMsg(destIP)
        elif command[0] == 'table':
            destIP = command[1]
            logging.write("Sending table request message to IP: "+str(destIP)+'\n')
            sendTableRequestMsg(destIP)
        elif command[0] == 'quit':
            logging.write("Ending execution."+'\n')
            logging.close()
            os._exit(1)
            break
        else: 
            logging.write("Invalid command."+'\n')

''' Recebe mensagens pelo soquete UDP na porta 55151,
    e as tratas de acordo com seu tipo e destino. '''    
def receiveMsgs():
    while True:
        msgJSON, senderIP = s.recvfrom(1024)
        msg = json.loads(msgJSON.decode('utf-8'))        
        msgType = msg['type']
        source = msg['source']
        dest = msg['destination']
        logging.write("Message received - Type: "+str(msgType)+", Source: "+str(source)+", Destination: "+str(dest)+'\n')
        
        if msgType == 'data':
            if dest == IP:
                logging.write("Router is destination.\n\t- Payload: "+str(msg['payload'])+'\n')
                print(msg['payload'])
            else:
                logging.write("Router is not destination. Sending message to next hop."+'\n')
                sendMsg(msg, dest)
        elif msgType == 'trace':
            msg['hops'].append(IP)
            if dest == IP:
                logging.write("Router is destination. Sending data back to source."+'\n')
                sendDataMsg(source, msg['hops'])
            else:
                logging.write("Router is not destination. Sending message to next hop."+'\n')
                sendMsg(msg, dest)
        elif msgType == 'table':
            if dest == IP: 
                payload = createPayload()
                logging.write("Router is destination. Sending data to source with payload: "+str(payload)+'\n')
                sendDataMsg(source, payload)
            else:
                sendMsg(msg, dest)
        elif msgType == 'update':
            if source in neighbours:
                logging.write("Updating routing table."+'\n')
                updateTable(msg['distances'], source)     
        else:
            logging.write("Invalid message, discarded."+'\n')

''' Adiciona um enlace direto ao roteador. '''            
def addLink(neighbour, weight):
    dt[neighbour].append({'nxtHop': neighbour, 'weight': weight, 'update': True})
    neighbours.append(neighbour)
    
''' Balanceamento de carga '''
def loadBalancing(dest):
    index = random.randint(0,len(loadBalance[dest])-1)
    hop = loadBalance[dest][index]
    return hop

''' Procura rotas com mesmo custo para o mesmo destino
    na tabela de roteamento, e, se existirem, as adicio-
    na na tabela de balanceamento. '''
def checkRoutes(router, nextHop, weight):
    for route in dt[router]:
        if (route['nxtHop'] != nextHop) and route['weight'] == weight:
            addRouteToLoadBalance(router, route['nxtHop'], nextHop)

''' Adiciona uma rota empatada na tabela de balanceamento
    de acordo com seu destino. '''            
def addRouteToLoadBalance(dest, address, hop):
    if dest not in loadBalance:
        loadBalance[dest] = []
    loadBalance[dest].append(address)
    if hop not in loadBalance[dest]:
        loadBalance[dest].append(hop)    

''' Checa a tabela de balanceamento, toda vez que um 
    enlace ou uma rota for removida, para atualizar
    seus valores. '''
def checkBalanceTable(key, address):
    if key in loadBalance:
        if address in loadBalance[key]:
            loadBalance[key].remove(address)
            if len(loadBalance[key]) < 2:
                loadBalance.pop(key, None)    

''' Remove a rota do endereço dado, assim como
    todas as rotas cujo próximo hop seria dado
    pelo endereço. '''    
def delLink(neighbour):
    neighbours.remove(neighbour)
    dt[neighbour] = []
    checkBalanceTable(neighbour, neighbour) 
    for router in dt:
        if dt[router]:
            for route in dt[router]:
                if route['nxtHop'] == neighbour:
                    checkBalanceTable(router, route['nxtHop'])  
                    dt[router].remove(route) 

''' Envia uma requisição de tabela para um destino. '''    
def sendTableRequestMsg(dest):
    trMsg = {'type': 'table', 'source': IP, 'destination': dest}
    nxtH = findNextHop(dest)
    sendMsg(trMsg, nxtH)

''' Envia uma mensagem de rastreamento para um destino. '''    
def sendTraceMsg(dest):
    traceMsg = {'type': 'trace', 'source': IP, 'destination': dest, 'hops': [IP]}
    nxtH = findNextHop(dest)
    sendMsg(traceMsg, nxtH)

''' Envia uma mensagem de update para todos os seus vizinhos. '''    
def sendUpdateMsg():
    for neighbour in neighbours:
        logging.write("Sending update message to "+str(neighbour)+'\n')
        distL = createDistancesList(neighbour)
        nextHop = findNextHop(neighbour)
        updateMsg = {'type': 'update', 'source': IP, 'destination': neighbour, 'distances': distL}     
        sendMsg(updateMsg, nextHop)     

''' Envia uma mensagem de dados para um destino. '''        
def sendDataMsg(dest, payload):
    dataMsg = {'type': 'data', 'source': IP, 'destination': dest, 'payload': payload}
    nxtH = findNextHop(dest)
    sendMsg(dataMsg, nxtH)

''' Cria uma lista de distâncias com as menores rotas
    conhecidas para cada destino conhecido na tabela de
    roteamento. '''        
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
                if minWeight < 10000: 
                    dl[router] = minWeight
                minWeight = 10000
    return dl

''' Envia uma mensagem JSON pelo soquete UDP para
    um próximo hop que alcance o destino, na porta 55151.
    Se não encontrar um roteador que chegue no destino,
    não envia a mensagem. '''        
def sendMsg(msg, dest):
    if dest != '':
        msgJSON = json.dumps(msg)
        logging.write("Message: "+str(msgJSON)+'\n')
        router = findNextHop(dest)
        if router != '':
            s.sendto(msgJSON.encode('utf-8'), (router,PORT))
        else:
            logging.write("Destino não alcançável. Mensagem não enviada.")
            
''' Envia uma mensagem de update para todos os vizinhos
    a cada PI segundos. '''    
def update():
    sendUpdateMsg()
    Timer(pi, update).start()  

''' Cria uma tabela de vetor de distâncias (tabela de roteamento)
    com IPs de 127.0.1.1 até 127.0.1.16 '''
def createDistanceTable():
    addressList = ['127.0.1.' for i in range(0,16)]  
    for i in range(0,16):
        addressList[i] += str(i+1)
    dt = {key:[] for key in addressList}
    dt[IP] = [{'nxtHop': IP, 'weight': 0, 'update': True}]   
    return dt

''' Calcula o peso do vizinho + o peso do destino pelo vizinho
    e adiciona uma rota na tabela de roteamento.
    Função utilizada na atualização de tabelas, toda vez que 
    encontrar novas rotas. '''
def addNewRoute(router, nextHop, weightNeighbour, weightDest):
    weight = weightNeighbour + weightDest
    dt[router].append({'nxtHop': nextHop, 'weight': weight, 'update': True})

''' Dada uma lista de distâncias recebida por um dado vizinho,
    atualiza sua tabela de roteamento de acordo com novas rotas
    encontradas até um destino passando pelo vizinho. '''    
def updateTable(distances, source):
    logging.write("Updating routing table."+'\n')
    if len(neighbours) > 0 and (source in neighbours):
        for route in dt[source]:
            if route['nxtHop'] == source: 
                neighbourWeight = route['weight']
                break
                
        for newRoute in distances:
            if dt[newRoute]:
                routes = dt[newRoute].copy()
                routeInTable = next((item for item in routes if item['nxtHop'] == source), None)
                if routeInTable:
                    for route in routes:
                        if route['nxtHop'] == source: 
                            if route['weight'] != distances[newRoute] + neighbourWeight: 
                                addNewRoute(newRoute, source, neighbourWeight, distances[newRoute])
                            else: 
                                route['update'] = True
                                updateRoute = next((item for item in routes if item['nxtHop'] == route['nxtHop']), None)
                                updateRoute['update'] = True
                else:
                    addNewRoute(newRoute, source, neighbourWeight, distances[newRoute])                    
            else:
                addNewRoute(newRoute, source, neighbourWeight, distances[newRoute])    

''' Encontra um roteador vizinho que possibilite o envio
    de uma mensagem até um destino com o menor custo.
    Chega se o menor custo possui rotas empatadas, caso sim,
    faz o Balanceamento de Carga. Se nenhum rota foi encontrada,
    retorna uma string vazia. '''
def findNextHop(dest):
    minWeight = 10000
    nxtHop = ''
    if dt[dest]:
        for route in dt[dest]:
            if route['weight'] < minWeight:
                minWeight = route['weight']
                nxtHop = route['nxtHop']
    if loadBalance:
        if nxtHop in loadBalance[dest]:
            balancedHop = loadBalancing(dest)
            return balancedHop 
    return nxtHop    

''' Cria o payload de uma mensagem de dados, contendo
    tuplas (destino, próx. hop, peso) de todos os destinos
    da tabela de roteamento. '''    
def createPayload():
    pl = []
    for router in dt:
        if dt[router]:
            for route in dt[router]:
                pl.append((router, route['nxtHop'], route['weight']))  
    pl.sort(key = operator.itemgetter(0, 1))
    return pl  

''' Após cada remoção de rotas desatualizadas, atribui
    a 'update' de cada rota como False, para indicar que
    necessitam ser atualizadas. '''
def resetUpdate():
    for router in dt:
        if dt[router]:
            for route in dt[router]:
                if route['nxtHop'] != IP:
                    route['update'] = False
                    
''' Remove da tabela de roteamento todas as rotas que
    não foram atualizadas em 4*PI segundos (a partir do atributo
    'update'). Também checa se a remoção da rota altera o balan-
    ceamento de carga. '''                  
def removeOldRoutes():
    logging.write("Removing old routes."+'\n')
    for router in dt:
        if dt[router]:
            for route in dt[router]:
                if route['update'] == False: 
                    checkBalanceTable(router, route['nxtHop'])
                    dt[router].remove(route)
    resetUpdate()

''' Chama as rotinas de remoção de rotas desatualizadas
    periodicamente, a cada 4*PI segundos. '''    
def updateRoutes():
    removeOldRoutes()
    Timer(4*pi, updateRoutes).start()

''' Lê comandos de um arquivo de inicialização que
    cria uma topologia inicial da rede de roteadores. '''
def createTopology(file):
    with open(file, "r") as topology:
        for line in topology:
            command = line.split()
            if command[0] == 'add':
                destIP = command[1]
                weight = command[2]
                logging.write("Creating link - IP: "+str(destIP)+", Weight: "+str(weight)+'\n')
                addLink(destIP, int(weight))
            elif command[0] == 'del':
                destIP = command[1]
                logging.write("Removing link - IP: "+str(destIP)+'\n')
                delLink(destIP)
            else:
                logging.write("Invalid command."+'\n')

''' Inicializaçao de variáveis, listas e dicionários globais. '''
# Argumentos de entrada
IP = sys.argv[1]
pi = int(sys.argv[2])
logging = open("logging"+IP, "w")
logging.write("IP: "+str(IP)+", PI: "+str(pi)+'\n')

# Criação do Soquete
HOST = IP
PORT = 55151
address = (HOST,PORT)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(address)

# Criação da Tabela de Distancias, tabela de balanceamento e lista de vizinhos
dt = {}
neighbours = []
loadBalance = {}
dt = createDistanceTable()

# Startup
if len(sys.argv) > 3:
    inputFile = sys.argv[3]
    logging.write("Startup file: "+str(inputFile)+'\n')
    createTopology(inputFile)

# Roteamento
try: 
    mainThread = Thread(target = startRouting)
    mainThread.start()
    signal.pause()
except (KeyboardInterrupt, SystemExit):
    logging.write("Ending execution."+'\n')
    logging.close()
    mainThread.join()
    s.close()
    os._exit(1)
