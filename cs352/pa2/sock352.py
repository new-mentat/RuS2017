import binascii
import socket as syssock
import struct
import sys
import time
import random

# encryption libraries 
import nacl.utils
import nacl.secret
import nacl.utils
from nacl.public import PrivateKey, Box

# if you want to debug and print the current stack frame 
from inspect import currentframe, getframeinfo

# these are globals to the sock352 class and
# define the UDP ports all messages are sent
# and received from

# the ports to use for the sock352 messages 
global sock352portTx
global sock352portRx
# the public and private keychains in hex format 
global publicKeysHex
global privateKeysHex

# the public and private keychains in binary format 
global publicKeys
global privateKeys

# the encryption flag 
global ENCRYPT

publicKeysHex = {} 
privateKeysHex = {} 
publicKeys = {} 
privateKeys = {}

# this is 0xEC 
ENCRYPT = 236 

# this is the structure of the sock352 packet 
sock352HdrStructStr = '!BBBBHHLLQQLL'

def readKeyChain(filename):
    global publicKeysHex
    global privateKeysHex 
    global publicKeys
    global privateKeys 
    
    if (filename):
        try:
            keyfile_fd = open(filename,"r")
            for line in keyfile_fd:
                words = line.split()
                # check if a comment
                # more than 2 words, and the first word does not have a
                # hash, we may have a valid host/key pair in the keychain
                if ( (len(words) >= 4) and (words[0].find("#") == -1)):
                    host = words[1]
                    port = words[2]
                    keyInHex = words[3]
                    if (words[0] == "private"):
                        privateKeysHex[(host,port)] = keyInHex
                        privateKeys[(host,port)] = nacl.public.PrivateKey(keyInHex, nacl.encoding.HexEncoder)
                    elif (words[0] == "public"):
                        publicKeysHex[(host,port)] = keyInHex
                        publicKeys[(host,port)] = nacl.public.PublicKey(keyInHex, nacl.encoding.HexEncoder)
        except Exception,e:
            print ( "error: opening keychain file: %s %s" % (filename,repr(e)))
    else:
            print ("error: No filename presented")             


    print("Read in Key file")
    return (publicKeys,privateKeys)


def init(UDPportTx,UDPportRx):    
    global rx_port
    global rx_socket
    global tx_port

    rx_port = int(UDPportRx)
    rx_socket = syssock.socket(syssock.AF_INET, syssock.SOCK_DGRAM)
    rx_socket.bind(('', rx_port))
    tx_port = int(UDPportTx)

    
