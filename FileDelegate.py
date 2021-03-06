from ClientNode import *
from NetworkClient import *
from FileCache import *
import os

class FileDelegate:
    def __init__(self, file_protocol, network_client):
        self.file_protocol = file_protocol
        self.network_client = network_client
        self.network_client.file_delegate = self
        self.file_cache = FileCache()

    def get_file_cache(self):
        return self.file_cache

    def stream_to_file(self, filename, query, dst):
        query["src"] = self.network_client.get_src_addr()
        query["id"] = self.network_client.get_query_id()
        f = open(os.path.join(self.file_cache.root, filename), 'wb')
        for packet in self.network_client.stream(json.dumps(query).encode(), dst):
            if packet == None:
                f.close()
                os.remove(os.path.join(self.file_cache.root, filename))
                self.mark_sync_query_as_completed(query["id"])
                return False
            f.write(packet)
        f.close()
        self.file_cache.add(filename)
        self.mark_sync_query_as_completed(query["id"])
        return True

    def stream_from_file(self, filename, chunk_size=1024):
        path = self.file_cache.get(filename)[0]
        size = os.stat(path).st_size
        msg = struct.pack('>I', size)
        yield msg
        with open(path, 'rb') as f:
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

    def set_file_root(self, root):
        self.file_cache.root = root

    def check_folder_hierarchy(self, curr_files):
        folder = self.file_cache.root
        for file in curr_files:
            paths = self.file_cache.get(file)
            if not paths:
                break
            for path in paths:
                if not os.path.isfile(path):
                    self.file_cache.prune(file, path)
            if len(self.file_cache.get(file)) == 0:
                self.file_cache.remove_file(file)
        for (root, dirs, fs) in os.walk(folder):
            for name in fs:
                if not self.file_cache.check(name, os.path.join(root, name)):
                    self.file_cache.add(name, os.path.join(root, name))
        return self.file_cache.get_files()

    def check_cache(self, filename):
        cached_files = list(self.file_cache.cached_files.keys())
        if filename in cached_files:
            return self.file_cache.cached_files[filename].addr

    @thread_safe
    def update_file_cache(self):
        cached_files = list(self.file_cache.cached_files.keys())
        for file in cached_files:
            self.file_cache.cached_files[file].persistance -= 1
            if self.file_cache.cached_files[file].persistance == 0:
                del self.file_cache.cached_files[file]

    def cache(self, filename, addr):
        self.file_cache.store(filename, addr)

    ####################
    #DEPRECATED
    def get_folder_hierarchy(self, foldername):
        files = []
        for (root, dirs, fs) in os.walk(foldername):
            for name in fs:
                self.file_cache.add(name, os.path.join(root, name))
                files.append(name)
        return files
