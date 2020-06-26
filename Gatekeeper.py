from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from Constants import *
import math
import json

app = Flask(__name__)
api = Api(app)

clients = {}

connection_response_template = Constants.Network.NO_CONNECTION
def get_addr_from_dict(dict):
    return (dict["ip"], dict["tcp"], dict["udp"])

def get_dict_from_addr(addr):
    dict = Constants.Network.DICT_CONNECTION_TEMPLATE
    dict["ip"] = addr[0]
    dict["tcp"] = addr[1]
    dict["udp"] = addr[2]
    return dict

def get_len_from_dict(dict):
    return dict["len"]

@app.route('/connect', methods=['POST'])
def connect():
    #print(request.json)
    ip_and_ports = get_addr_from_dict(request.json)
    #print(ip_and_ports)
    print("\n\n")
    print(clients)
    if ip_and_ports and (ip_and_ports not in clients):
        connection_candidate = None
        minimum = math.inf
        for candidate in clients:
            if clients[candidate] < 5:
                connection_candidate = candidate
                break
            """
            num_connections = clients[candidate]
            if (not connection_candidate) or num_connections <= minimum:
                minimum = num_connections
                connection_candidate = candidate
            """
        clients[ip_and_ports] = 0
        resp = connection_response_template
        if connection_candidate:
            resp = get_dict_from_addr(connection_candidate)
        #print(resp)
        return json.dumps(resp), 200
    return "User already exists at {}".format(ip_and_ports), 400

@app.route('/update', methods=['POST'])
def update():
    addr = get_addr_from_dict(request.json)
    clients[addr] = get_len_from_dict(request.json)
    return "Updated".format(addr), 200

@app.route('/delete', methods=['DELETE'])
def delete():
    addr = get_addr_from_dict(request.json)
    if addr in clients:
        del clients[addr]
    print("\n\n")
    print(clients)
    return "{} deleted".format(addr), 200

app.run(host="0.0.0.0",port=5000)
