import socket
from scapy.all import *
HOST = "127.0.0.1"
PORT = 8080#65432
import time



class Y():
    def __init__(self):
        pass
    def heartbeat(self, files):
        while True:
            files.append(1)
            time.sleep(3)



class TestMaster:
    def __init__(self):
        self.files = []
        self.slave = TestSlave(self)

class TestSlave:
    def __init__(self, master):
        self.file = "hello"
        self.master = master
    def give_back(self):
        self.master.files.append(self.file)

"""
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))
try:
    while True:
        data = sock.recvfrom(1024)
        payload = Ether(data)[Raw].load.decode()
        print(data)
        print(payload)
except KeyboardInterrupt:
    sock.close()
    sys.exit(1)
"""
#master = TestMaster()
#print(master.files)
#master.slave.give_back()
#print(master.files)
