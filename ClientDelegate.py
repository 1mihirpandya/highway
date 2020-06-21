from ClientNode import *
from NetworkClient import *
import threading

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


    def listen_to_ports(self):
        self.network_client.listen_to_ports()

    def cache_neighbor_files(self, src, files):
        print(files)
        self.network_cache.update_cache(src, files=files)

    def cache_neighbor_neighbors(self, src, neighbors):
        self.network_cache.update_cache(src, neighbors_of_neighbors=neighbors)

    def send(self, query, dsts, udpsync=False):
        query["src"] = self.get_src_addr()
        if query["type"] != Constants.Network.HEARTBEAT and query["type"] != Constants.Network.ACK:
            query["id"] = self.network_cache.get_query_id()
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
            #print(query)
            getattr(self, query["query"])(query["src"], query["payload"])
            resp = JSONHeartbeatAckTemplate.template
            resp["src"] = self.get_src_addr()
            self.network_client.send_udp(json.dumps(resp).encode(), query["src"])
        if query["type"] == Constants.Network.QUERY:
            proc_th = threading.Thread(target=self.respond_udp, kwargs={"query":query}, daemon=True)
            proc_th.start()
        if query["type"] == Constants.Network.RESPONSE:
            proc_th = threading.Thread(target=self.process_udp_response, kwargs={"query":query}, daemon=True)
            proc_th.start()

    def receive_tcp(self, query):
        query["src"] = tuple(query["src"])
        query["dst"] = tuple(query["dst"])

        response = JSONQueryRPCTemplate.template
        response["src"] = query["dst"]
        response["dst"] = query["src"]
        response["payload"] = getattr(self.client_node, query["query"])(query["payload"])
        return json.dumps(response).encode()

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
            self.network_cache.cache_query(None, query["id"], src, None)
            for neighbor in self.client_node.neighbors:
                if neighbor != src:
                    query["dst"] = neighbor
                    self.network_client.send_udp(json.dumps(query).encode(), query["dst"])

    def process_udp_response(self, query):
        query_ids = self.network_cache.query_ids
        neighbors = self.network_cache.neighbors
        if query_ids[query["id"]].src != None:
            query["src"] = self.get_src_addr()
            query["dst"] = query_ids[query["id"]].src
            self.network_client.send_udp(json.dumps(query).encode(), query["dst"])
            #CACHE FILE IF HIT
        elif query_ids[query["id"]].query == "get_neighbor_status":
            if TimeManager.get_time_diff_in_seconds(neighbors[query["payload"]["neighbor"]].last_sent, query["payload"]["last_ack"]) < Constants.Heartbeat.TIMEOUT:
                neighbors[neighbor].status = CacheConstants.OKAY
        else:
            query_ids[query["id"]].payload = query["payload"]
        self.mark_query_as_completed(query["id"])

    def mark_query_as_completed(self, id):
        self.network_cache.query_ids[id].status += 1

    def mark_sync_query_as_completed(self, id):
        self.network_cache.query_ids[id].status = 1

    def make_query_sync(self, id):
        self.network_cache.query_ids[id].status = 2

    def completed(self, id):
        return self.network_cache.query_ids[id].status > 2

    def get_resp(self, id):
        return self.network_cache.query_ids[id].payload

    def get_src_addr(self):
        return self.network_cache.get_src_addr()
