#!/usr/bin/env python3

# ------------------------------------------------------------------------------
# Some generally useless tools useful for, but not specific to, the ALCT Test
# Software
# ------------------------------------------------------------------------------

import time
import datetime
import sys
import os

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

# Clears console screen of text
def ClearScreen(): 
    if os.name == 'posix': 
        os.system('clear')
    elif os.name == 'nt': 
        os.system('cls')

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

def BitToHexLen(size):
    result = ((size - 1) // 4) + 1
    return(result)

def BitToByteLen(size):
    result = ((size - 1) // 8)+1;
    return(result)

def RevHexDigit(digit):
    FlipHalfByte(digit)

def FlipByte(value): 
    result = 0;
    for i in range(8): 
        result = result | (((value >> i) & 0x1) << (7-i))
    return(result)

def FlipHalfByte(value):
    result = 0
    for i in range(4): 
        result = result | (((value  >> i) & 0x1) << (3-i))
    return(result)

def FlipWord(word):
    result = 0
    for i in range(16): 
        result = result | (((word >> i) & 0x1) << (15-i));
    return(result)

def FlipLongword(longword):
    result = 0
    for i in range(32): 
        result = result | (((word >> i) & 0x1) << (31-i));
    return(result)

def FlipDR(data,length):
    result=0
    for i in range(1,length):
        result = result | (((data >> i) & 0x1) << (10-i))
    return(result)
