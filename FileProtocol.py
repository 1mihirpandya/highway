import os
import struct
import json
import socket

class FileProtocol():
    def __init__(self):
        self.network_client = None

    def set_network_client(self, network_client):
        self.network_client = network_client

    def read_in_chunks(self, file, chunk_size=1024):
        while True:
            data = file.read(chunk_size)
            if not data:
                break
            yield data

    def load_file(self, filename):
        contents = None
        with open(filename, 'rb') as f:
            for chunk in self.read_in_chunks(f):
                if contents == None:
                    contents = chunk
                else:
                    contents += chunk
        return chunk

    def receive(self, query, sock):
        with open(query["payload"], 'rb') as f:
            size = os.stat(query["payload"]).st_size
            msg = struct.pack('>I', size)
            sock.sendall(msg)
            for chunk in self.read_in_chunks(f):
                sock.sendall(chunk)

    def send(self, query, dst):
        query["src"] = self.network_client.get_src_addr()
        query["id"] = self.network_client.network_cache.get_query_id()
        print(query)
        json_query = json.dumps(query).encode()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.network_client.get_tcp_addr(dst))
        self.network_client.send_msg_tcp(sock, json_query)
        raw_msglen = self.network_client.recvall_tcp(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack('>I', raw_msglen)[0]
        with open("xxxyz", 'wb') as f:#query["payload"], 'wb') as f:
            print("opened")
            data_len = 0
            while data_len < msglen:
                packet = sock.recv(msglen - data_len)
                if not packet:
                    return None
                f.write(packet)
                data_len += len(packet)
        #self.mark_sync_query_as_completed(query["id"])
