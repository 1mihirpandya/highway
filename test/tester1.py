import sys
sys.path.append('/Users/mihirpandya/Desktop/Mihir/Projects/DS')
import socket
from scapy.all import *
from JSONTemplate import *
import json
from tester import *
import threading

class X():
    def __init__(self):
        self.files = []
        self.y = Y()

    def beat(self):
        udp_th = threading.Thread(target=self.y.heartbeat, kwargs={"files":self.files}, daemon=True)
        udp_th.start()
        while True:
            print(self.files)
            time.sleep(3)


"""
HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 8080        # The port used by the server

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
query = JSONQueryUDPTemplate.template
query["query"] = "get_filelist"
p = Ether()/IP(dst=HOST)/UDP(sport=50001, dport=port)/Raw(load=json.dumps(query))
print(len(bytes(p)))
sock.sendto(bytes(p), (HOST, PORT))
#sock.sendall(b'Hello, world')
#data = s.recv(1024)

#print('Received', repr(data))
"""
