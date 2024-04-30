#change eth interface name if necessary in myIP()
from methods import comm
from methods import GUI_modulated as GUI

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

# BLOCK.PY IMPORTS
import re
from moralis import evm_api
import base64

import errno

# COMM.PY GLOBALS
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #new socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
samaritan = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
self_samaritan = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

lightweight1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
lightweight2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
lwserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 

neighbor_nodes = []
initial_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connectport = 11453
givenport = 12453
LWport = 13453

# BLOCK.PY CLASSES
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

class Block: # Block represents each 'item' in the blockchain
    def __init__(self, index, timestamp, prevHash, validatorName, transactionType, payload):
        self.index = index                          # block's position in the blockchain
        self.timestamp = timestamp                  # when block was created (<year>-<mh>-<dy> <hr>:<mi>:<se>.<millis>)
        self.prevHash = prevHash                    # 64-character hash of previous block (blank for genesis)
        self.validatorName = validatorName          # address of the validator (blank for genesis)
        self.hash = self.calculateBlockHash()     # hash for the block
        self.transactionType = transactionType      # either "Upload", "Download", "Create_Account", or "Genesis"
        self.payload = payload                      # ** EITHER FILEDATA OR ACCOUNT OBJECT
        
        # update this depending on how sign-in/authorization works:
        self.approved_IDs = []

    def calculateHash(self, s):# calculateHash is a simple SHA256 hashing function
        h = hashlib.sha256()
        h.update(s.encode('utf-8'))
        return h.hexdigest()
    
    def calculateBlockHash(self): # calculateBlockHash returns the hash of all block information
        record = str(self.index) + self.timestamp + self.prevHash
        return self.calculateHash(record)


# BLOCK.PY GLOBALS
blockchain = [] # Blockchain is a series of validated Blocks
tempBlocks = []
ipfsHashes = [] # keep up with all uploaded IPFS hashes and file names
fileNames = []
accountNames = []
nodes = [] #client tcp address array
candidateBlocks = [] # candidateBlocks handles incoming blocks for validation
candidateBlocksLock = threading.Lock()
validatorLock = threading.Lock()
validators = [] # validators keeps track of open validators and balances
validator = Validator(0, Account("", "", "?", "")) # keep track of current validator
stopThreads = False # use flag to stop threading
# key for ipfs upload
apiKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImE0NmE4MmFjLWJlYjEtNGM4MC05MjIwLTIxZDFlNGQ3MGM1NyIsIm9yZ0lkIjoiMzU5ODUyIiwidXNlcklkIjoiMzY5ODMwIiwidHlwZUlkIjoiNTY2M2MwZjAtMmM3Mi00N2YxLWJkMDktNTM1M2RmYmZhNjhhIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE2OTY0NDQ5MTgsImV4cCI6NDg1MjIwNDkxOH0.kW9jP_Y_2JA70nCkUaBQMW329kQK6vuyHIfFNym0SNs"

blockchainMessage = "default_blockchain_message"

def myIP():
    return (ni.ifaddresses('enp0s31f6')[ni.AF_INET][0]['addr'])
def addToCandidateBlocks(transactionType, payload, validator):
    with validatorLock:
        oldLastIndex = blockchain[-1]
    newBlock = generateBlock(oldLastIndex, validator.address, transactionType, payload)

    if isBlockValid(newBlock, oldLastIndex):
        candidateBlocks.append(newBlock)
    
    return newBlock

def assembleBlockchain():
    message = ""
    for block in blockchain:
        if block.transactionType == "Genesis":
            genesis = expandGenesisBlock()
            message = message + genesis
        else:
            standardBlock = expandStandardblock(block)
            message = message + standardBlock
            if (block.transactionType == "Upload") or (block.transactionType == "Download"):
                hash = "IPFS_Hash: " + block.payload.ipfsHash
                filename = "File_Name: " + block.payload.fileName
                type = "Type: " + block.transactionType
                upload = "\n" + hash + "\n" + filename + "\n" + type
                message = message + upload
            else:
                credentialBlock = expandCredentials(block)
                message = message + credentialBlock
    return message    

def assembleBlock(block):
    message = ""
    if block.transactionType == "Genesis":
        genesis = expandGenesisBlock()
        message = message + genesis
    else:
        standardBlock = expandStandardblock(block)
        message = message + standardBlock
        if (block.transactionType == "Upload") or (block.transactionType == "Download"):
            hash = "IPFS_Hash: " + block.payload.ipfsHash
            filename = "File_Name: " + block.payload.fileName
            accessList = "Access_List: " + block.payload.accessList
            type = "Type: " + block.transactionType
            upload = "\n" + hash + "\n" + filename + "\n" + accessList + "\n" + type
            message = message + upload
        else:
            credentialBlock = expandCredentials(block)
            message = message + credentialBlock
    return message    

