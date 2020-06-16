from enum import Enum
import time
import re
import datetime
from Constants import *

class NeighborInfo():
    def __init__(self):
        self.neighbors = []
        self.last_sent = None
        self.last_ack = None
        self.last_received = None
        #maybe tcp/udp specific?

class NetworkClientCache():
    def __init__(self, query_size=100, size=10):
        self.query_ids = {}
        self.neighbors = {}
        self.extended_neighbors = {}
        self.ip = None
        self.tcp_port = None
        self.udp_port = None

    def update_cache(self, neighbor, neighbors_of_neighbors=[], last_sent=None, last_ack=None, last_received=None):
        if neighbor not in self.neighbors:
            self.neighbors[neighbor] = NeighborInfo()
        ref = self.neighbors[neighbor]
        if last_sent != None:
            ref.last_sent = last_sent
        if last_ack != None:
            ref.last_ack = last_ack
        if last_received != None:
            ref.last_received = last_received
        if len(neighbors_of_neighbors) > 0:
            for n in neighbors_of_neighbors:
                if n not in ref.neighbors:
                    ref.neighbors.append(n)


class CacheConstants(Enum):
    EMPTY = 0

class TimeManager:
    def get_formatted_time_from_epoch(timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%m-%d-%Y %H:%M:%S')

    def get_formatted_time():
        return datetime.datetime.fromtimestamp(get_time()).strftime('%m-%d-%Y %H:%M:%S')

    def get_time():
        return time.time()

    #time2 - time1
    def get_time_diff_in_seconds(time1, time2):
        formatted_time1 = re.split("[-: ]", time1)
        formatted_time2 = re.split("[-: ]", time2)
        seconds = 0
        #don't really have to worry about months...
        #days
        seconds += formatted_time2[1] - formatted_time1[1] * 24 * 60 * 60
        #dont really have to worry about years...
        #hours
        seconds += formatted_time2[3] - formatted_time1[3] * 60 * 60
        #minutes
        seconds += formatted_time2[4] - formatted_time1[4] * 60
        #seconds
        seconds += formatted_time2[5] - formatted_time1[5]
        return seconds
