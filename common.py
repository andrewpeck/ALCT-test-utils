import time
import datetime
import sys

#Print things to stdout on one line dynamically
class Printer():
    def __init__(self,data):
        sys.stdout.write("\r"+data.__str__())
        sys.stdout.flush()


def Now():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    return(st)

def Day():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    return(st)
