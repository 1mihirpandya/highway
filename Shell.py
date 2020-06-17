from ClientNode import *

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-ip", "--hostIP", help="host IP", required=False)
    parser.add_argument("-udp", "--udpPort", help="udp port", required=False)
    parser.add_argument("-tcp", "--tcpPort", help="tcp port", required=False)
    #parser.add_argument("-f", "--files", help="existing files", required=False)
    parser.add_argument("-t", "--testCommands", help="test commands", required=False)
    parser.add_argument("-tn", "--testNeighbor", help="test neighbor", required=False)
    return parser.parse_args()

def delegate(input):
    if input.startswith("addfile "):
        filename = input[len("addfile "):]
        client.files.append(filename)
        print("Current Files:", client.files)
    elif input.startswith("connect"):
        client.connect_to_network()
        print("Current Neighbors:", client.neighbors)
    elif input.startswith("testneighbor "):
        a = input[len("testneighbor "):].split()
        client.neighbors.append((a[0], int(a[1])))
        print("Current Neighbors:", client.neighbors)
    elif input.startswith("start"):
        listener_th = threading.Thread(target=client.network_client.listen_to_ports, daemon=True)
        listener_th.start()
        file_heartbeat_th = threading.Thread(target=client.heartbeat_filelist, daemon=True)
        file_heartbeat_th.start()
        file_heartbeat_th = threading.Thread(target=client.heartbeat_neighbors, daemon=True)
        file_heartbeat_th.start()
        swim_th = threading.Thread(target=client.failure_detector, daemon=True)
        swim_th.start()
        print("Services running...")
        print("Heartbeat intitiated...")
        print("IP = {}".format(client.ip))
        print("UDP Port @ {}".format(client.network_cache.udp_port))
        print("TCP Port @ {}".format(client.network_cache.tcp_port))
    elif input.startswith("printfiles"):
        print("Current Files:", client.files)
    elif input.startswith("printneighbors"):
        print("Current Neighbors:", client.neighbors)
    elif input.startswith("getneighborsfiles"):
        client.get_neighbor_filelist()
        print("Current Files:", client.files)
    elif input.startswith("showcache"):
        print("Query Ids: ", client.network_cache.query_ids, "\n")
        for neighbor in client.network_cache.neighbors:
            print("Neighbor: {}".format(neighbor))
            print(client.network_cache.neighbors[neighbor].printable())

if __name__ == "__main__":
    args = parse_arguments()
    global client
    client = ClientNode()
    try:
        resp = input("FastTrakk >> ")
        while resp != "exit":
            delegate(resp)
            resp = input("FastTrakk >> ")
    except KeyboardInterrupt:
        sys.exit(1)
