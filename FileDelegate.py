from ClientNode import *
from NetworkClient import *
import os

class FileDelegate:
    def __init__(self, file_protocol, network_client):
        self.file_protocol = file_protocol
        self.network_client = network_client
        self.network_client.file_delegate = self

    def stream_to_file(self, filename, query, dst):
        query["src"] = self.network_client.get_src_addr()
        query["id"] = self.network_client.get_query_id()
        with open("filename", 'wb') as f:
            for packet in self.network_client.stream(json.dumps(query).encode(), query["dst"]):
                if packet == None:
                    self.mark_sync_query_as_completed(query["id"])
                    return False
                f.write(packet)
        self.mark_sync_query_as_completed(query["id"])
        return True

    def stream_from_file(self, filename, chunk_size=1024):
        size = os.stat(filename).st_size
        msg = struct.pack('>I', size)
        yield msg
        with open(filename, 'rb') as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                yield data

    def receive(self, query, sock):
        for packet in getattr(self.file_protocol, query["query"])(query["payload"]):
            sock.sendall(packet)

    def mark_sync_query_as_completed(self, id):
        self.network_client.network_cache.query_ids[id].status = 1
