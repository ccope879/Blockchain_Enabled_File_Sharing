import hashlib
import json
import socket
import signal
import time
import random
import threading
import sys
import os
import requests
from random import randint
from datetime import datetime
from queue import Queue
import netifaces as ni
import shlex  
from subprocess import Popen, PIPE, STDOUT
import ipaddress
import multiprocessing

#VARIABLES
block_lock = threading.Lock()
client_lock = threading.Lock()

#FILES
clientOut = open('logs/clientOut.txt', 'w') #check what the client is receiving

#FUNCTIONS
def myIP():
    return (ni.ifaddresses('enp0s31f6')[ni.AF_INET][0]['addr'])
    
def acceptconnectportConnection(server): #server method, only for connectport
    requester_socket, requester_address = server.accept()
    print(f"I am server. Accepted connection from {requester_address[0]}:{requester_address[1]}")
    return requester_socket

def acceptConnection(self_samaritan): #self_samaritan method
    neighbor_socket, neighbor_address = self_samaritan.accept()
    print(f"I am self_samaritan. Accepted connection from {neighbor_address[0]}:{neighbor_address[1]}")
    return neighbor_socket

def approveConnection(requester_socket, givenport): #server method
    myip = myIP()
    response = f"accepted. talk on {myip}, port: {givenport}".encode("utf-8") # convert string to bytes
    #givenport = givenport + 1
    #send accept response to the client
    requester_socket.send(response)

def bindasServer(port, server): 
    myip = myIP() # I am the server
    server.bind((myip, port)) # I am the server

def closerequesterConnection(requester_socket): #server method
    time.sleep(0.5) #without the client sees "acceptedclosed"
    senddatatorequester(requester_socket, "closed")
    requester_socket.close()
    print("I am server. Connection to requester closed")

def closesamaritanConnection(client): #client method
    client.send("client closing".encode("utf-8"))
    client.close()
    #write_to_client_out("I am client. Connection to samaritan closed")

def closeserverConnection(initial_client): #initial_client method
    initial_client.send("client closing".encode("utf-8"))
    initial_client.close()
    write_to_client_out("I am initial_client. Connection to server closed")

def extractIP(message): #server method
    ip_split = message.split("on ")
    temp = ip_split[1]
    temp2 = temp.partition(",")
    port_split = message.split("port: ")
    
    client_ip = temp2[0]
    client_port = port_split[1]

    return client_ip, client_port

def listenforLWRequests(port, server): #server method, connectport
    # listen for incoming connections
    server.listen(1)
    server_ip = myIP()
    print(f"I am server. Listening on {server_ip}:{port}")

def listenforRequests(connectport, server): #server method, connectport
    # listen for incoming connections
    server.listen(3)
    server_ip = myIP()
    print(f"I am server. Listening on {server_ip}:{connectport}")

def listenServer(message_queue): #selfsamaritan method listen to server
    try:
        message = message_queue.get(timeout=1)  # Wait for a message
        print(f"received message: {message}")
    except queue.Empty:
        pass  # Continue waiting if queue is empty

def receivedatafromneighbor(neighbor_socket): #server method
    request = neighbor_socket.recv(8192)
    request = request.decode("utf-8") # convert bytes to string
    print(f"I am server. Received: {request}")
    return request

def receivedatafromrequester(requester_socket): #server method
    request = requester_socket.recv(8192)
    request = request.decode("utf-8") # convert bytes to string
    print(f"I am server. Received: '{request}'")
    return request

def receivedatafromsamaritan(client): #client method
    response = client.recv(8192)
    response = response.decode("utf-8")
    write_to_client_out(f"I am client. Received: {response}")
    if response.lower() == "closed":
        closesamaritanConnection(client)
    return response

def receivedatafromserver(initial_client): #initial_client method
    response = initial_client.recv(8192)
    response = response.decode("utf-8")
    write_to_client_out(f"I am initial_client. Received: {response}")
    if response.lower() == "closed":
        closeserverConnection(initial_client)
    return response

def requestConnection(server_ip, server_port, initial_client, givenport): #initial_client method
    try:
        initial_client.connect((server_ip, server_port)) #initial_client requests to connect to server
        myip = myIP()
        message = f"be my neighbor? answer on {myip}, port: {givenport}"
        senddatafrominitialclient(message,initial_client) #initial_client parameter
        # receive message from the server
        response = receivedatafromserver(initial_client)
        initial_client.close()
        #neighbor returns their self_samaritan connect data, which I see as my neighbor
        neighbor_ip, neighbor_port = extractIP(response)
        return neighbor_ip, neighbor_port
    except socket.error:
        return ("failure")

def requestsustainedConnection(samaritan_ip, samaritan_port, client): #client method
    samaritan_port = int(samaritan_port)
    try:
        write_to_client_out(f"Trying to connect to: {samaritan_ip}:{samaritan_port}")
        client.connect((samaritan_ip, samaritan_port)) #client requests to connect to server
    except Exception as e: write_to_client_out(e)

def senddatafromclient(data, client): #client method, buffer size 1024 may need to increase to accomodate blockchain message
    client.send(data.encode("utf-8")[:8192])

def senddatafrominitialclient(data, initial_client): #initial_client method, buffer size 1024 may need to increase to accomodate blockchain message
    initial_client.send(data.encode("utf-8")[:8192])

def senddatatoneighbor(neighbor_socket, data): #samaritan method, buffer size 1024 may need to increase to accomodate blockchain message
    neighbor_socket.send(data.encode("utf-8")[:8192])

def senddatatorequester(requester_socket, data): #server method, buffer size 1024 may need to increase to accomodate blockchain message
    requester_socket.send(data.encode("utf-8")[:8192])

def setreceiveequal(givenport):
    receiveport = givenport
    return receiveport

def write_to_client_out(data):
    with client_lock:
        clientOut.write(data)
        clientOut.flush()
