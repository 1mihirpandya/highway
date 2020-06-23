from JSONTemplate import *
from ClientDelegate import *

import time


class ClientProtocol:
    def __init__(self, client_node, network_client):
        self.client_delegate = ClientDelegate(client_node, network_client)

    def get_neighbors(self, addr):
        query = JSONQueryRPCTemplate.template
        query["query"] = "get_neighbors"
        return self.client_delegate.send(query, addr)

    def add_neighbor(self, addr):
        query = JSONQueryRPCTemplate.template
        query["query"] = "confirm_neighbor"
        query["payload"] = self.get_src_addr()
        return self.client_delegate.send(query, addr)

    def check_neighbor_files(self, filename):
        result = self.client_delegate.find_neighbor_file_location(filename)
        if result:
            return filename, tuple(result)
        return result

    def ask_neighbors_for_file(self, filename, neighbors):
        query = JSONQueryUDPTemplate.template
        query["query"] = "check_for_file"
        query["payload"] = filename
        query["ttl"] = 10
        id = self.client_delegate.send(query, neighbors, True)
        while not self.client_delegate.completed(id):
            time.sleep(0.5)
        result = self.client_delegate.get_resp(id)
        #print(id, result)
        self.client_delegate.mark_sync_query_as_completed(id)
        if result: return tuple(result[1])
        return None

    #UNDERLYING SERVICES

    def listen_to_udp_port(self):
        self.client_delegate.listen_to_udp_port()

    def listen_to_tcp_port(self):
        self.client_delegate.listen_to_tcp_port()

    def heartbeat(self, name, payload, neighbors, frequency):
        try:
            while True:
                msg = JSONHeartbeatUDPTemplate.template
                msg["query"] = name
                msg["payload"] = list(payload)
                self.client_delegate.send(msg, neighbors)
                time.sleep(frequency)
        except KeyboardInterrupt:
            sys.exit(1)

    def get_neighbor_status(self, neighbor, neighbor_of_neighbor_addrs):
        query = JSONQueryUDPTemplate.template
        query["query"] = "get_neighbor_status"
        query["payload"] = neighbor
        num_destinations = min(len(neighbor_of_neighbor_addrs), Constants.FD.SWIM_CONTACT)
        destinations = random.sample(neighbor_of_neighbor_addrs, num_destinations)
        self.client_delegate.send(query, destinations)

    def get_src_addr(self):
        return self.client_delegate.get_src_addr()
