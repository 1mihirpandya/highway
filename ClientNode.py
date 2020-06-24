from GatekeeperClient import *
from NetworkClientCache import *
from NetworkClient import *
from FileProtocol import FileProtocol
from ClientProtocol import ClientProtocol
from Decorator import *
import argparse
import math
import socket
import sys

#ClientNode sends a dictionary to NetworkClient, and receives a dictionary from NetworkClient
class ClientNode:
    def __init__(self):
        self.neighbors = []
        self.files = []
        hostname = socket.gethostname()
        self.ip = socket.gethostbyname(hostname)
        self.network_cache = NetworkClientCache(self.ip)
        network_client = NetworkClient(None, self.network_cache, None, self.ip)
        self.file_protocol = FileProtocol(network_client)
        self.client_protocol = ClientProtocol(self, network_client)

    def initialize_files(self, root):
        self.files = self.file_protocol.initialize_files(root)
        return self.files

    def get_file_cache(self):
        return self.file_protocol.get_file_cache()

    def get_file(self, filename):
        loc = None
        resp = self.find_file(filename)
        if resp:
            _, loc = resp
        if loc:
            if self.file_protocol.get_file(filename, loc):
                self.files.append(filename)

    def find_file(self, filename):
        on_machine = self.check_for_file(None, filename)
        if on_machine:
            return on_machine
        else:
            return self.client_protocol.ask_neighbors_for_file(filename, self.neighbors)

    def check_for_file(self, src, filename):
        if filename in self.files:
            return filename, self.get_src_addr()
        return self.file_protocol.check_cache_for_file(filename) or self.client_protocol.check_neighbor_files(filename)

    def connect_to_network(self):
        gatekeeper_suggestion = GatekeeperClient.connect_to_network(self.get_src_addr())
        if not gatekeeper_suggestion:
            return
        potential_connections = [gatekeeper_suggestion]
        self.connect(potential_connections)

    def connect(self, potential_connections):
        if len(self.neighbors) >= Constants.Network.MAX_NEIGHBORS:
            return
        while len(potential_connections) > 0: #or TTL/round count?
            candidate = potential_connections[0]
            if candidate == "|":
                potential_connections.append("|")
                continue
            candidate_neighbors = self.client_protocol.get_neighbors(candidate)
            if len(candidate_neighbors) < Constants.Network.MAX_NEIGHBORS:
                if candidate in self.neighbors:
                    break ##CHANGE TO CONTINUE MAYBE????
                complete = self.add_neighbor(candidate)
                if complete:
                    return
            potential_connections.extend(candidate)
        self.connect_to_network()
        #no open positions, an issue for another time...

    def add_neighbor(self, potential_neighbor):
        status, files = self.client_protocol.add_neighbor(potential_neighbor)
        if status != 0: #for membership, 0 is no, anything else is yes
            self.neighbors.append(tuple(potential_neighbor))
            return True
        return False

    def confirm_neighbor(self, potential_neighbor):
        #other checks to see if this node can accept another connection.
        #like net traffic? existing connections? available cpu/memory?
        if tuple(potential_neighbor) not in self.neighbors and len(self.neighbors) <= Constants.Network.MAX_NEIGHBORS:
            self.neighbors.append(tuple(potential_neighbor))
            return 1, self.files
        return 0, None

    def get_neighbors(self, _):
        return self.neighbors

    def get_neighbor_status(self, src, neighbor):
        neighbor = tuple(neighbor)
        if self.network_cache.neighbors[neighbor]:
            return neighbor, self.network_cache.neighbors[neighbor].last_ack
        else:
            return neighbor, "00-00-0000 00:00:00"

    """def update_filelist(self, files):
        for file in files:
            if file not in self.files:
                self.files.append(file)
    """

    #UNDERLYING SERVICES
    @listener_thread
    def listen_to_udp_port(self):
        self.client_protocol.listen_to_udp_port()

    @listener_thread
    def listen_to_tcp_port(self):
        self.client_protocol.listen_to_tcp_port()

    @continuous_thread(Constants.Heartbeat.TIMEOUT)
    def update_gatekeeper(self):
        GatekeeperClient.update_gatekeeper(self.get_src_addr(), len(self.neighbors))

    @continuous_thread(Constants.Heartbeat.FILES_FREQUENCY)
    def heartbeat_filelist(self):
        self.client_protocol.heartbeat(Constants.Heartbeat.FILES, self.files, self.neighbors)

    @continuous_thread(Constants.Heartbeat.NEIGHBORS_FREQUENCY)
    def heartbeat_neighbors(self):
        self.client_protocol.heartbeat(Constants.Heartbeat.NEIGHBORS, self.neighbors, self.neighbors)

    @continuous_thread(Constants.Heartbeat.TIMEOUT)
    def failure_detector(self):
        to_delete = []
        ref = self.network_cache.neighbors
        keys = list(ref.keys())
        for neighbor in keys:
            neighbor_of_neighbor_addrs = ref[neighbor].neighbors
            if not ref[neighbor].last_sent:
                continue
            if ref[neighbor].status == CacheConstants.WARNING and TimeManager.get_time_diff_in_seconds(ref[neighbor].last_sent, ref[neighbor].last_ack) > 2 * Constants.Heartbeat.TIMEOUT:
                #break off connection and connect to neighbor
                if neighbor_of_neighbor_addrs:
                    self.connect(neighbor_of_neighbor_addrs)
                to_delete.append(neighbor)
                GatekeeperClient.notify_client_dead(neighbor)
            elif TimeManager.get_time_diff_in_seconds(ref[neighbor].last_sent, ref[neighbor].last_ack) > Constants.Heartbeat.TIMEOUT:
                ref[neighbor].status = CacheConstants.WARNING
                self.client_protocol.get_neighbor_status(neighbor, neighbor_of_neighbor_addrs)
        for addr in to_delete:
            if addr in self.neighbors:
                self.neighbors.remove(addr)
            del ref[addr]

    @continuous_thread(Constants.Heartbeat.TIMEOUT)
    def update_file_dep(self):
        self.files = self.file_protocol.update_file_dep(self.files)

    def get_src_addr(self):
        return self.network_cache.get_src_addr()
