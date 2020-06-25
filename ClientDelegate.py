from ClientNode import *
from NetworkClient import *
from Decorator import *

class ClientDelegate:
    def __init__(self, client_node, network_client):
        self.client_node = client_node
        self.network_client = network_client
        self.network_client.client_delegate = self
        self.network_cache = self.network_client.network_cache

    def get_neighbors(self):
        return self.client_node.neighbors

    def find_neighbor_file_location(self, filename):
        neighbors = list(self.network_cache.neighbors.keys())
        for neighbor in neighbors:
            neighbor_state = self.network_cache.neighbors[neighbor]
            if not neighbor_state:
                continue
            if filename in neighbor_state.files:
                return neighbor
        return None

    def cache_neighbor_files(self, src, files):
        self.network_cache.update_cache(self.get_neighbors(), src, files=files)

    def cache_neighbor_neighbors(self, src, neighbors):
        self.network_cache.update_cache(self.get_neighbors(), src, neighbors_of_neighbors=neighbors)

    def send(self, query, dsts, udpsync=False):
        query["src"] = self.get_src_addr()
        if query["type"] != Constants.Network.HEARTBEAT and query["type"] != Constants.Network.ACK:
            query["id"] = self.network_cache.get_query_id(waiting=len(dsts))
        #dealing with udp messages
        if query["protocol"] == Constants.Network.UDP:
            if udpsync:
                self.make_query_sync(query["id"])
            for dst in dsts:
                query["dst"] = dst
                self.network_client.send_udp(json.dumps(query).encode(), dst)
            return query["id"]
        #dealing with tcp messages
        elif query["protocol"] == Constants.Network.TCP:
            response = self.network_client.send_rpc(json.dumps(query).encode(), dsts)
            self.mark_sync_query_as_completed(query["id"])
            if type(response["payload"]) == dict:
                return [val for val in response["payload"].values()]
            else:
                return response["payload"]

    def receive(self, query):
        if query["src"]:
            query["src"] = tuple(query["src"])
        if "dst" in query and query["dst"]:
            query["dst"] = tuple(query["dst"])
        if query["protocol"] == Constants.Network.UDP:
            self.receive_udp(query)
        elif query["protocol"] == Constants.Network.TCP:
            return self.receive_tcp(query)

    def receive_udp(self, query):
        if query["type"] == Constants.Network.HEARTBEAT:
            if query["src"] not in self.get_neighbors():
                self.client_node.notify_not_neighbor(query["src"])
            else:
                getattr(self, query["query"])(query["src"], query["payload"])
                resp = JSONHeartbeatAckTemplate.template
                resp["src"] = self.get_src_addr()
                self.network_client.send_udp(json.dumps(resp).encode(), query["src"])
        if query["type"] == Constants.Network.QUERY:
            self.respond_udp(query)
        if query["type"] == Constants.Network.RESPONSE:
            self.process_udp_response(query)

    def receive_tcp(self, query):
        response = JSONQueryRPCTemplate.template
        response["src"] = query["dst"]
        response["dst"] = query["src"]
        response["payload"] = getattr(self.client_node, query["query"])(query["payload"])
        return json.dumps(response).encode()

    @thread
    def respond_udp(self, query):
        resp_content = getattr(self.client_node, query["query"])(query["src"], query["payload"])
        query["ttl"] -= 1
        if resp_content or query["ttl"] <= 0 or len(self.client_node.neighbors) <= 1:
            response = JSONResponseUDPTemplate.template
            response["id"] = query["id"]
            response["src"] = query["dst"]
            response["dst"] = query["src"]
            response["payload"] = resp_content
            self.network_client.send_udp(json.dumps(response).encode(), response["dst"])
        else:
            self.forward(query, query["src"])

    def forward(self, query, src):
        if not self.network_cache.has_id(query["id"]):
            query["src"] = self.get_src_addr()
            self.network_cache.cache_query(None, query["id"], src, None, len(self.client_node.neighbors)-1)
            for neighbor in self.client_node.neighbors:
                if neighbor != src:
                    query["dst"] = neighbor
                    self.network_client.send_udp(json.dumps(query).encode(), query["dst"])

    @thread
    def process_udp_response(self, query):
        query_ids = self.network_cache.query_ids
        if query_ids[query["id"]].src != None: #udp w/ src means it was forwarded, and forwarded implies sync
            if query_ids[query["id"]].status == 1:
                return
            query["src"] = self.get_src_addr()
            query["dst"] = query_ids[query["id"]].src
            query_ids[query["id"]].waiting -= 1
            if query["payload"]:
                self.network_client.send_udp(json.dumps(query).encode(), query["dst"])
                self.network_client.cache_response(*query["payload"])
                self.mark_query_as_completed(query["id"])
            elif query_ids[query["id"]].waiting <= 0:
                self.network_client.send_udp(json.dumps(query).encode(), query["dst"])
                self.mark_query_as_completed(query["id"])
        elif query_ids[query["id"]].query == "get_neighbor_status":
            neighbors = self.network_cache.neighbors
            if TimeManager.get_time_diff_in_seconds(neighbors[query["payload"]["neighbor"]].last_sent, query["payload"]["last_ack"]) < Constants.Heartbeat.TIMEOUT:
                neighbors[neighbor].status = CacheConstants.OKAY
            self.mark_query_as_completed(query["id"])
        else:
            if query_ids[query["id"]].status == 1 or query_ids[query["id"]].payload:
                return
            query_ids[query["id"]].waiting -= 1
            if query["payload"]:
                query_ids[query["id"]].payload = query["payload"]
                self.mark_query_as_completed(query["id"])
            elif query_ids[query["id"]].waiting <= 0:
                self.mark_query_as_completed(query["id"])

    def mark_query_as_completed(self, id): #THIS METHOD IS NO LONGER NECESSARY
        self.network_cache.query_ids[id].status += 1

    def mark_sync_query_as_completed(self, id):
        self.network_cache.query_ids[id].status = 1

    def make_query_sync(self, id):
        self.network_cache.query_ids[id].status = 2

    def completed(self, id):
        now = TimeManager.get_formatted_time()
        if TimeManager.get_time_diff_in_seconds(now, self.network_cache.query_ids[id].time) > Constants.Heartbeat.TIMEOUT:
            return True
        return self.network_cache.query_ids[id].status > 2

    def get_resp(self, id):
        return self.network_cache.query_ids[id].payload

    def get_src_addr(self):
        return self.network_cache.get_src_addr()

    #UNDERLYING SERVICES
    def listen_to_udp_port(self):
        self.network_client.attach_to_udp_port()

    def listen_to_tcp_port(self):
        self.network_client.attach_to_tcp_port()
