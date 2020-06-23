#!/usr/bin/env python
from NetworkClientCache import *
from JSONTemplate import *
from ClientDelegate import *
import socket
import struct
import threading
import random
import json
import sys

class NetworkClient:

    def __init__(self, client_delegate, network_cache, file_delegate, ip):
        self.client_delegate = client_delegate
        self.file_delegate = file_delegate
        self.network_cache = network_cache
        self.ip = ip

    def cache_response(self, filename, addr):
        self.file_delegate.cache(filename, addr)

    def listen_to_tcp_port(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.ip, 0))
        self.network_cache.tcp_port = sock.getsockname()[1]
        sock.listen()
        try:
            while True:
                conn, addr = sock.accept()
                with conn:
                    payload = self.recv_msg_tcp(conn)
                    dict_payload = json.loads(payload)
                    self.network_cache.update_cache(dict_payload["src"], last_received=TimeManager.get_formatted_time())
                    if dict_payload["protocol"] == Constants.Network.STREAM:
                        self.file_delegate.receive(dict_payload, conn)
                    else:
                        response = self.client_delegate.receive(dict_payload)
                        self.send_msg_tcp(conn, response)
                    self.network_cache.update_cache(dict_payload["src"], last_sent=TimeManager.get_formatted_time())
        except KeyboardInterrupt:
            sock.close()
            sys.exit(1)

    def listen_to_udp_port(self):
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        sock.bind((self.ip, 0))
        self.network_cache.udp_port = sock.getsockname()[1]
        try:
            while True:
                # TODO: Multi-sized packets
                payload, address = sock.recvfrom(1024)
                dict_payload = json.loads(payload)
                src = tuple(dict_payload["src"])
                #self.network_cache.update_cache(src, last_received=TimeManager.get_formatted_time())
                if dict_payload["type"] == Constants.Network.ACK:
                    self.network_cache.update_cache(src, last_ack=TimeManager.get_formatted_time())
                self.client_delegate.receive(dict_payload)
        except KeyboardInterrupt:
            sock.close()
            sys.exit(1)

    def send_udp(self, query, dst):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(query, self.get_udp_addr(dst))
        self.network_cache.update_cache(dst, last_sent=TimeManager.get_formatted_time())

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

    def stream(self, query, dst):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.get_tcp_addr(dst))
        self.send_msg_tcp(sock, query)
        raw_msglen = self.recvall_tcp(sock, 4)
        if not raw_msglen:
            yield None
        msglen = struct.unpack('>I', raw_msglen)[0]
        for packet in self.receive_stream_packet(sock, msglen):
            yield packet

    def receive_stream_packet(self, sock, msglen):
        data_len = 0
        while data_len < msglen:
            packet = sock.recv(msglen - data_len)
            if not packet:
                yield None
            yield packet
            data_len += len(packet)

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

    def get_query_id(self):
        return self.network_cache.get_query_id()

    def get_src_addr(self):
        return (self.ip, self.network_cache.tcp_port, self.network_cache.udp_port)

    def get_udp_addr(self, dst):
        return (dst[0], dst[2])

    def get_tcp_addr(self, dst):
        return (dst[0], dst[1])
