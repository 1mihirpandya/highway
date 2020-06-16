#!/usr/bin/env python
from scapy.all import *
from NetworkClientCache import *
from JSONTemplate import *
import socket
import threading
import random
import json

class NetworkClient:

    def __init__(self, client_node, network_cache, ip):
        self.network_cache = network_cache
        self.client_node = client_node
        self.ip = ip

    def listen_to_ports(self):
        #udp_port
        udp_th = threading.Thread(target=self.listen_to_udp_port, daemon=True)
        udp_th.start()
        #tcp port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.ip, 0)) #CHANGE THIS
        self.network_cache.tcp_port = sock.getsockname()[1]
        #print("tcp", self.network_cache.tcp_port)
        sock.listen()
        try:
            while True:
                conn, addr = sock.accept()
                with conn:
                    print('TCP connected by', addr)
                    payload = self.recv_msg_tcp(conn)
                    #print(payload)
                    dict_payload = json.loads(payload)
                    #print(dict_payload)
                    response = getattr(self.client_node, dict_payload["query"])(dict_payload["payload"])
                    response = json.dumps(response).encode()
                    self.send_msg_tcp(conn, response)
                print("TCP connection closed")
        except KeyboardInterrupt:
            sock.close()
            sys.exit(1)

    def listen_to_udp_port(self):
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        sock.bind((self.ip, 0)) #CHANGE THIS
        self.network_cache.udp_port = sock.getsockname()[1]
        #print("udp", self.network_cache.udp_port)
        try:
            while True:
                # TODO: Multi-sized packets
                payload, address = sock.recvfrom(1024)
                dict_payload = json.loads(payload)
                if dict_payload["type"] == Constants.Network.HEARTBEAT:
                    content = dict_payload["payload"]
                    getattr(self.client_node, dict_payload["query"])(dict_payload["payload"])
                    resp = JSONHeartbeatAckTemplate.template
                    resp["src"] = self.get_src_addr()
                    json_resp = json.dumps(resp)
                    sock.sendto(json_resp.encode(), address)
                #deal with type == heartbeat_ack
        except KeyboardInterrupt:
            sock.close()
            sys.exit(1)

    def heartbeat(self, name, payload, neighbors, frequency=5):
        try:
            while True:
                for neighbor in neighbors:
                    msg = JSONHeartbeatUDPTemplate.template
                    msg["src"] = self.get_src_addr()
                    msg["query"] = name
                    msg["payload"] = list(payload)
                    self.send_udp(json.dumps(msg), (neighbor[0],neighbor[-1]))
                time.sleep(frequency)
        except KeyboardInterrupt:
            sys.exit(1)

    def send_udp(self, query, dst):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(query.encode(), dst)

    def send_rpc(self, query):
        query["id"] = random.randint(0,10000)
        while query["id"] in self.network_cache.query_ids:
            query["id"] = random.randint(0,10000)
        self.network_cache.query_ids[query["id"]] = CacheConstants.EMPTY
        json_query = json.dumps(query)
        #print(json_query)
        payload = self.send_recv_tcp_using_socket(json_query, (query["dst"], query["dstport"]))
        self.network_cache.query_ids[query["id"]] = None
        #print(payload)
        return json.loads(payload)

    def send_recv_tcp_using_socket(self, query, dst):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(dst)
        print()
        print()
        s.connect((dst[0], dst[1]))#self.tcp_port))
        self.send_msg_tcp(s, query.encode())
        payload = self.recv_msg_tcp(s)
        s.close()
        return payload

    def send_msg_tcp(self, sock, msg):
        # Prefix each message with a 4-byte length (network byte order)
        msg = struct.pack('>I', len(msg)) + msg
        sock.sendall(msg)

    def recv_msg_tcp(self, sock):
        # Read message length and unpack it into an integer
        raw_msglen = self.recvall_tcp(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        # Read the message data
        return self.recvall_tcp(sock, msglen)

    def recvall_tcp(self, sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def get_src_addr(self):
        return (self.ip, self.network_cache.tcp_port, self.network_cache.udp_port)
