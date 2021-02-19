#!/usr/bin/env python

import subprocess
import pathlib
import os.path
import time
import sys

encryption = 'clear'


path = pathlib.Path().absolute().parent
ppath = os.path.join(path, "proxy")
apath = os.path.join(path, "analyst")
cpath = os.path.join(path, "client")
spath = os.path.join(path, "server")

#By Wissam Jarjoui https://goshippo.com/blog/measure-real-size-any-python-object/
def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size

def open_proxy():
    output_proxy = open('proxy_output.txt', 'wb')
    cmd = ['python.exe',ppath + "\Proxy3.py", encryption]
    proxy = subprocess.Popen(cmd, stdout = output_proxy, cwd = ppath)
    proxy.terminate()


def save_time_process():
    t = time.process_time()
    time.sleep(2)
    waited = time.process_time() - t
    print(waited)
    
def save_time_time():
    t = time.time()
    time.sleep(2)
    waited = time.time() - t
    print(waited)
    

def save_size():
    with open('size_test.txt','r') as f:
        text = f.read()
    print(get_size(text))

if __name__ == '__main__':
    #open_proxy()
    #save_time_process()
    #save_time_time()
    save_size()