class socket:
    
    def __init__(self):
        self.seq_num = -1 # sequence number for packet which has been received last
        self.ack_num = -1
        self.connected = False # if handshake completed, set to true
        self.current_buffer = None
        self.client_closed = False
        self.packet_format = struct.Struct('!BBBBHHLLQQLL')
        self.address = None 
        self.client = False
        self.server = False
        self.encrypt = None
        self.box = None
        self.nonce = None

    def bind(self,address):
      # null function for part 1 
        return 

    # connection sets performs the initial handshake and establishes a connection on the client side. This function is also responsible for transmitting all addtional packets including the final packet

    def connect(self,*args):  # fill in your code here
        # Check publicKeys and privateKeys to check for matching host and
        # port
        # Create nonce
        # Find Keys
        # Create Box Object:

        global ENCRYPT
        global rx_port
        global tx_port
        
        address = args[0]
        self.address = address[0] 
        self.client = True


        init_sequence_no = random.randint(1,100) # randomly select first seq num
   #                                            opt,prot,h-len,c-sum,s-port,d-port,     ack,rec-window, payload len                           

        if (len(args) < 2):
          
          while True:

            try:

              init_packet = self.packet_format.pack(1, 1, 0, 0, 40, 0, 0, 0, init_sequence_no, 0, 0, 0)
              rx_socket.settimeout(.2)
              rx_socket.sendto(init_packet, (self.address, tx_port)) 

              print("Sending init packet with sequence number + " + str(init_sequence_no))

              ack = rx_socket.recv(4096) # Received ack from server
              ack = self.packet_format.unpack(ack)

              print("Received ack packet " + str(ack))

              client_ack = self.packet_format.pack(1, 0, 0, 0, 40, 0, 0, 0, ack[9], int(ack[8]) + 1, 0, 0) # Send final client ack
              rx_socket.sendto(client_ack, (self.address, tx_port))

              print("Sending final client ack " + str((1, 0, 0, 0, 40, 0, 0, 0, ack[9], int(ack[8]) + 1, 0, 0)))

              self.seq_num = ack[9]
              self.ack_num = ack[8]
              rx_socket.settimeout(None)

              print("connected")
              break

            except syssock.timeout:
              continue



        elif (len(args) >=2):  
          if (args[1] == ENCRYPT):
            print("USING ENCRYPTION")
            self.encrypt = True

        
          try: 
            encrypt_key = privateKeys[('localhost', rx_port)] # retrieve clients private key used to encrypt messages 
          except:
            encrypt_key = privateKeys[('*', '*')]

          try:
            decrypt_key = publicKeys[address]
          except:
            decrypt_key = publicKeys[('*', '*')]

          self.box = Box(encrypt_key, decrypt_key)


          while True:
            try:

              init_packet = self.packet_format.pack(1, 1, 1, 0, 40, 0, 0, 0, init_sequence_no, 0, 0, 0)
              rx_socket.settimeout(.2)
              rx_socket.sendto(init_packet, (self.address, tx_port)) 

              print("Sending init packet with sequence number + " + str(init_sequence_no))

              ack = rx_socket.recv(4096) # Received ack from server
              header = self.packet_format.unpack(ack[:40]) 
              nonce = ack[40: len(ack)]
              self.nonce = nonce
              print("Received ack packet " + str(ack))

              client_ack = self.packet_format.pack(1, 0, 0, 0, 40, 0, 0, 0, int(header[9]), int(header[8]) + 1, 0, 0) # Send final client ack
              rx_socket.sendto(client_ack, (self.address, tx_port))


              self.seq_num = header[9]
              self.ack_num = header[8]
              rx_socket.settimeout(None)

              print("connected")
              break

            except syssock.timeout:
              continue



    
    def listen(self,backlog):
        return

    #accept accepts the conection and continues to retrieve packets for as long as the connection is open
    def accept(self, *args):
        if(len(args) > 0):
          if args[0] == ENCRYPT:
            self.encrypt = True
        
        self.server = True
        while True:
          self.__sock352_get_packet()
          if self.connected == True:
            return (self, tx_port)
          
    #close closes the connection and handles terminates the connection after recieving the last ack from sending the packet with the FIN bit set.       
    def close(self): 

        if self.client_closed == False and self.server == True:
          while self.client_closed == False:
            self.__sock352_get_packet()
          self.close()

        if self.client:
          while True:
            try:
              rx_socket.settimeout(.2)
              final_packet = self.packet_format.pack(1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
              rx_socket.sendto(final_packet, (self.address, tx_port))
              final_ack = rx_socket.recv(1096)
              final_ack = self.packet_format.unpack(final_ack)
              
              if final_ack[1] == 2:
                print("Terminating connection")
                rx_socket.close()
                return

            except syssock.timeout:
              continue


    #send creates and sends packets as well as checks the acks revcieved 
    def send(self, buffer):
        bytessent = 0     # fill in your code here

        ret_length = len(buffer)

        if(self.encrypt):
          print("Encrypting packet " + str(self.seq_num))
          buffer = self.box.encrypt(buffer, self.nonce)
        
        payload_len = len(buffer) 
        packet = self.packet_format.pack(1, 0, 0, 0, 40, 0, 0, 0, self.seq_num, self.ack_num, 0, payload_len)
        packet = packet + buffer 
        
        while True:
          try:
            print("Sending packet number " + str(self.seq_num))
            rx_socket.sendto(packet, (self.address, tx_port))
            rx_socket.settimeout(.2)
            ack = rx_socket.recv(1096)
            ack = self.packet_format.unpack(ack)

            if ack[9] == self.seq_num:
              self.seq_num = self.seq_num + 1
              self.ack_num = ack[8] + 1
              rx_socket.settimeout(None)
              break

          except syssock.timeout:
            continue

        return ret_length

    #recv recieves the data and makes sure it is delivered in the correct fragment size by utilizing a buffer 
    def recv(self,bytes_to_receive): 
        if self.current_buffer: 
          if bytes_to_receive > len(self.current_buffer):
            data = self.current_buffer
            self.current_buffer = None
          else:           
            data = self.current_buffer[0:bytes_to_receive]
            self.current_buffer = self.current_buffer[bytes_to_receive:]
            
          return data 

        else:
          
          while not self.current_buffer and self.client_closed == False:
            try:
              rx_socket.settimeout(.2)
              self.__sock352_get_packet() # Get another packet
            except syssock.timeout:
              continue

            rx_socket.settimeout(None)
          
          data = self.current_buffer[0:bytes_to_receive]
          self.current_buffer = self.current_buffer[bytes_to_receive:len(self.current_buffer)]

          return data
    
    #__sock352_get_packet creates and sends acks to the client when packets are recieved. It makes sure to check that the seq_num is in the correct order as well as check the flags of the packet sent            
                
    def  __sock352_get_packet(self):
        global tx_port 
        packet, address = rx_socket.recvfrom(64000)
        header = self.packet_format.unpack(packet[:40])
        data = packet[40: len(packet)]
        self.address = address[0]
        payload_len = len(data) 
        flags = header[1]

        if flags == 1: # initial handshake 
          print("Received connection initiation " + str(packet))
          self.nonce = nacl.utils.random(Box.NONCE_SIZE)
          server_seq_num = random.randint(1,100)
          ack = self.packet_format.pack(1, 0, 0, 0, 40, 0, 0, 0, server_seq_num, header[8] + 1, 0, len(self.nonce)) # send back Ack with bits set to indicate handshake is completed
          ack = ack + self.nonce

          try: 
            encrypt_key = privateKeys[('localhost', rx_port)] # retrieve clients private key used to encrypt messages 
          except:
            encrypt_key = privateKeys[('*', '*')]

          try:
            decrypt_key = publicKeys[('localhost', str(address[1]))]
          except:
            decrypt_key = publicKeys[('*', '*')]


          self.box = Box(encrypt_key, decrypt_key)

          while True:
            try:
              rx_socket.settimeout(.2)
              rx_socket.sendto(ack, address)
              print("sending server ack" + str(self.packet_format.unpack(ack[:40])))
              client_ack = rx_socket.recv(4096)               
              client_ack = self.packet_format.unpack(client_ack)
              print("received client ack" + str(client_ack))
              self.connected = True
              self.seq_num = int(client_ack[8])
              self.ack_num = int(client_ack[9])
              print("connected and waiting for " + str(self.seq_num))
              rx_socket.settimeout(None)
              return

            except syssock.timeout:
              continue

          print "connection established"

        if flags == 2: # initiate connection close 
          while True:
            try:
              rx_socket.settimeout(.2)
              final_ack = self.packet_format.pack(1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0) # send packet with FIN bit set 
              rx_socket.sendto(final_ack, address)
              self.client_closed = True
              break

            except syssock.error:
              self.client_closed = True

            except syssock.timeout:
              continue


        else:
          seq_num = header[8]
          ack_num = header[9]
          
          if(self.encrypt):
            print("Decrypting Packet " + str(self.seq_num))
            data = self.box.decrypt(data)


          if (seq_num != self.seq_num) or payload_len != header[11]: # if ack is dropped or packet is malformed
            self.seq_num = seq_num + 1
            reset_packet = self.packet_format.pack(1, 8, 0, 0, 40, 0, 0, 0, ack_num, seq_num, 0, 0)
            rx_socket.sendto(reset_packet, address)            # send reset (RST) packet with sequence nubmer

          else:
            print("Sending ack for packet " + str(self.seq_num))
            self.current_buffer = data
            self.seq_num = seq_num + 1
            ack = self.packet_format.pack(1, 0, 0, 0, 40, 0, 0, 0, ack_num + 1, seq_num, 0, 0)
            rx_socket.sendto(ack , address)