def calculateHash(s):
    h = hashlib.sha256()
    h.update(s.encode('utf-8'))
    return h.hexdigest()

def convertString(currentBlockchain):
    blockDictionary = {}
    delimiters = ["\n"]
    for delimiter in delimiters:
        currentBlockchain = " ".join(currentBlockchain.split(delimiter))
    result = currentBlockchain.split()
    i = 0
    blockDictionary["Previous_Hash"] = "Default"
    blockDictionary["Validator"] = "Default"
    blockDictionary["Hash"] = "hash"
    accessList = "" #deleted but may need to declare as empty string
    for item in result:
        if item == "Index:":
            blockDictionary["Index"] = result[i + 1]
        elif item == "Timestamp:":
            blockDictionary["Timestamp"] = result[i + 1]+ " " + result[i+2]
        elif item == "Previous_Hash:":
            blockDictionary["Previous_Hash"] = result[i + 1]
        elif item == "Hash:":
            blockDictionary["Hash"] = result[i + 1]
        elif item == "Validator:":
            blockDictionary["Validator"] = result[i + 1]
        elif item == "IPFS_Hash:":
            blockDictionary["IPFS_Hash"] = result[i + 1]
        elif item == "File_Name:":
            blockDictionary["File_Name"] = result[i + 1]
        elif item == "Access_List:":
            blockDictionary["Access_List"] = result[i + 1]
        elif item == "Username:":
            blockDictionary["Username"] = result[i + 1]
        elif item == "Password:":
            blockDictionary["Password"] = result[i + 1]
        elif item == "Role:":
            blockDictionary["Role"] = result[i + 1]
        elif item == "Type:":
            blockDictionary["Type"] = result[i + 1]
            #added update user
            if (blockDictionary['Type'] == 'Create_Account') or (blockDictionary['Type']== 'Update_User'):
                print("I made it to account")
                username = blockDictionary['Username']
                password = blockDictionary['Password']
                role = blockDictionary['Role']
                fullLegalName = "admin"
                payload = Account(username, password, role, fullLegalName)
            elif (blockDictionary['Type'] == 'Upload') or (blockDictionary['Type'] == 'Download'):
                print("I made it to upload/download")
                ipfsHash = blockDictionary['IPFS_Hash']
                fileName = blockDictionary['File_Name']
                validator = blockDictionary['Validator']
                accessList = blockDictionary['Access_List']
                payload = FileData(ipfsHash, fileName, validator, accessList)
            else:
                print(f"block type is: {blockDictionary['Type']}")
                payload = FileData("", "", "", accessList)
            index = int(blockDictionary['Index'])
            timestamp = blockDictionary['Timestamp']
            prevHash = blockDictionary['Previous_Hash']
            hash = blockDictionary['Hash']
            validatorName = blockDictionary['Validator']
            transactionType = blockDictionary['Type']
            newBlock = GivenBlock(index, timestamp, prevHash, hash, validatorName, transactionType, payload)
            blockchain.append(newBlock)

        i += 1
    GUI.setGUIBlockchain(blockchain)
    return result

def createAccount(username, password, name, roleSelection): # , root
    # print("role is " + roleSelection)
    if roleSelection == "Admin":
        role = "a"
    elif roleSelection == "Doctor":
        role = "d"
    else:
        role = "p"
    newAccount = Account(username, password, role, name)

    return newAccount

def createFirstBlocks():
    genesisBlock = generateGenesisBlock()
    blockchain.append(genesisBlock)
    address = ""

def createValidator(currentAccount):
    #Randomly stakes coins to prevent a favored node
    balance = randint(1,100)

    newValidator = Validator(balance, currentAccount)

    with validatorLock:
        validators.append(newValidator)
        for validator in validators: 
            pass           

    return newValidator

def generateBlock(oldBlock, address, transactionType, payload): # generate_block creates a new block using the previous block's hash
    t = str(datetime.now())
    new_block = Block(oldBlock.index + 1, t, oldBlock.hash, address, transactionType, payload)
    return new_block

def generateGenesisBlock(): # generate_genesis_block creates the genesis block
    t = str(datetime.now())
    genesisBlock = Block(0, t, "", "admin", "Create_Account", Account("admin", "admin", "a", "Admin"))
    return genesisBlock

