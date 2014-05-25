################################################################################
# common.py Some general tools useful for the ALCT Test Software
################################################################################

import time
import datetime
import sys

# Print things to stdout on one line dynamically
class Printer():
    def __init__(self,data):
        sys.stdout.write("\r"+data.__str__())
        sys.stdout.flush()

# Gives Current Time  (e.g. 12:32:21)
def Now():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%H:%M:%S')
    return(st)

# Gives Current Day (e.g. 2013-02-12)
def Day():
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
    return(st)

# class to mimic the Pascal record type 
# probably better to reimplement as a normal dictionary...
# Can write to the tuple with tuple.entry=1234
# Can read from the typle with tuple.entry
# No need to prefedefine, no safety, be careful 
from collections import OrderedDict
class MutableNamedTuple(OrderedDict):
    def __init__(self, *args, **kwargs):
        super(MutableNamedTuple, self).__init__(*args, **kwargs)
        self._initialized = True

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        if hasattr(self, '_initialized'):
            super(MutableNamedTuple, self).__setitem__(name, value)
        else:
            super(MutableNamedTuple, self).__setattr__(name, value)
