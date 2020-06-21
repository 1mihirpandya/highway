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
        self.set_file_root(root)
        #files = []
        #folders = [root]
        return self.file_delegate.get_folder_hierarchy(root)
        """while len(folders) > 0:
            curr_path = folders[0]
            print(curr_path)
            curr_files, curr_folders = self.file_delegate.get_folder_hierarchy(curr_path)
            for file in curr_files:
                print(files)
                files.append(file)
            for folder in curr_folders:
                folders.append(curr_path + "/" + folder)
            folders = folders[1:]"""
        #return files

    def set_file_root(self, root):
        self.file_delegate.set_file_root(root)


    def get_file(self, filename, addr):
        query = JSONQueryRPCTemplate.template
        query["query"] = "load_file"
        query["payload"] = filename
        query["protocol"] = "fstream"
        return self.file_delegate.stream_to_file(filename, query, addr)

    def load_file(self, filename):
        for packet in self.file_delegate.stream_from_file(filename):
            yield packet

    def check_dep(self, files):
        return self.file_delegate.check_folder_hierarchy(files)
