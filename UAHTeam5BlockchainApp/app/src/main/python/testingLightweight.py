#To run server: python3 posTnet.py
#To run client: nc <ip addr> <port#>

from methods import comm
#from methods import GUI_modulated as GUI

import hashlib
import socket
import signal
import time
import threading
import os
import sys
import netifaces as ni
from subprocess import Popen, PIPE, STDOUT
import multiprocessing
import re
import errno
from random import randint
from datetime import datetime
from queue import Queue
from moralis import evm_api
import requests
import base64
from queue import Queue

# COMM.PY GLOBALS
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #new socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
samaritan = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
self_samaritan = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
neighbor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
initial_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connectport = 11455
givenport = 12455
lightweightport = 13455

#import netifaces as ni

#Import these to use the encryption
import rsa
from cryptography.fernet import Fernet

class Validator:
    def __init__(self, balance, account): # account is an Account object!
        self.address = account.username
        self.balance = balance
        self.role = account.role
        self.fullLegalName = account.fullLegalName

class FileData:
    def __init__(self, ipfsHash, fileName, authorName, accessList):
        self.ipfsHash = ipfsHash
        self.fileName = fileName
        self.authorName = authorName
        self.accessList = accessList

class Account:
    def __init__(self, username, password, role, fullLegalName):
        self.username = username
        self.password = password
        self.role = role
        self.fullLegalName = fullLegalName

class GivenBlock:
    def __init__(self, index, timestamp, prevHash, hash, validatorName, transactionType, payload):
        self.index = index                          # block's position in the blockchain
        self.timestamp = timestamp                  # when block was created (<year>-<mh>-<dy> <hr>:<mi>:<se>.<millis>)
        self.prevHash = prevHash                    # 64-character hash of previous block (blank for genesis)
        self.validatorName = validatorName          # address of the validator (blank for genesis)
        self.hash = hash    # hash for the block
        self.transactionType = transactionType      # either "Upload", "Download", "Create_Account", or "Genesis"
        self.payload = payload                      # ** EITHER FILEDATA OR ACCOUNT OBJECT

# Block represents each 'item' in the blockchain
class Block:
    def __init__(self, index, timestamp, prevHash, validatorName, transactionType, payload):
        self.index = index                          # block's position in the blockchain
        self.timestamp = timestamp                  # when block was created (<year>-<mh>-<dy> <hr>:<mi>:<se>.<millis>)
        self.prevHash = prevHash                    # 64-character hash of previous block (blank for genesis)
        self.validatorName = validatorName          # address of the validator (blank for genesis)
        self.hash = self.calculate_block_hash()     # hash for the block
        self.transactionType = transactionType      # either "Upload", "Download", "Create_Account", or "Genesis"
        self.payload = payload                      # ** EITHER FILEDATA OR ACCOUNT OBJECT
        
        # update this depending on how sign-in/authorization works:
        self.approved_IDs = []

    # calculateHash is a simple SHA256 hashing function
    def calculate_hash(self, s):
        h = hashlib.sha256()
        h.update(s.encode('utf-8'))
        return h.hexdigest()


    # calculateBlockHash returns the hash of all block information
    def calculate_block_hash(self):
        record = str(self.index) + self.timestamp + self.prevHash
        return self.calculate_hash(record)

# Blockchain is a series of validated Blocks
blockchain = []
temp_blocks = []

#Private local blockchain
currentBlockchainData = []

#client tcp address array
nodes = []

# candidate_blocks handles incoming blocks for validation
candidate_blocks = []
candidate_blocks_lock = threading.Lock()

# keep up with all uploaded IPFS hashes and file names
ipfsHashes = []
fileNames = []
accountNames = []
# announcements broadcasts winning validator to all nodes
# hi this is caleb. this list isn't called anywhere but idk the plan for it so
# i'm leaving it in
announcements = []

#targetIP = "146.229.163.145"
loggedIn = False
loggedInLock = threading.Lock()
validatorLock = threading.Lock()
currentLoggedInUserLock = threading.Lock()
candidateBlocks = [] # candidateBlocks handles incoming blocks for validation
candidateBlocksLock = threading.Lock()

# validators keeps track of open validators and balances
# validators = {}
validators = []
validator = Validator(0, Account("", "", "?", "")) # keep track of current validator

apiKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImE0NmE4MmFjLWJlYjEtNGM4MC05MjIwLTIxZDFlNGQ3MGM1NyIsIm9yZ0lkIjoiMzU5ODUyIiwidXNlcklkIjoiMzY5ODMwIiwidHlwZUlkIjoiNTY2M2MwZjAtMmM3Mi00N2YxLWJkMDktNTM1M2RmYmZhNjhhIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE2OTY0NDQ5MTgsImV4cCI6NDg1MjIwNDkxOH0.kW9jP_Y_2JA70nCkUaBQMW329kQK6vuyHIfFNym0SNs"




#Function to send the request to the target IP
def sendRequest(sendRequestMessage, blockToAdd, targetIP="146.229.163.145", authorizingUser=None):
    try:
        #Creates a socket
        clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientSocket.settimeout(5)
        #Connects to the other device
        clientSocket.connect((targetIP, lightweightport))
        #Code to get the encryption key
        clientSocket.send((sendRequestMessage).encode("utf-8")[:4096])
        time.sleep(0.5)
        #Sends the message with the public key to encrypt the key
        clientSocket.send((blockToAdd.save_pkcs1().decode("utf-8")).encode("utf-8")[:4096])
        #Waits for reception of the file key and decrypts it with the privateKey
        return rsa.decrypt(clientSocket.recv(4096), authorizingUser)
        #
        
    #Except if something has gone wrong, return false as the operation failed
    except socket.timeout:
        return "DeviceNotOnline"#Except if something has gone wrong, return false as the operation failed
    except Exception as e:
        return str(e.__cause__)#"Something went wrong"
    


#Function to get the file symmetric key
def getFileKey():
    result = rsa.newkeys(1024)

    return sendRequest("Get_Key", result[0], "146.229.163.145", result[1])

finalData = getFileKey()
print(finalData)
newFernet = Fernet(finalData)
#print(finalData == 'yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os='.encode('utf-8'))
#print(finalData == b'yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os=')
#print(finalData == 'yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os=')
localFernet = Fernet(b'yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os=')
localFernet = Fernet('yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os='.encode('utf-8'))
localFernet = Fernet('yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os=')

        #file1Key = 'yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os='.encode('utf-8')



file1Key = 'yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os='.encode('utf-8')#b'yrnX6PYjWcITai_1Ux6IC1rXlCP7y1TiPC8dcxTi7os='
fernet = Fernet(file1Key)
#Open the encrypted file and read the data
with open("newImage.png", "rb") as enc_file:
    encrypted = enc_file.read()

#Decrypts the file data
decrypted = newFernet.decrypt(encrypted)

#Overwrites the encrypted data with the unencrypted data
with open("newImage.png", "wb") as dec_file:
    dec_file.write(decrypted)

import requests



#print(finalData.encode('utf-8'))
#print(finalData.decode('utf-8'))

