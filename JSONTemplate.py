import json



#Messaging
class JSONQueryUDPTemplate:
    template = {
    "id":"xxxx",
    "type":"query",
    "src":"",
    "query":"",
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONHeartbeatUDPTemplate:
    template = {
    "id":"xxxx",
    "type":"heartbeat",
    "src":"",
    "query":"",
    "payload":"",
    }
    length_without_src_query_payload = len(json.dumps(template))

class JSONHeartbeatAckTemplate:
    template = {
    "id":"xxxx",
    "type":"heartbeat_ack",
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
