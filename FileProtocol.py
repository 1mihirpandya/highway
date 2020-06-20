import os
import struct
import json
import socket
from JSONTemplate import *
from NetworkClient import NetworkClient
from FileDelegate import FileDelegate

class FileProtocol():
    def __init__(self, network_client):
        #self.network_client = network_client
        self.file_delegate = FileDelegate(self, network_client)

    def get_file(self, filename, addr):
        query = JSONQueryRPCTemplate.template
        query["query"] = "load_file"
        query["payload"] = filename
        query["protocol"] = "fstream"
        return self.file_delegate.stream_to_file(filename, query, addr)

    def load_file(self, filename):
        for packet in self.file_delegate.stream_from_file(filename):
            yield packet
