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
        self.files = []
        self.connection_load = 0.3
        self.num_clients = math.inf
        hostname = socket.gethostname()
        self.ip = socket.gethostbyname(hostname)
        self.network_cache = NetworkClientCache(self.ip)
        self.network_client = NetworkClient(self, self.network_cache, self.ip)

    def connect_to_network(self):
        gatekeeper_suggestion = GatekeeperClient.connect_to_network(self.network_client.get_src_addr()) #http request to gatekeeper
        if not gatekeeper_suggestion:
            return
        potential_connections = [gatekeeper_suggestion]
        self.connect(potential_connections)

    def connect(self, potential_connections):
        #num_clients = math.inf #answer from gatekeeper
        query = JSONQueryRPCTemplate.template
        query["src"] = self.network_client.get_src_addr()
        query["query"] = "get_neighbors"
        while len(potential_connections) > 0: #or TTL/round count?
            candidate = potential_connections[0]
            if candidate == "|":
                potential_connections.append("|")
                continue
            query["dst"] = candidate
            #neighbors_of_candidate = candidate.get_neighbors(network_client)
            response = self.network_client.send_rpc(query)
            if len(response["payload"]) < self.connection_load * self.num_clients:
                if candidate in self.neighbors:
                    break
                complete = self.add_neighbor(candidate)
                if complete:
                    break
            potential_connections.extend(response["payload"])
        #no open positions, an issue for another time...

    def add_neighbor(self, dst):
        query = JSONQueryRPCTemplate.template
        query["src"] = self.network_client.get_src_addr()
        query["query"] = "confirm_neighbor"
        query["dst"] = dst
        query["payload"] = self.network_client.get_src_addr()
        #neighbor.confirm_neighbor()
        response = self.network_client.send_rpc(query)
        if response["payload"]["status"] != 0: #for membership, 0 is no, anything else is yes
            self.update_filelist(None, response["payload"]["files"])
            self.neighbors.append(dst)
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
        if tuple(payload) not in self.neighbors and len(self.neighbors) < self.connection_load * self.num_clients:
            response = JSONResponseRPCTemplate.template
            response["src"] = self.network_client.get_src_addr()
            response["payload"]["status"] = 1
            response["payload"]["files"] = list(self.neighbors)
            self.neighbors.append(tuple(payload))
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

    def get_neighbor_status(self, src, neighbor):
        neighbor = tuple(neighbor)
        if self.network_cache.neighbors[neighbor]:
            return {
            "neighbor": neighbor,
            "last_ack": self.network_cache.neighbors[neighbor].last_ack
            }
        else:
            return {
            "neighbor": neighbor,
            "last_ack": "00-00-0000 00:00:00"
            }

    def update_filelist(self, src, files):
        for file in files:
            if file not in self.files:
                self.files.append(file)

    def update_neighbors(self, src, neighbors):
        self.network_cache.update_cache(src, neighbors_of_neighbors=neighbors)

    def get_filelist(self, payload):
        response = JSONResponseRPCTemplate.template
        response["src"] = self.network_client.get_src_addr()
        response["payload"] = self.files
        return response

    def heartbeat_filelist(self):
        self.network_client.heartbeat(Constants.Heartbeat.FILES, self.files, self.neighbors, Constants.Heartbeat.FILES_FREQUENCY)

    def heartbeat_neighbors(self):
        self.network_client.heartbeat(Constants.Heartbeat.NEIGHBORS, self.neighbors, self.neighbors, Constants.Heartbeat.NEIGHBORS_FREQUENCY)

    def failure_detector(self):
        try:
            while True:
                time.sleep(Constants.Heartbeat.TIMEOUT)
                to_delete = []
                ref = self.network_cache.neighbors
                #print("failure detection ", ref.keys())
                for neighbor in ref:
                    #print("failure detection a", neighbor)
                    neighbor_of_neighbor_addrs = ref[neighbor].neighbors
                    if not ref[neighbor].last_sent:
                        continue
                    if ref[neighbor].status == CacheConstants.WARNING and TimeManager.get_time_diff_in_seconds(ref[neighbor].last_sent, ref[neighbor].last_ack) > 2 * Constants.Heartbeat.TIMEOUT:
                        #break off connection and connect to neighbor
                        if neighbor_of_neighbor_addrs:
                            self.connect(neighbor_of_neighbor_addrs)
                        to_delete.append(neighbor)
                        GatekeeperClient.notify_client_dead(neighbor)
                        #send message to gatekeeper
                    elif TimeManager.get_time_diff_in_seconds(ref[neighbor].last_sent, ref[neighbor].last_ack) > Constants.Heartbeat.TIMEOUT:
                        ref[neighbor].status = CacheConstants.WARNING
                        self.network_client.send_udp_query("get_neighbor_status", neighbor, random.sample(neighbor_of_neighbor_addrs, min(len(neighbor_of_neighbor_addrs),3)))
                #print("failure detection d", to_delete)
                for addr in to_delete:
                    if addr in self.neighbors:
                        #print("failure detection ind", addr)
                        self.neighbors.remove(addr)
                        #print("failure detection ind2", self.neighbors)
                    del ref[addr]
                #print()
        except KeyboardInterrupt:
            sys.exit(1)
