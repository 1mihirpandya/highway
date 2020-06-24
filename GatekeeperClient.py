import requests
import json
from Constants import *

class GatekeeperClient:
    URL = "http://192.168.1.95:5000"
    #URL = "http://127.0.0.1:8080"
    CONNECT = "/connect"
    DELETE = "/delete"
    UPDATE = "/update"
    def connect_to_network(ip_and_ports):
        data = {'ip':ip_and_ports[0], 'tcp':ip_and_ports[1], 'udp':ip_and_ports[2]}
        # sending get request and saving the response as response object
        response = requests.post((GatekeeperClient.URL + GatekeeperClient.CONNECT), json=data)
        if response:
            content = json.loads(response.text)
            if content == Constants.Network.NO_CONNECTION:
                return None
            else:
                potential_connection = (content["ip"], content["tcp"], content["udp"])
                return potential_connection

    def notify_client_dead(addr):
        data = {'ip':addr[0], 'tcp':addr[1], 'udp':addr[2]}
        response = requests.delete((GatekeeperClient.URL + GatekeeperClient.DELETE), json=data)

    def update_gatekeeper(addr, num_connections):
        data = {'ip':addr[0], 'tcp':addr[1], 'udp':addr[2], "len":num_connections}
        response = requests.post((GatekeeperClient.URL + GatekeeperClient.UPDATE), json=data)
