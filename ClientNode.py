from NetworkClient import *
from NetworkClientCache import *
from JSONTemplate import *
from GatekeeperClient import *
import argparse
import math

#ClientNode sends a dictionary to NetworkClient, and receives a dictionary from NetworkClient
class ClientNode:
    def __init__(self):
        self.neighbors = []
        self.files = set()
        self.connection_load = 0.3
        self.num_clients = math.inf
        hostname = socket.gethostname()
        self.ip = socket.gethostbyname(hostname)
        self.network_cache = NetworkClientCache()
        self.network_client = NetworkClient(self, self.network_cache, self.ip)


    def connect_to_network(self):
        #query gatekeeper
        gatekeeper_suggestion = GatekeeperClient.connect_to_network(self.network_client.get_src_addr()) #http request to gatekeeper
        if not gatekeeper_suggestion:
            return
        potential_connections = [gatekeeper_suggestion]
        #num_clients = math.inf #answer from gatekeeper
        query = JSONQueryRPCTemplate.template
        neighbor_count = math.inf
        query["src"] = self.network_client.get_src_addr()
        query["query"] = "get_neighbors"
        while len(potential_connections) > 0: #or TTL/round count?
            candidate = potential_connections[0]
            if candidate == "|":
                potential_connections.append("|")
                continue
            query["dst"] = candidate[0]
            query["dstport"] = candidate[1]
            #print("here",candidate)
            response = self.network_client.send_rpc(query)
            if len(response["payload"]) < self.connection_load * self.num_clients:
                complete = self.add_neighbor(*candidate)
                if complete:
                    break
            potential_connections.extend(response["payload"])
        #no open positions, an issue for another time...

    def add_neighbor(self, ip, port, udp_port):
        query = JSONQueryRPCTemplate.template
        query["src"] = self.network_client.get_src_addr()
        query["query"] = "confirm_neighbor"
        query["dst"] = ip
        query["dstport"] = port
        query["payload"] = self.network_client.get_src_addr()
        response = self.network_client.send_rpc(query)
        if response["payload"]["status"] != 0: #for membership, 0 is no, anything else is yes
            self.update_filelist(response["payload"]["files"])
            self.neighbors.append((ip, port, udp_port))
            return True
        return False

    def confirm_neighbor(self, payload):
        #other checks to see if this node can accept another connection.
        #like net traffic? existing connections? available cpu/memory?
        response = JSONResponseRPCTemplate.template
        response["src"] = self.network_client.get_src_addr()
        response["payload"] = {
        "status": 0,
        "files": None
        }
        if len(self.neighbors) < self.connection_load * self.num_clients:
            response = JSONResponseRPCTemplate.template
            response["src"] = self.network_client.get_src_addr()
            response["payload"]["status"] = 1
            response["payload"]["files"] = list(self.neighbors)
            self.neighbors.append(payload)
        return response

    def get_neighbors(self, payload):
        response = JSONResponseRPCTemplate.template
        response["src"] = self.network_client.get_src_addr()
        response["payload"] = list(self.neighbors)
        return response

    def get_neighbor_filelist(self):
        query = JSONQueryRPCTemplate.template
        query["src"] = self.network_client.get_src_addr()
        query["query"] = "get_filelist"
        for neighbor in self.neighbors:
            query["dst"] = neighbor[0]
            query["dstport"] = neighbor[1]
            response = self.network_client.send_rpc(query)
            self.update_filelist(response["payload"])

    def update_filelist(self, files):
        self.files |= set(files)

    def update_neighbors(self, neighbors):
        #would have to update cache
        pass

    def get_filelist(self, payload):
        response = JSONResponseRPCTemplate.template
        response["src"] = self.network_client.get_src_addr()
        response["payload"] = list(self.files)
        return response

    def heartbeat_filelist(self):
        self.network_client.heartbeat(Constants.Heartbeat.FILES, self.files, self.neighbors, Constants.Heartbeat.FILES_FREQUENCY)

    def heartbeat_neighbors(self):
        self.network_client.heartbeat(Constants.Heartbeat.NEIGHBORS, self.neighbors, self.neighbors, Constants.Heartbeat.NEIGHBORS_FREQUENCY)
