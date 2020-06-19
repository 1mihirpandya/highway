import json
from Constants import *



#Messaging
class JSONQueryUDPTemplate:
    template = {
    "id":"xxxx",
    "type":"query",
    "src":"",
    "dst":"",
    "protocol":"UDP",
    "query":"",
    "payload":"",
    "ttl":0
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONResponseUDPTemplate:
    template = {
    "id":"xxxx",
    "type":"response",
    "src":"",
    "dst":"",
    "protocol":"UDP",
    "query":"",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONHeartbeatUDPTemplate:
    template = {
    "id":"xxxx",
    "type":Constants.Network.HEARTBEAT,
    "src":"",
    "protocol":"UDP",
    "query":"",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONHeartbeatAckTemplate:
    template = {
    "id":"xxxx",
    "type":Constants.Network.ACK,
    "src":"",
    "protocol":"UDP"
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONQueryRPCTemplate:
    template = {
    "id":"xxxx",
    "type":"query",
    "src":"",
    "dst":"",
    "protocol":"TCP",
    "query":"",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONResponseRPCTemplate:
    template = {
    "id":"xxxx",
    "type":"response",
    "src":"",
    "protocol":"TCP",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))
