import json
from Constants import *



#Messaging
class JSONQueryUDPTemplate:
    template = {
    "id":"xxxx",
    "type":"query",
    "src":"",
    "dst":"",
    "query":"",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONResponseUDPTemplate:
    template = {
    "id":"xxxx",
    "type":"response",
    "src":"",
    "dst":"",
    "query":"",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONHeartbeatUDPTemplate:
    template = {
    "id":"xxxx",
    "type":Constants.Network.HEARTBEAT,
    "src":"",
    "query":"",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONHeartbeatAckTemplate:
    template = {
    "id":"xxxx",
    "type":Constants.Network.ACK,
    "src":""
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONQueryRPCTemplate:
    template = {
    "id":"xxxx",
    "type":"query",
    "src":"",
    "dst":"",
    "dstport":"",
    "query":"",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONResponseRPCTemplate:
    template = {
    "id":"xxxx",
    "type":"response",
    "src":"",
    "payload":""
    }
    length_without_src_query_payload = len(json.dumps(template))
