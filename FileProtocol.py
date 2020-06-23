import os
import struct
import json
import socket
from JSONTemplate import *
from NetworkClient import NetworkClient
from FileDelegate import FileDelegate
import time

class FileProtocol():
    def __init__(self, network_client):
        self.file_delegate = FileDelegate(self, network_client)

    def get_file_cache(self):
        return self.file_delegate.get_file_cache()

    def initialize_files(self, root):
        self.file_delegate.set_file_root(root)
        return self.file_delegate.check_folder_hierarchy(root)

    def set_file_root(self, root):
        self.file_delegate.set_file_root(root)

    def get_file(self, filename, addr):
        query = JSONQueryRPCTemplate.template
        query["query"] = "load_file"
        query["payload"] = filename
        query["protocol"] = Constants.Network.STREAM
        return self.file_delegate.stream_to_file(filename, query, addr)

    def load_file(self, filename):
        for packet in self.file_delegate.stream_from_file(filename):
            yield packet

    def check_cache_for_file(self, filename):
        res = self.file_delegate.check_cache(filename)
        if res:
            return filename, tuple(res)
        return res

    #UNDERLYING SERVICES
    def update_file_dep(self, files):
        self.file_delegate.update_file_cache()
        return self.file_delegate.check_folder_hierarchy(files)
