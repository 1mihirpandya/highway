import time
import threading
import socket
import sys

class HighwayContinuousThread(threading.Thread):
    def __init__(self, wait_time, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.wait_time = wait_time

    def run(self):
        while True:
            try:
                while True:
                    self.func(*self.args, **self.kwargs)
                    time.sleep(self.wait_time)
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                pass

def continuous_thread(wait_time=None):
    def thread_f(func):
        def wrap_thread(*args, **kwargs):
            t = HighwayContinuousThread(wait_time, func, *args, **kwargs)
            t.daemon = True
            t.start()
            return t
        return wrap_thread
    return thread_f

class HighwayListenerThread(threading.Thread):
    def __init__(self, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        #self.ip = ip

    def run(self):
        #while True:
        try:
            self.func(*self.args, **self.kwargs)
        except KeyboardInterrupt:
            sys.exit(1)

def listener_thread(func):
    def wrap_thread(*args, **kwargs):
        t = HighwayListenerThread(func, *args, **kwargs)
        t.daemon = True
        t.start()
        return t
    return wrap_thread

def listener(func):
    def wrapper(*args, **kwargs):
        while True:
            try:
                while True:
                    func(*args, **kwargs)
            except KeyboardInterrupt:
                sys.exit(1)
            except:
                pass
    return wrapper

class HighwayThread(threading.Thread):
    def __init__(self, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.func(*self.args, **self.kwargs)
        except:
            return None

def thread(func):
    def wrap_thread(*args, **kwargs):
        t = HighwayThread(func, *args, **kwargs)
        t.daemon = True
        t.start()
        return t
    return wrap_thread

def thread_safe(func):
    def wrap(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
            return res
        except:
            return None
    return wrap
