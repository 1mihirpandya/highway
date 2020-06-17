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

@app.route('/connect', methods=['POST'])
def connect():
    print("\n\n")
    print(clients)
    #print(request.json)
    ip_and_ports = get_addr_from_dict(request.json)
    #print(ip_and_ports)
    if ip_and_ports and (ip_and_ports not in clients):
        connection_candidate = None
        minimum = math.inf
        for candidate in clients:
            num_connections = clients[candidate]
            if (not connection_candidate) or num_connections <= minimum:
                minimum = num_connections
                connection_candidate = candidate
        clients[ip_and_ports] = 0
        resp = connection_response_template
        if connection_candidate:
            resp = get_dict_from_addr(connection_candidate)
        #print(resp)
        return json.dumps(resp), 200
    return "User already exists at {}".format(ip_and_ports), 400

@app.route('/delete', methods=['DELETE'])
def delete():
    addr = get_addr_from_dict(request.json)
    if addr in clients:
        del clients[addr]
    print("\n\n")
    print(clients)
    return "{} deleted".format(addr), 200

"""
class Connect(Resource):
    def post(self):
        print(clients)
        ip_and_ports = request.args.get('ip_and_ports')
        print(ip_and_ports)
        if ip_and_ports and (ip_and_ports not in clients):
            connection_candidate = None
            minimum = math.inf
            for candidate in clients:
                num_connections = clients[candidate]
                if (not connection_candidate) or num_connections <= minimum:
                    minimum = num_connections
                    connection_candidate = candidate
            clients[ip_and_ports] = 0
            return connection_candidate, 200
        return "User already exists at {}".format(ip_and_ports), 400

    def get(self, name):
        for user in users:
            if(name == user["name"]):
                return user, 200
        return "User not found", 404

    def post(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("age")
        parser.add_argument("occupation")
        args = parser.parse_args()

        for user in users:
            if(name == user["name"]):
                return "User with name {} already exists".format(name), 400

        user = {
            "name": name,
            "age": args["age"],
            "occupation": args["occupation"]
        }
        users.append(user)
        return user, 201

    def put(self, name):
        parser = reqparse.RequestParser()
        parser.add_argument("age")
        parser.add_argument("occupation")
        args = parser.parse_args()

        for user in users:
            if(name == user["name"]):
                user["age"] = args["age"]
                user["occupation"] = args["occupation"]
                return user, 200

        user = {
            "name": name,
            "age": args["age"],
            "occupation": args["occupation"]
        }
        users.append(user)
        return user, 201

    def delete(self, name):
        global users
        users = [user for user in users if user["name"] != name]
        return "{} is deleted.".format(name), 200
    """

app.run(host="0.0.0.0",port=5000)
