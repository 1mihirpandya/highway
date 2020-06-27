from flask import Flask, request
from flask_restful import Api, Resource, reqparse
from Constants import *
import math
import json
import redis

app = Flask(__name__)
api = Api(app)
redis_write = "127.0.0.1"
redis_read = "10.104.97.21"
redis_port = 6379


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

def addr_to_redis(addr):
    return addr[0] + "," + str(addr[1]) + "," + str(addr[2])

def redis_to_addr(s):
    s = s.decode()
    s = s.split(",")
    return (s[0], int(s[1]), int(s[2]))

@app.route('/g', methods=['GET'])
def get():
    for key in r.scan_iter():
        print(key, r.get(key))
    return "User already exists at {}", 400

@app.route('/connect', methods=['POST'])
def connect():
    addr = get_addr_from_dict(request.json)
    exist = r.exists(addr_to_redis(addr))
    if addr and not exist:
        connection_candidate = None
        for key in r.scan_iter():
            print(key)
            num_connections = r.get(key)
            if num_connections < 5:
                connection_candidate = redis_to_addr(key)
                break
        r.set(addr_to_redis(addr), 0)
        resp = connection_response_template
        if connection_candidate:
            resp = get_dict_from_addr(connection_candidate)
        return json.dumps(resp), 200
    return "User already exists at {}".format(addr), 400

@app.route('/update', methods=['POST'])
def update():
    addr = get_addr_from_dict(request.json)
    r.set(addr_to_redis(addr), get_len_from_dict(request.json))
    #clients[addr] = get_len_from_dict(request.json)
    return "Updated".format(addr), 200

@app.route('/delete', methods=['DELETE'])
def delete():
    addr = get_addr_from_dict(request.json)
    #if addr in clients:
    #    del clients[addr]
    r.delete(addr_to_redis(addr))
    return "{} deleted".format(addr), 200

if __name__ == "__main__":
    global r
    r = redis.StrictRedis(host=redis_write, port=redis_port)
    r.set_response_callback("GET", int)
    app.run(host="0.0.0.0",port=5000)
