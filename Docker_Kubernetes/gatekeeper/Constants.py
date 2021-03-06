class Constants:
    class Network:
        DICT_CONNECTION_TEMPLATE = {"ip": None,"tcp": None,"udp": None}
        NO_CONNECTION = {"ip": -1,"tcp": -1,"udp": -1}
        HEARTBEAT = "heartbeat"
        ACK = "heartbeat_ack"
        QUERY = "query"
        RESPONSE = "response"
        UDP = "UDP"
        TCP = "TCP"
        STREAM = "fstream"
        MAX_NEIGHBORS = 5

    class Heartbeat:
        FILES = "cache_neighbor_files"
        NEIGHBORS = "cache_neighbor_neighbors"
        FILES_FREQUENCY = 5
        NEIGHBORS_FREQUENCY = 1
        TIMEOUT = 15

    class FD:
        SWIM_CONTACT = 3

    class RPC:
        pass

    class JSON:
        pass