def generateSampleBlocks():
    t = str(datetime.now())

    address = "admin"
    accessList = ""
    blockchain.append(generateBlock(blockchain[-1], address, "Create_Account", Account("doctor", "batman", "d", "Dr. Doctor")))

def getLotteryWinner():
    weightedValidators = validators.copy()
    balanceTotal = 0
    prevBalance = 0
    chosenValidator = ""

    for validator in weightedValidators:
        balanceTotal = balanceTotal + validator.balance
    print("balance total is " + str(balanceTotal))
    randomValue = randint(0,balanceTotal)
    print("random value is " + str(randomValue))
    for validator in weightedValidators:
        print("prev balance is " + str(prevBalance))
        if randomValue < validator.balance:
            chosenValidator = validator
            break
        else:
            randomValue = randomValue - prevBalance
            prevBalance = validator.balance

    print("chosen validator is " + chosenValidator.address)
    return chosenValidator

def isBlockValid(newBlock, oldBlock):
    if (oldBlock.index + 1) != newBlock.index:
        return False
    elif oldBlock.hash != newBlock.previous_hash:
        return False
    elif calculateHash(newBlock) != newBlock.hash:
        return False
    return True

def newBlockchain():
    blockchain = []
    blockchain.append(generateGenesisBlock())

    return blockchain

def pickWinner(server_to_client, server_to_self_samaritan, parent_to_child): # , root
    chosenValidator = getLotteryWinner()

    if chosenValidator != "":
        msg = "You won the lottery! Please process the transaction."
        server_to_self_samaritan.put(msg)

        #message is wrong now
        for transaction in candidateBlocks:
            if (transaction.transactionType == "Upload") or (transaction.transactionType == "Download"):
                validator = transaction.payload.validator
                if validator == chosenValidator:
                    msg = f"Block {transaction} contains a transaction relevant to you. Please process it."
                    server_to_self_samaritan.put(msg)
                    return
            elif transaction.validator == chosenValidator:
                msg = f"Block {transaction} was chosen by the lottery. Please process it."
                server_to_self_samaritan.put(msg)
                return
    else:
        msg = "No validators eligible to win. Please wait for more validators."
        server_to_self_samaritan.put(msg)

def printBlockchain():
    chainAsString = ""
    for block in blockchain:
        chainAsString += block.__str__()
    print(chainAsString)

def runInput(server_input_to_server, validator): # , root
    while True:
        serverInput = server_input_to_server.get()

        if serverInput == "validate":
            pickWinner(server_to_client, server_to_self_samaritan, parent_to_child)
        elif serverInput == "print":
            printBlockchain()
        elif serverInput == "exit":
            os.kill(os.getpid(), signal.SIGINT)

def run_LW(lw_to_full, validator):
    while True:
        lwInput = lw_to_full.get()

        if lwInput == "update":
            updateValidators()
        elif lwInput == "exit":
            os.kill(os.getpid(), signal.SIGINT)

def run_client(child_to_parent, parent_to_child, new_client_for_samaritan, self_samaritan_to_client, client_to_self_samaritan, client_to_server, server_to_client, server_to_self_samaritan, self_samaritan_to_server, server_input_to_server): # , root
    #Used to send messages to server and recieve messages from server
    msg = client_to_server.get()
    server_input_to_server.put(msg)
    #Receive message from server
    msg = server_to_client.get()
    child_to_parent.put(msg)

    #For the Samaritan
    while True:
        msg = client_to_self_samaritan.get()
        self_samaritan_to_server.put(msg)
        msg = server_to_self_samaritan.get()
        self_samaritan_to_client.put(msg)

def run_server(lw_to_full, child_to_parent, parent_to_child, validator, new_client_for_samaritan, self_samaritan_to_client, client_to_self_samaritan, client_to_server, server_to_client, server_to_self_samaritan, self_samaritan_to_server, server_input_to_server): # , root
    while True:
        msg = parent_to_child.get()
        if msg == "lw":
            lw_to_full.put("update")
        else:
            client_to_server.put(msg)
            msg = self_samaritan_to_server.get()
            server_input_to_server.put(msg)
        msg = self_samaritan_to_client.get()
        parent_to_child.put(msg)

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    exit()

def updateValidators():
    winners = []
    for i in range(0, 5):
        winners.append(getLotteryWinner())
    for validator in validators:
        validator.balance = validator.balance - 1
    for winner in winners:
        winner.balance = winner.balance + 1


if __name__ == "__main__":
    main()
