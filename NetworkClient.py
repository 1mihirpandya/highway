#!/usr/bin/env python
from NetworkClientCache import *
from JSONTemplate import *
from Transport import ClientDelegate
import socket
import struct
import threading
import random
import json
import sys

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
                    dict_payload = json.loads(payload)
                    self.network_cache.update_cache(dict_payload["src"], last_received=TimeManager.get_formatted_time())
                    response = ClientDelegate.receive(dict_payload, self.client_node)
                    self.send_msg_tcp(conn, response)
                    self.network_cache.update_cache(dict_payload["src"], last_sent=TimeManager.get_formatted_time(), last_received=TimeManager.get_formatted_time())
                print("TCP connection closed")
        except KeyboardInterrupt:
            sock.close()
            sys.exit(1)

    def listen_to_udp_port(self):
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        sock.bind((self.ip, 0))
        self.network_cache.udp_port = sock.getsockname()[1]
        #print("udp", self.network_cache.udp_port)
        try:
            while True:
                # TODO: Multi-sized packets
                payload, address = sock.recvfrom(1024)
                dict_payload = json.loads(payload)
                dict_payload["src"] = tuple(dict_payload["src"])
                self.network_cache.update_cache(dict_payload["src"], last_received=TimeManager.get_formatted_time())
                if dict_payload["type"] == Constants.Network.HEARTBEAT:
                    content = dict_payload["payload"]
                    getattr(self.client_node, dict_payload["query"])(dict_payload["src"], dict_payload["payload"])
                    resp = JSONHeartbeatAckTemplate.template
                    resp["src"] = self.get_src_addr()
                    json_resp = json.dumps(resp)
                    self.send_udp(json_resp, self.get_udp_addr(dict_payload["src"]))
                if dict_payload["type"] == Constants.Network.ACK:
                    self.network_cache.update_cache(dict_payload["src"], last_ack=TimeManager.get_formatted_time())
                if dict_payload["type"] == Constants.Network.QUERY:
                    proc_th = threading.Thread(target=self.respond_to_udp_query, kwargs={"query":dict_payload}, daemon=True)
                    proc_th.start()
                if dict_payload["type"] == Constants.Network.RESPONSE:
                    proc_th = threading.Thread(target=self.process_udp_response, kwargs={"query":dict_payload}, daemon=True)
                    proc_th.start()
        except KeyboardInterrupt:
            sock.close()
            sys.exit(1)

    def process_udp_response(self, query):
        query_ids = self.network_cache.query_ids
        neighbors = self.network_cache.neighbors
        if query_ids[query["id"]].query == "get_neighbor_status":
            if TimeManager.get_time_diff_in_seconds(neighbors[query["payload"]["neighbor"]].last_sent, query["payload"]["last_ack"]) < Constants.Heartbeat.TIMEOUT:
                ref[neighbor].status = CacheConstants.OKAY
        query_ids[query["id"]] = None


    def respond_to_udp_query(self, query):
        response = JSONResponseUDPTemplate.template
        response["id"] = query["id"]
        response["src"] = query["dst"]
        response["dst"] = query["src"]
        response["payload"] = getattr(self.client_node, query["query"])(query["src"], query["payload"])
        dst = self.get_udp_addr(response["dst"])
        response = json.dumps(response)
        #print(response["dst"])
        self.send_udp(response, dst)
        #self.network_cache.update_cache(response["dst"], last_sent=TimeManager.get_formatted_time(), last_received=TimeManager.get_formatted_time())

    def heartbeat(self, name, payload, neighbors, frequency=5):
        try:
            while True:
                for neighbor in neighbors:
                    msg = JSONHeartbeatUDPTemplate.template
                    msg["src"] = self.get_src_addr()
                    msg["query"] = name
                    msg["payload"] = list(payload)
                    self.send_udp(json.dumps(msg), (neighbor[0],neighbor[-1]))
                    #print(84, dict_payload["src"])
                    self.network_cache.update_cache(neighbor, last_sent=TimeManager.get_formatted_time())
                time.sleep(frequency)
        except KeyboardInterrupt:
            sys.exit(1)

    def send_udp_query(self, q, payload, destinations):
        query = JSONQueryUDPTemplate.template
        query["id"] = self.network_cache.get_query_id(query)
        query["src"] = self.get_src_addr()
        query["query"] = q
        query["payload"] = payload
        for dst in destinations:
            query["dst"] = dst
            #print(query)
            #print()
            self.send_udp(json.dumps(query), self.get_udp_addr(dst))

    def send_udp(self, query, dst):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(query.encode(), dst)

    def send_rpc(self, query, dst):
        #query["id"] = self.network_cache.get_query_id()
        #json_query = json.dumps(query)
        #network_cache.update_cache(neighbor, last_sent=TimeManager.get_formatted_time())
        payload = self.send_recv_tcp_using_socket(query, dst)
        #self.network_cache.query_ids[query["id"]] = None
        return json.loads(payload)

    def send_recv_tcp_using_socket(self, query, dst):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.get_tcp_addr(dst))
        self.send_msg_tcp(sock, query)
        payload = self.recv_msg_tcp(sock)
        sock.close()
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

    def get_udp_addr(self, dst):
        return (dst[0], dst[2])

    def get_tcp_addr(self, dst):
        return (dst[0], dst[1])
