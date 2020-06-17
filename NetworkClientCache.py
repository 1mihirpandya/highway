from enum import Enum
import time
import re
import datetime
from Constants import *
import random

class NeighborInfo():
    def __init__(self):
        self.neighbors = []
        self.last_sent = None
        self.last_ack = None
        self.last_received = None
        #0 = communicating, 1 = warning (hasnt responded in one timeout period), 2 means kick it out
        self.status = 0
        #maybe tcp/udp specific?
    def printable(self):
        return {
        "neighbors":self.neighbors,
        "last_sent":self.last_sent,
        "last_ack":self.last_ack,
        "last_received":self.last_received
        }

class QueryInfo():
    def __init__(self, query):
        self.query = query
        self.dst = None

class NetworkClientCache():
    def __init__(self, ip, query_size=100, size=10):
        self.query_ids = {}
        self.neighbors = {}
        #self.extended_neighbors = {}
        self.ip = ip
        self.tcp_port = None
        self.udp_port = None

    def update_cache(self, neighbor, neighbors_of_neighbors=[], last_sent=None, last_ack=None, last_received=None):
        neighbor = tuple(neighbor)
        if neighbor not in self.neighbors:
            #print("update_cache", "adding neighbor")
            self.neighbors[neighbor] = NeighborInfo()
        ref = self.neighbors[neighbor]
        if ref:
            #print("update_cache", neighbor, ref)
            if last_sent != None:
                ref.last_sent = last_sent
            if last_ack != None:
                ref.last_ack = last_ack
            if last_received != None:
                ref.last_received = last_received
            if len(neighbors_of_neighbors) > 0:
                curr_len = len(ref.neighbors)
                ref.neighbors.extend([tuple(n) for n in neighbors_of_neighbors])
                ref.neighbors = ref.neighbors[curr_len:]

    def get_query_id(self, query=""):
        id = random.randint(0,10000)
        while id in self.query_ids:
            id = random.randint(0,10000)
        self.query_ids[id] = QueryInfo(query)
        return id

    def get_src_addr(self):
        return (self.ip, self.tcp_port, self.udp_port)


class CacheConstants(Enum):
    EMPTY = 0
    OKAY = 1
    WARNING = 2

class TimeManager:
    def get_formatted_time_from_epoch(timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%m-%d-%Y %H:%M:%S')

    def get_time():
        return time.time()

    def get_formatted_time():
        return datetime.datetime.fromtimestamp(TimeManager.get_time()).strftime('%m-%d-%Y %H:%M:%S')


    #time2 - time1
    def get_time_diff_in_seconds(time1, time2):
        #print(time1, time2)
        if not (time1 and time2):
            return 0
        formatted_time1 = [int(x) for x in re.split("[-: ]", time1)]
        formatted_time2 = [int(x) for x in re.split("[-: ]", time2)]
        seconds = 0
        #don't really have to worry about months...
        #days
        seconds += abs(formatted_time2[1] - formatted_time1[1]) * 24 * 60 * 60
        #dont really have to worry about years...
        #hours
        seconds += abs(formatted_time2[3] - formatted_time1[3]) * 60 * 60
        #minutes
        seconds += abs(formatted_time2[4] - formatted_time1[4]) * 60
        #seconds
        seconds += abs(formatted_time2[5] - formatted_time1[5])
        return seconds
