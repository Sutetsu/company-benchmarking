#Proxy
import base64
import sys
import json
import sqlite3
from flask import Flask, json, request, abort
import os
import os.path
import numpy as np
from phe import paillier
from seal import *
from pyope.ope import OPE
import math
import random
from time import sleep
import pathlib
import time
import argparse

sys.path.append('../eval')
import pythoneval
pythoneval.enable_measurements(False)

IP_PROXY = '127.0.0.1'
IP_SERVER = '127.0.0.1'
PORT_PROXY = 5005
PORT_SERVER = 5006

#algorithmUrl = 'http://localhost:5000/algorithm'

#Password the analyst uses to identify themselves
analyst_pwd = 15

#Password the server uses to identify themselves
server_pwd = 6

#Default algorithm lookup table
alg_lookup = []

#Dict of all the functions that are still to do for each client. Keys are client IDs
client_todo_dict = {}

#Default list of symbols which are doable internally
internal_symbols = ['+','-','*','=']

#Scale for FHE
scale = pow(2.0, 40)

api = Flask(__name__)

def encode_list(input_list):
    output_list = []
    for entry in input_list:
        if type(entry) == bytes:
            temp = base64.b64encode(entry).decode()
            output_list.append(temp)
        elif type(entry) == list:
            temp = encode_list(entry)
            output_list.append(temp)
        elif type(entry) == str:
            output_list.append('#'+entry)
        else:
            output_list.append(entry)

    return output_list

def decode_list(input_list):
    output_list = []
    for entry in input_list:
        if type(entry) == str:
            if entry == '-':
                output_list.append(entry)
                continue
            elif entry.startswith('#'):
                output_list.append(entry[1:])
                continue
            try:
                temp = base64.b64decode(entry.encode())
            except:
                temp = entry
            output_list.append(temp)
        elif type(entry) == list:
            temp = decode_list(entry)
            output_list.append(temp)
        else:
            output_list.append(entry)

    return output_list

def encode_dict(msg):
    msg_base = {}
    for key in msg:
        if type(msg[key]) == bytes:
            msg_base[key] = base64.b64encode(msg[key]).decode()
        elif type(msg[key]) == dict:
            msg_base[key] = encode_dict(msg[key])
        elif type(msg[key]) == list:
            msg_base[key] = encode_list(msg[key])
        elif type(msg[key]) == str:
            msg_base[key] = '#' + msg[key]
        else:
            msg_base[key] = msg[key]
    return msg_base

def decode_dict(msg_base):
    data = {}
    for key in msg_base:
        if type(msg_base[key]) == str:
            if msg_base[key].startswith('#'):
                data[key] = msg_base[key][1:]
                continue
            try:
                data[key] = base64.b64decode(msg_base[key].encode())
            except:
                data[key] = msg_base[key]
        elif type(msg_base[key]) == dict:
            data[key] = decode_dict(msg_base[key])
        elif type(msg_base[key]) == list:
            data[key] = decode_list(msg_base[key])
        else:
            data[key] = msg_base[key]
    return data

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

@api.route('/write', methods=['POST'])
def writesth():
    data = json.loads(request.get_data())
    f = open('/home/alex/2020-ba-siuda-code/stataggregation.txt', 'a')
    f.write(str(data.get('phase')))
    f.write(str(data.get('time')))
    f.write('\n')
    f.close()
    msg = {'ok': 'ok'}
    msg_base = encode_dict(msg)
    return msg_base

@api.route('/getalgorithm', methods=['GET'])
def returnalgorithm():
    conn = sqlite3.connect('main.db')
    m = conn.cursor()

    lookup_list = []
    search = 'SELECT * FROM algorithm'
    m.execute(search)
    lookup_list.extend(m.fetchall())
    print(lookup_list)
    return {'alg':lookup_list}


#Description
@api.route('/', methods=['GET'])
def descriptor():
    return 'Proxy for a benchmarking platform'

#For analyst to update algorithm
@api.route('/algorithm', methods=['GET', 'POST', 'PATCH'])
@pythoneval.duration_function('algorithm')
def algorithm():
    if latency:
        sleep(download)
    if request.method == 'POST':
        print('Received Algorithm Post')
        data = json.loads(request.get_data())
        if log:
            f = open(os.path.join('log','Analyst-download.txt'), 'a')
            f.write(json.dumps(get_size(data)))
            f.write('\n')
            f.close()
        key = data.get('key')
        alg = data.get('alg')
        kpi = data.get('kpi')
        if key is None or key is not analyst_pwd:
            print('Wrong password:', key)
            abort(400) #Wrong key
        if alg is None:
            print('No algorithm')
            abort(400) #Missing argument
        if kpi is None:
            print('No kpi list')
            abort(400) #Missing argument
        process_algorithm(alg, kpi)

        if latency:
            sleep(upload)        
        if log:
            f = open(os.path.join('log','Analyst-upload.txt'), 'a')
            f.write(json.dumps(get_size({'result': 'ack'})))
            f.write('\n')
            f.close()
        return json.dumps({'result': 'ack'})
    else:
        return json.dumps('TODO')


#Returns type of encryption
@api.route('/encryption', methods=['GET'])
def enc_type():
        print('TODO implement telling client which encryption')
        return encryption


#First contact from a client
#TODO check if Analyst posted beforehand
@api.route('/initial', methods=['POST', 'GET'])
@pythoneval.duration_function('setup')
def initial():

    if latency:
        sleep(download)
        
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' Initial Start')
        times.write('\n')
    if request.method == 'POST':
        print('Received Initial Contact')

        #Check if we already have the keys from the server
        if not encryption == 'clear':
            try:
                test = ope_key
            except:
                print('Did not get a connection from Server yet')
                print('Aborting')
                abort(400)

        msg_base = json.loads(request.get_data())
        data = decode_dict(msg_base)
        if log:
            f = open(os.path.join('log','Client-download.txt'), 'a')
            f.write(json.dumps(get_size(msg_base)))
            f.write('\n')
            f.close()

        #Check if we will get a public key
        #For fhe, we will use the relin keys instead, since calculations are done over context
        print('Getting public key')
        client_pub_key = data.get('key')
        #print('Key:', client_pub_key)

        #Generate a client ID and add the client to the main database
        client_id = generate_id()
        if encryption == 'fhe':
            relin_keys = data.get('relin')
            add_client_fhe(client_id, client_pub_key, relin_keys)
        else:
            add_client(client_id, client_pub_key)
            
        create_obfus_db(client_id)
            

        #Add a default todo list into the dict for the new client
        client_todo_dict[client_id] = alg_lookup
        #print(client_todo_dict)
        #print(alg_lookup)
        if encryption == 'fhe':

            msg = {'id': client_id, 'ope': ope_key, 'he': he_key}
        else:
            msg = {'id': client_id}

        msg_base = encode_dict(msg)
        msg = json.dumps(msg_base)
        

        if log:
            f = open(os.path.join('log','Client-upload.txt'), 'a')
            f.write(json.dumps(get_size(msg)))
            f.write('\n')
            f.close()
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' Initial End')
            times.write('\n')
        
        if latency:
            sleep(upload)
            
        return msg
    else:
        return json.dumps('TODO')

#For a client to add values. Returns a list of functions to calculate next
@api.route('/values', methods=['POST'])
@pythoneval.duration_function('computation')
def new_values():

    if latency:
        sleep(download)
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' NewVals Start')
        times.write('\n')
    
    if request.method == 'POST':
        print('Received new values')

        msg_base = json.loads(request.get_data())
        data = decode_dict(msg_base)
        if log:
            f = open(os.path.join('log','Client-download.txt'), 'a')
            f.write(json.dumps(get_size(msg_base)))
            f.write('\n')
            f.close()

        client_id = data.get('id')
        client_vals = data.get('values')
        print('Received values from Client ' + str(client_id) + ' for the following kpis:')
        print(client_vals.keys())

        computation_local = pythoneval.duration_start('computation_local', considerOverall=False)

        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' LoadKeys Start')
            times.write('\n')
        if encryption == 'fhe':
            print('Loading relinearization keys')
            global relin_keys, client_pub_key
            pub_key_str,rel_key_str = get_key_fhe(client_id)
            f = open('relin','wb')
            f.write(rel_key_str)
            f.close()
            f = open('pub','wb')
            f.write(pub_key_str)
            f.close()
            #Load from file using SEAL method and context
            #Relin keys
            relin_keys = RelinKeys()
            relin_keys.load(context,'relin')
            #Pub key
            client_pub_key = PublicKey()
            client_pub_key.load(context,'pub')
            global encryptor
            encryptor = Encryptor(context, client_pub_key)
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' LoadKeys End')
            times.write('\n')
            
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' DeObfuscate Start')
            times.write('\n')
        #Removing obfuscation
        client_vals = deobfuscate(client_id, client_vals)
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' DeObfuscate End')
            times.write('\n')

        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' AddVals Start')
            times.write('\n')
        print('Adding values')
        add_values(client_id, client_vals)
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' AddVals End')
            times.write('\n')

        todos = check_todos(client_id)

        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' InternalCalcs Start')
            times.write('\n')
        #Calculate all possible functions internally
        internals = get_internals(todos)
        while internals:
            print('-'*50)
            #Does internal calculations and adds them for the client
            calculate_internal(client_id, internals)
            #Rechecks for doable todos
            todos = check_todos(client_id)
            #print(todos)
            internals = get_internals(todos)
            #print(internals)
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' InternalCalcs End')
            times.write('\n')

        pythoneval.duration_stop(computation_local)

        #Check if we are done with all todos
        if not todos:
            print('-'*50)
            print('Completed all todos')
            #printTable('client','ID'+client_id)
            print('Number of Tables:', count_clients())
            #Get a dict of kpis and corresponding values
            kpis = get_kpis(client_id)

            msg = {'done': 1, 'kpi': kpis}
            msg_base = encode_dict(msg)
            if log:
                f = open(os.path.join('log','Client-upload.txt'), 'a')
                f.write(json.dumps(get_size(msg_base)))
                f.write('\n')
                f.close()
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' NewVals End')
                times.write('\n')
            
            if latency:
                sleep(upload)
                
            return msg_base

        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' Obfuscate Start')
            times.write('\n')
        #Obfuscating
        todos = obfuscate(client_id, todos)
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' Obfuscate End')
            times.write('\n')

        #Setting ciphertexts to level 0 to save space
        if encryption == 'fhe' and set_zero:
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' LevelZero Start')
                times.write('\n')
            todos = delevel(todos)
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' LevelZero End')
                times.write('\n')

        msg = {'todo': todos}
        msg_base = encode_dict(msg)

        if log:
            f = open(os.path.join('log','Client-upload.txt'), 'a')
            f.write(json.dumps(get_size(msg_base)))
            f.write('\n')
            f.close()
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' NewVals End')
            times.write('\n')
        
        if latency:
            sleep(upload)
            
        return msg_base


#For client to hand of Server!encrypted KPIs and for server to get aggregated KPIs
@api.route('/kpi', methods=['POST', 'GET'])
@pythoneval.write_duration_after_function()
@pythoneval.duration_function('aggregation_client')
def kpi():
    if latency:
        sleep(download)
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' AddKPIs Start')
        times.write('\n')
    if request.method == 'POST':
        print('-'*100)
        print('Got KPI post')

        msg_base = json.loads(request.get_data())
        data = decode_dict(msg_base)
        if log:
            f = open(os.path.join('log','Server-download.txt'), 'a')
            f.write(json.dumps(get_size(msg_base)))
            f.write('\n')
            f.close()

        client_id = data.get('id')
        kpi = data.get('kpi')
        ope = data.get('ope')
        if client_id is None:
            print('No client id')
            abort(400) #Missing argument
        if kpi is None:
            print('No kpi list')
            abort(400) #Missing argument
        if ope is None:
            print('No ope list')
            abort(400) #Missing argument

        #Get new kpi into database
        add_kpi(client_id, kpi, ope)
        drop_client(client_id)

        if log:
            f = open(os.path.join('log','Server-upload.txt'), 'a')
            f.write(json.dumps(get_size({'result': 'ack'})))
            f.write('\n')
            f.close()
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' AddKPIs End')
            times.write('\n')
        
        if latency:
            sleep(upload)
            
        return json.dumps({'result': 'ack'})
    else:
        return json.dumps('Wrong method')

#For server to provide keys
@api.route('/key', methods=['GET', 'POST', 'PATCH'])
@pythoneval.duration_function('setup')
def key():
    if latency:
        sleep(download)
    
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' Keys Start')
        times.write('\n')
    
    if request.method == 'POST':
        print('Received server connection')

        msg = request.get_data()
        msg_base = json.loads(request.get_data())
        data = decode_dict(msg_base)
        if log:
            f = open(os.path.join('log','Server-download.txt'), 'a')
            f.write(json.dumps(get_size(msg_base)))
            f.write('\n')
            f.close()

        pwd = data.get('pwd')
        ope = data.get('ope')
        he = data.get('he')
        if pwd is None or pwd is not server_pwd:
            print('Wrong password:', key)
            abort(400) #Wrong key
        if ope is None:
            print('No ope key')
            abort(400) #Missing argument
        if he is None:
            print('No homomorphic key')
            abort(400) #Missing argument
        save_keys(ope, he)
        print('Saved public keys')
        
        if log:
            f = open(os.path.join('log','Server-upload.txt'), 'a')
            f.write(json.dumps(get_size({'result': 'ack'})))
            f.write('\n')
            f.close()
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' Keys End')
            times.write('\n')
        
        if latency:
            sleep(download)
        
        return json.dumps({'result': 'ack'})
    else:
        return json.dumps('TODO')


#For server to retrieve aggregated values
@api.route('/statistics', methods=['GET'])
@pythoneval.write_duration_after_function()
@pythoneval.duration_function('aggregation_all')
def statistics():
    if latency:
        sleep(download)
    if log:  
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' Statistics Start')
        times.write('\n')
    
    #if count_clients() > 3: TODO    if latency:
    agg, ope_max, ope_min = aggregate()

    #Turn ciphertext into pickleable string
    agg_string = {}
    for eid in agg:
        #print('To string for eid ' + eid)
        agg_string[eid] = fhe_to_string(agg[eid])

    #print(agg_string)
    print(ope_max)
    print(ope_min)
    print('Number of clients', count_clients())

    msg = {'mean': agg_string, 'max': ope_max, 'min': ope_min, 'count': count_clients()}
    msg_base = encode_dict(msg)

    if log:
        f = open(os.path.join('log','Server-upload.txt'), 'a')
        f.write(json.dumps(get_size(msg_base)))
        f.write('\n')
        f.close()
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' Statistics End')
        times.write('\n')
        
    if latency:
        sleep(upload)
        
    return msg_base


#For server to retrieve aggregated values
@api.route('/statistics-avg', methods=['GET'])
@pythoneval.write_duration_after_function()
@pythoneval.duration_function('aggregation_avg')
def statistics_avg():
    if latency:
        sleep(download)
    #if count_clients() > 3: TODO
    agg = aggregate_avg()

    #Turn ciphertext into pickleable string
    agg_string = {}
    for eid in agg:
        #print('To string for eid ' + eid)
        agg_string[eid] = fhe_to_string(agg[eid])

    #print(agg_string)
    print('Number of clients', count_clients())

    msg = {'mean': agg_string, 'count': count_clients()}
    msg_base = encode_dict(msg)

    if latency:
        sleep(upload)
    if log:
        f = open(os.path.join('log','Server-upload.txt'), 'a')
        f.write(json.dumps(get_size(msg_base)))
        f.write('\n')
        f.close()
    return msg_base


# Explicitly write pythoneval results to disk
@api.route('/write-results', methods=['GET'])
def write_results():
    pythoneval.write_duration()
    pythoneval.write_traffic()
    return {}

#Given a list of functions, sets all contained ciphertexts to level 0
#List example [['aa102', '/', 3.0, 2.0], ['bb100', 'Min', 5.0, 6.0, 7.0], ['dd100', 'Abs', -3.0], ['ee100', 'Wurzel', 9.0], ['gg100', '^', 2.0, 2.0]]
def delevel(todo_list):
    print('Reducing levels')
    new_todo = []
    for func in todo_list:
        newfunc = func[:2]
        for arg in func[2:]:
            string_val = fhe_from_string(arg)
            if isinstance(string_val, Ciphertext):
                arg = level_zero(string_val)
                arg = fhe_to_string(arg)
            newfunc.append(arg)
        new_todo.append(newfunc)
    return new_todo
    
#Sets the level of a given ciphertext to the lowest possible
def level_zero(val):
    #print('-'*20)
    while magnitude(val.scale()) > 40 and parm_levels[val.parms_id()[0]] < len(parm_levels)-1:
       evaluator.rescale_to_next_inplace(val)
       #print('Lowered level')
    #try:
    #while val.parms_id() != lowest_parms_id:
    #    #evaluator.rescale_to_next_inplace(val)
    #    evaluator.mod_switch_drop_to_next(val, val)
    #    print('Lowered level')
    #except:
    #    print('Could not lower level')
    #try:
    #    evaluator.mod_switch_to_inplace(x_encrypted, context.last_parms_id())
    #except:
    #    print('Could not lower level')
    return val
    
def lowest_parms(context):
    context_data = context.first_context_data()
    global lowest_parms_id
    while(context_data):
        lowest_parms_id = context_data.parms_id()
        context_data = context_data.next_context_data()
    

#For a given client ID and obfuscated value dict we return the deobfuscated value dict
def deobfuscate(client_id, vals):
    print('Deobfuscating')
    deob_vals = {}
    
    #Remove dummies from dict
    tmp = dict(vals)
    for key in vals:
        if dummies:
            if is_dummy(client_id, key):
                tmp.pop(key, None)
    vals = tmp

    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' DeRandomizeBlind Start')
        times.write('\n')
    #Remove randomization and blinds
    for key in vals:            
        if randomization:
            eid = derandomize(client_id, key)
        else:
            eid = key
            
        if blinding:
            #print(client_id, key, vals)
            val = unblind(client_id, eid, vals[key])
        else:
            val = vals[key]
                
        deob_vals[eid] = val
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' DeRandomizeBlind End')
        times.write('\n')
    return deob_vals

#For a given client ID and func list we return an obuscated value list
#Vals example [['aa102', '/', 3.0, 2.0], ['bb100', 'Min', 5.0, 6.0, 7.0], ['dd100', 'Abs', -3.0], ['ee100', 'Wurzel', 9.0], ['gg100', '^', 2.0, 2.0]]
def obfuscate(client_id, vals):
    print('Obfuscating')
    ob_vals = []
    for func in vals:
        #print('-'*50)
        #print('Obfuscating EID', func[0])
        if blinding:
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' Blind Start')
                times.write('\n')
            func = blind(client_id, func)
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' Blind End')
                times.write('\n')
        if randomization:
            func[0] = randomize(client_id, func[0])
      
        ob_vals.append(func)
    
    if dummies:
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' Dummies Start')
            times.write('\n')
        dums = create_dummies(client_id)
        #Dummies are always at the end, but that does not affect our testing
        ob_vals = ob_vals + dums
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' Dummies End')
            times.write('\n')
    
    return ob_vals

#Blind a function
def blind(client_id, func):
    
    #Symbols which can be blinded with just *c multiplication
    mult = ['/','Abs','Min','Max']
    
    new_func = func[:2]
    c = random.uniform(blind_lower,blind_upper)
    
    #print('Blinding', func[0], 'with blind', c)
    
    conn = sqlite3.connect('obfus.db')
    o = conn.cursor()
    
    
    if encryption == 'fhe':
        #'Easy' to blind
        if func[1] in mult:
            if not func[1] == '/': #Division stays the same, so we don't need an entry here
                exe = 'INSERT INTO ID'+ client_id +' (EID, symbol, blind) VALUES (?,?,?)'
                o.execute(exe, (func[0], func[1], c))
            for val in func[2:]:
                #Turn string into encrypted number, blind, and back into string for saving
                val = functions_fhe('*', [fhe_from_string(val), c])
                val = fhe_to_string(val)
                new_func.append(val)
        #'Harder' to blind
        else:
            print('TODO')
            return func 

    else:
        #'Easy' to blind
        if func[1] in mult:
            if not func[1] == '/': #Division stays the same, so we don't need an entry here
                exe = 'INSERT OR IGNORE INTO ID'+ client_id +' (EID, symbol, blind) VALUES (?,?,?)'
                o.execute(exe, (func[0], func[1], c))
            for val in func[2:]:
                new_func.append(val*c)
        #'Harder' to blind
        else:
            #print('TODO')
            return func    

    conn.commit()
    o.close()
    conn.close()
    
    return new_func
    
def unblind(client_id, eid, val):

    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' UnBlind Start')
        times.write('\n')

    #Get the blind and symbol used for the eid, then delete the entry
    conn = sqlite3.connect('obfus.db')
    o = conn.cursor()
    exe = 'SELECT blind FROM ID'+client_id+' WHERE EID = (?)'
    o.execute(exe, (eid,))
    blind = o.fetchall()
    
    exe = 'SELECT symbol FROM ID'+client_id+' WHERE EID = (?)'
    o.execute(exe, (eid,))
    symbol = o.fetchall()
    
    exe = 'DELETE FROM ID'+client_id+' WHERE EID = (?)'
    o.execute(exe, (eid,))
    o.close()
    conn.close()
    
    #print('EID', eid, 'blind', blind, 'symbol', symbol)
    
    if blind:
        if blind[0][0] != None:
            if encryption == 'fhe':
                #Turn string into encrypted number, remove blind, and back into string for saving
                val = functions_fhe('*', [fhe_from_string(val), 1/blind[0][0]])
                val = fhe_to_string(val)
            else:
                val = val/blind[0][0]
              
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' UnBlind End')
        times.write('\n')
    
    return val
    
#Randomize EID names
#TODO ensure no fid is double
def randomize(client_id, eid):
    #print('Randomizing')
    letters = 'abcdefghijklmnopqrstuvwxyz'
    numbers = '123456780'
    
    fid = ''
    
    fid = fid + random.choice(letters)
    fid = fid + random.choice(letters)
    fid = fid + random.choice(letters)
    fid = fid + random.choice(numbers)
    fid = fid + random.choice(numbers)
    fid = fid + random.choice(numbers)
    fid = fid + random.choice(numbers)
    
    #print('Adding ' + eid + ' as false id ' + fid)
    
    conn = sqlite3.connect('obfus.db')
    o = conn.cursor()
    
    exe = 'INSERT OR IGNORE INTO ID'+ client_id +' (EID, fid) VALUES (?,?)'
    o.execute(exe, (eid, fid))
    exe = 'UPDATE ID'+ client_id +' SET fid = (?) WHERE eid = (?)'
    o.execute(exe, (fid, eid))
    
    conn.commit()
    o.close()
    conn.close()
    return fid
   
#Derandomize for given false id and client id   
def derandomize(client_id, fid):
    #print('Derandomizing')
    #print('False ID', fid)
    ret = fid
    
    conn = sqlite3.connect('obfus.db')
    o = conn.cursor()
    
    exe = 'SELECT EID FROM ID'+client_id+' WHERE fid = (?)'
    o.execute(exe, (fid,))
    eid = o.fetchall()
    
    o.close()
    conn.close()
    
    if eid:
        ret = eid[0][0]
    return ret
    
#Create a list of dummy functions
def create_dummies(client_id):
    """
    Dummy types   dummy_type
    'Fixed'
    dummy_number = 3
    """
    print('Creating dummies')
    dummies = []
    if dummy_scheme == 'fixed':
        for i in range(dummy_number):
            dummies.append(dummy(client_id))
    elif dummy_scheme == 'random':
        dummy_number = random.randint(dummy_lower, dummy_upper)
        for i in range(dummy_number):
            dummies.append(dummy(client_id))
    else:
        print('TODO: No other dummy schemes yet')
    #print(dummies)
    return dummies

#Checks if a given eid is a dummy
def is_dummy(client_id, eid):
    conn = sqlite3.connect('obfus.db')
    o = conn.cursor()
    
    exe = 'SELECT EID FROM ID'+client_id+' WHERE dummy = (?)'
    o.execute(exe, (True,))
    tmp = o.fetchall()
    
    try:
        boo = [eid[0] for eid in tmp]
    except:
        boo = []
        
    #print(boo)
    if eid in boo:
        exe = 'DELETE FROM ID'+client_id+' WHERE EID = (?)'
        o.execute(exe, (eid,))
        conn.commit()
        o.close()
        conn.close()
        print(eid, 'is dummy')
        return True
    conn.commit()
    o.close()
    conn.close()
    #print(eid, 'is not dummy')
    return False

def dummy(client_id):
    letters = 'abcdefghijklmnopqrstuvwxyz'
    numbers = '123456780'
    symbols = ['Abs','Wurzel','Min','Max','/','^']
    
    sym = random.choice(symbols)
    eid = ''
    eid = eid + random.choice(letters)
    eid = eid + random.choice(letters)
    eid = eid + random.choice(letters)
    eid = eid + random.choice(numbers)
    eid = eid + random.choice(numbers)
    eid = eid + random.choice(numbers)
    eid = eid + random.choice(numbers)
    
    dum = [eid, sym]
    print('Dummy:', dum)
    #One arg
    if sym == 'Abs' or sym == 'Wurzel':
        arg = dummy_arg(sym)
        dum.append(arg)
    #Two args
    elif sym == '/' or sym == '^':
        arg = dummy_arg(sym)
        dum.append(arg)
        arg = dummy_arg(sym)
        dum.append(arg)
    #Random number of args
    else:
        num = random.randint(dummy_mult_start, dummy_mult_end)
        for i in range(num):
            arg = dummy_arg(sym)
            dum.append(arg)
            
    #Put dummy into db
    conn = sqlite3.connect('obfus.db')
    o = conn.cursor()
    
    exe = 'INSERT OR IGNORE INTO ID'+ client_id +' (EID, dummy) VALUES (?,?)'
    o.execute(exe, (eid, True))
    
    conn.commit()
    o.close()
    conn.close()
    return dum

#Create a dummy argument, in encrypted string form for fhe
def dummy_arg(sym):
    ran = random.uniform(dummy_arg_start,dummy_arg_end)
    #Make sure we don't get the root of a negative and too high exponents
    if sym == 'Wurzel':
        ran = abs(ran)
    if sym == '^':
        ran = random.uniform(1,20)
    
    if encryption == 'fhe':
        v_plain = Plaintext()
        encoder.encode(ran, scale, v_plain)
        #Encrypt
        v_encrypted = Ciphertext()
        encryptor.encrypt(v_plain, v_encrypted)
        #Save to file
        v_encrypted.save('v_save')
        #Read as binary string
        f = open('v_save', 'rb')
        string_val = f.read()
        f.close()
        ran = string_val
    
    return ran




def create_obfus_db(cid):
    print('Creating obfuscation db for client', cid)
    conn = sqlite3.connect('obfus.db')
    o = conn.cursor()
    o.execute('CREATE TABLE IF NOT EXISTS ID'+ cid +' (EID string PRIMARY KEY, FID string UNIQUE, symbol string, blind real, dummy bool)')
    o.close()
    conn.close()

def save_keys(ope, he):
    global ope_key, cipher, he_key
    ope_key = ope
    cipher = OPE(ope_key)
    he_key = he

#For a list of todos returns a list of todos doable internally
def get_internals(todos):
    internal_todos = []
    for func in todos:
        if func[1] in internal_symbols:
            internal_todos.append(func)
    #print('Internal todos:', internal_todos)
    return internal_todos


def get_key_fhe(cid):
    #print('X'*100)
    #printTable('main', 'clients')
    #Get the client's public key
    conn = sqlite3.connect('main.db')
    m = conn.cursor()
    #table clients (CID string PRIMARY KEY, pub_key blob, pwd string, done boolean)')
    #print(cid)
    ex = "SELECT pub_key FROM clients WHERE CID = "+ str(cid)
    m.execute(ex)
    key = m.fetchall()[0][0]
    m.close()
    conn.close()

    
    conn = sqlite3.connect('main.db')
    m = conn.cursor()
    #table clients (CID string PRIMARY KEY, pub_key blob, pwd string, done boolean)')
    #print(cid)
    ex = "SELECT relin_keys FROM clients WHERE CID = "+ str(cid)
    m.execute(ex)
    relin = m.fetchall()[0][0]
    m.close()
    conn.close()
    
    return key, relin

#Calculates functions internally and adds them to the client
def calculate_internal(c_id, todos):
    print('Internals')
    vals = {}
    #relin_keys = get_key(c_id)
    #Cleartext
    if encryption == 'clear':
        for func in todos:
            #print(func)
            val = functions_clear(func[1], func[2:])
            #Add to output dict
            vals[func[0]] = val
    #Fully homomorphic
    elif encryption == 'fhe':
        for func in todos:
            #print('Function', func)
            print('Calculating', func[0], 'internally')
            val = functions_fhe(func[1], func[2:])
            #Add to output dict
            vals[func[0]] = val
    #Partially homomorphic
    elif encryption == 'phe':
        key = get_key(c_id)
        for func in todos:
            #print(func)
            val = functions_phe(func[1], func[2:], c_id, key)
            #Add to output dict
            vals[func[0]] = val
    else:
        print('Something went wrong while trying to calculate internally')
        print('Encryption type is probably wrong')
    #print('Adding for id:', c_id, vals)
    add_values(c_id, vals)

def functions_clear(symbol, args):
    #print('Functions clear')
    #print(symbol, args)
    #Addition
    if symbol == '+':
        return sum(args)
    #Subtraction
    if symbol == '-':
        res = args[0]
        for arg in args[1:]:
            res -= arg
        return res
    #Multiplication
    if symbol == '*':
        res = 1
        for arg in args:
            res = res * arg
        return res
    #Division
    if symbol == '/':
        return (args[0]/args[1])
    #Root
    if symbol == 'Root':
        return math.sqrt(args[0])
    #Minimum
    if symbol == 'Min':
        return min(args)
    #Maximum
    if symbol == 'Max':
        return max(args)
    #Absolute
    if symbol == 'Abs':
        return abs(args[0])
    #Redirect
    if symbol == '=':
        return args[0]


def functions_phe(symbol, args, cid, key):
    print('Functions phe')
    print('Using key', key)


def functions_fhe(symbol, args):
    #print('Functions fhe')
    #print('Using evaluator', evaluator)
    #print('Relin Keys:', relin_keys)

    """
    'add','add_inplace','add_many','add_plain','add_plain_inplace'
    'exponentiate', 'exponentiate_inplace'
    'multiply','multiply_inplace','multiply_many','multiply_plain','multiply_plain_inplace'
    'square', 'square_inplace'
    'sub', 'sub_inplace', 'sub_plain', 'sub_plain_inplace'
    """

    #Turn the saved strings back into Cipertexts
    args = [fhe_from_string(arg) for arg in args]

    #Quick and dirty catch for unencrypted-encrypted
    if len(args) > 1:
        #print('Two or more args')
        #print(type(args[0]),type(args[1]))
        if is_number(args[0]) and symbol == '-' and isinstance(args[1], Ciphertext):
            print('Encrypted substraction fix')
            #We should only have one encrypted and one unencrypted here
            subtrahend = Plaintext()
            encoder.encode(args[0], scale, subtrahend)
            args[1] = negate_fhe(args[1])
            args = rescale_mult([args[1], subtrahend])
            res = Ciphertext()
            print('Plaintext substraction')
            evaluator.add_plain(args[0], args[1], res)
            return res

    #Check where we have unencrypted numbers
    unenc = check_unencrypted(args)

    #If we have unencrypted numbers, calculate the function to ensure we have at most 1
    if any(unenc):
        #Split the list into unencrypted and encrypted
        #This also ensures we can put singular unencrypted numbers at the end
        une = []
        enc = []
        for arg in args:
            if is_number(arg):
                une.append(arg)
            else:
                enc.append(arg)
        if unenc.count(True) > 1:
            print('More than one unencrypted number')
            #Calculate the unencrypted numbers
            #Since we only have mult and add here, we can use the same symbol
            ret = functions_clear(symbol, une)
        else:
            ret = une[0]
        #Check if there were any encrypted numbers, then append. Otherwise the unenc are our result
        if enc:
            print('Appending unencrypted numbers')
            enc.append(ret)
            args = enc
        else:
            return ret



    if symbol == '=':
        return args[0]
    elif symbol == '+':
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' InternalAdd Start')
            times.write('\n')
        print('Encrypted addition')
        #We have an unencrypted number
        if any(unenc):
            #Unencrypted numbers are always singular at this point and in the last spot
            if len(args) > 2:
                #Rekursively do the encrypted numbers, then the unencrypted one
                print('Rekursive addition')
                ret = functions_fhe(symbol, args[1:])
            #We should only have one encrypted and one unencrypted here
            res = Ciphertext()
            plain = Plaintext()
            encoder.encode(args[1], scale, plain)
            args = rescale_mult([args[0], plain])
            prms = [arg.parms_id()[0] for arg in args]
            #print(prms)

            if isinstance(args[1], Plaintext):
                evaluator.add_plain(args[0], args[1], res)
            else:
                evaluator.add(args[0], args[1], res)
            
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' InternalAdd End')
                times.write('\n')
            
            return res
            
        #Multiple encrypted
        else:
            res = Ciphertext()
            if len(args) > 2:
                #Do it rekursively again
                print('Rekursive addition')
                rek = functions_fhe(symbol, args[1:])
                args = rescale_mult([args[0], rek])
                evaluator.add(args[0], args[1], res)
            else:
                args = rescale_mult(args)
                #for arg in args:
                #    print(arg.scale())
                #for arg in args:
                #    print(arg.parms_id())
                evaluator.add(args[0], args[1], res)
            
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' InternalAdd End')
                times.write('\n')
    
            return res

    elif symbol == '-':
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' InternalSub Start')
            times.write('\n')
        print('Encrypted substraction')
        #We have an unencrypted number
        if any(unenc):
            #Unencrypted numbers are always singular at this point and in the last spot
            if len(args) > 2:
                #Rekursively do the encrypted numbers, then the unencrypted one
                print('Rekursive substraction')
                subtrahend = negate_fhe(functions_fhe('+', args[1:]))
            else:
                #We should only have one encrypted and one unencrypted here
                subtrahend = Plaintext()
                tmp = args[1]*(-1)
                encoder.encode(tmp, scale, subtrahend)
            args = rescale_mult([args[0], subtrahend])
            res = Ciphertext()
            if isinstance(args[1], Plaintext):
                print('Plaintext substraction')
                evaluator.add_plain(args[0], args[1], res)
            else:
                evaluator.add(args[0], args[1], res)
            
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' InternalSub End')
                times.write('\n')
    
            return res
        #Multiple encrypted
        else:
            #Rescale and relinearize
            print('Multiple encrypted')
            args = rescale_mult(args)
            res = Ciphertext()
            minuend = args[0]
            subtrahend = [negate_fhe(arg) for arg in args[1:]]
            args = [minuend] + subtrahend
            #for arg in args:
            #    print(arg.scale())
            #for arg in args:
            #    print(arg.parms_id())
            evaluator.add_many(args, res)
            
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' InternalSub End')
                times.write('\n')
    
            return res

    elif symbol == '*':
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' InternalMult Start')
            times.write('\n')
        print('Encrypted multiplication')
        #We have an unencrypted number
        if any(unenc):
            print('Unencrypted number')
            #Unencrypted numbers are always singular at this point and in the laste spot
            if len(args) > 2:
                #Rekursively do the encrypted numbers, then the unencrypted one
                second = functions_fhe(symbol, args[1:])
            else:
                second = Plaintext()
                encoder.encode(args[1], scale, second)
            #Rescale and relinearize
            args = rescale_mult([args[0], second])
            res = Ciphertext()
            if isinstance(args[1], Plaintext):
                evaluator.multiply_plain(args[0],args[1], res)
            else:
                evaluator.multiply(args[0],second, res)
                
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' InternalMult End')
                times.write('\n')
    
            return res
        #Multiple encrypted
        else:
            res = Ciphertext()
            #Rescale and relinearize
            args = rescale_mult(args)
            #CKKS does not seem to support multiply_many
            #evaluator.multiply_many(args, relin_keys, res)
            if len(args) > 2:
                #Do it rekursively again
                print('Rekursive multiplication')
                rek = functions_fhe(symbol, args[1:])
                evaluator.multiply(args[0], rek, res)
            else:
                evaluator.multiply(args[0], args[1], res)
                
            if log:
                times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
                times.write(str(time.perf_counter_ns()) + ' InternalMult End')
                times.write('\n')

            return res

    #elif symbol == '^':
    #    x1 = args[0]
    #    x2 = args[1]
    #   evaluator.square(x1, x2)
    #    return x1
    else:
        print('TODO')

#Negates an encrypted number, since SEAL does not use any return functions
def negate_fhe(arg):
    evaluator.negate_inplace(arg)
    return arg



#Takes a list of encrypted numbers and rescales them all so multiplication can be run over them
def rescale_mult(args):

    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' Rescale Start')
        times.write('\n')

    print('Rescaling')
    mags, prms = ciph_stats(args)
    """
    for arg in args:
        print(arg.scale())
        print(arg.parms_id())
    """

    #First we rescale to make sure our scales don't exceed the bounds
    max_scale = len(parm_levels)*40 #TODO change this for the one from scale
    #print(mags, prms, max_scale)

    while sum(mags.values()) > max_scale:
        #Look for the value with the highest level/lowest prms
        index = min(prms, key=prms.get)
        evaluator.rescale_to_next_inplace(args[index])
        mags, prms = ciph_stats(args)

    #Make sure scales match
    index = min(prms, key=mags.get)
    lowest_mag = magnitude(args[index].scale())
    while not all(val == lowest_mag for val in mags.values()):
        for arg in args:
            if magnitude(arg.scale()) > lowest_mag:
                evaluator.rescale_to_next_inplace(arg)
                mags, prms = ciph_stats(args)
                #print(mags)
    """
    print('After rescale')
    for arg in args:
        print(arg.scale())
        print(arg.parms_id())
    """

    #Determine lowest parms level
    index = 0
    print('Parm levels', parm_levels)
    print('Current parms', prms)
    lowest = 0
    for i in range(len(prms)):
        if parm_levels[prms[i]] > lowest:
            index = i
            lowest = parm_levels[prms[i]]
    lowest_parms = args[index].parms_id()
    print('Lowest parms', lowest_parms)
    for arg in args:
        evaluator.mod_switch_to_inplace(arg, lowest_parms)

    """
    print('After parms')
    for arg in args:
        print(arg.scale())
        print(arg.parms_id())
    """
    for arg in args:
        if isinstance(arg, Ciphertext):
            evaluator.relinearize_inplace(arg, relin_keys)
            #Make sure the scales match
            arg.scale(pow(2.0, magnitude(arg.scale())))
    
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' Rescale End')
        times.write('\n')
    
    return args

#Takes a list of encrypted numbers and rescales them all so addition can be run over them
def rescale_add(args):

    mags, prms = ciph_stats(args)

    for arg in args:
        if isinstance(arg, Ciphertext):
            evaluator.relinearize_inplace(arg, relin_keys)
            #Make sure the scales match
            arg.scale(pow(2.0, 40))
    return args

#Returns dicts for parms and magnitudes for each argument
def ciph_stats(args):
    prms = {}
    mags = {}
    for i in range(len(args)):
        prms[i] = args[i].parms_id()[0]
        mags[i] = magnitude(args[i].scale())
    return mags, prms

#Creates a dict for the first element in each parm level
def get_parms():
    context_data = context.first_context_data()
    parms = {}
    i = 1
    while(context_data):
        parms[context_data.parms_id()[0]] = i
        i += 1
        context_data = context_data.next_context_data()
    return parms

def magnitude(x):
    return int(math.log2(x))


#Returns a list of booleans corresponding to a given list of arguments. True if an argument is unencrypted
def check_unencrypted(args):
    #print('Check unencrypted')
    unenc = []
    for arg in args:
        if is_number(arg):
            unenc.append(True)
        else:
            unenc.append(False)
    return unenc

#Aggregate the KPIs we have. Returns a dict of average values with EID as keys
def aggregate():
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' Aggregate Start')
        times.write('\n')
    print('Aggregate')

    #Get the EIDs for KPIs
    conn = sqlite3.connect('main.db')
    conn.row_factory = lambda cursor, row: row[0]
    m = conn.cursor()


    m.execute('SELECT EID FROM algorithm WHERE kpi = 1')
    kpi_list = m.fetchall()
    print(kpi_list)

    #Start aggregation
    global agg
    agg = {}

    ope_min = {}

    ope_max = {}

    for eid in kpi_list:
        search = 'SELECT value FROM kpi WHERE EID = (?)'
        print(search, eid)
        vals = m.execute(search, (eid,)).fetchall()


        #Average
        if encryption == 'clear':
            agg[eid] = np.mean(vals)
        elif encryption == 'fhe':
            args = [fhe_from_string(arg) for arg in vals]
            enc_sum = Ciphertext()
            evaluator.add_many(args, enc_sum)
            agg[eid] = enc_sum
        elif encryption == 'phe':
            print('TODO aggregation')

        #Use ope for min and max
        if encryption == 'clear':
            #We can use kpi for min/max, and we are not sending ope in clear
            search = 'SELECT ope FROM kpi WHERE EID = (?)'
        else:
            search = 'SELECT ope FROM kpi WHERE EID = (?)'
        print(search, eid)
        vals = m.execute(search, (eid,)).fetchall()
        print(vals)

        if len(vals) >= 1:
            ope_max[eid] = max(vals)
            ope_min[eid] = min(vals)

    m.close()
    conn.close()

    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' Aggregate End')
        times.write('\n')
    
    return agg, ope_max, ope_min
    #print(agg)

#Aggregate the KPIs we have. Returns a dict of average values with EID as keys
def aggregate_avg():
    print('Aggregate avg')

    #Get the EIDs for KPIs
    conn = sqlite3.connect('main.db')
    conn.row_factory = lambda cursor, row: row[0]
    m = conn.cursor()

    m.execute('SELECT EID FROM algorithm WHERE kpi = 1')
    kpi_list = m.fetchall()
    print(kpi_list)

    #Start aggregation
    global agg
    agg = {}

    for eid in kpi_list:
        search = 'SELECT value FROM kpi WHERE EID = (?)'
        print(search, eid)
        vals = m.execute(search, (eid,)).fetchall()

        #Average
        if encryption == 'clear':
            agg[eid] = np.mean(vals)
        elif encryption == 'fhe':
            args = [fhe_from_string(arg) for arg in vals]
            enc_sum = Ciphertext()
            evaluator.add_many(args, enc_sum)
            agg[eid] = enc_sum
        elif encryption == 'phe':
            print('TODO aggregation')

    m.close()
    conn.close()

    return agg

"""
#Takes a list of encrypted values in string representation and calculates their encrypted sum
def fhe_mean(fhe_list):
    enc_vals = []
    enc_vals = fhe_list
    #Turn into list Ciphertexts

    enc_sum = functions_fhe('+', enc_vals)
    #Use list length as divisor
    x = 1/len(fhe_list)
    divisor = Plaintext(str('{:x}'.format(int(x))))
    mean = Ciphertext()
    #Careful to use the Server!Evaluator
    evaluator.multiply_plain(enc_sum, divisor, mean)
    return mean
"""



#Adds Server!encrypted KPIs for a given client id
#TODO Server key
def add_kpi(client_id, kpi, ope):
    print('Add kpi')
    conn = sqlite3.connect('main.db')
    m = conn.cursor()

    """
    if encryption == 'clear':
        for key in kpi:
            print('Trying to insert into Table ID'+ client_id+ ': EID '+ key)# + ' and value '+ str(vals[key]))
            m.execute('INSERT OR REPLACE INTO kpi (CID, EID, value) VALUES (?,?,?)', (client_id, key, kpi[key]))
    else:
    """
    for key in kpi:
        #print('Key:', key, 'Val:', kpi[key])
        print('Trying to insert into Table ID'+ client_id+ ': EID '+ key + ' ope ' + str(ope[key]))# + ' and value '+ str(vals[key]))
        m.execute('INSERT OR REPLACE INTO kpi (CID, EID, value, ope) VALUES (?,?,?,?)', (client_id, key, kpi[key], ope[key]))
    conn.commit()
    m.close()
    conn.close()
    #printTable('main', 'kpi')

#Drops client of given id from the client database
def drop_client(id):
    print('Dropping client ID', id)
    """
    conn = sqlite3.connect('client.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS ID'+id)
    print('Dropping done')
    conn.commit()
    c.close()
    conn.close()
    
    conn = sqlite3.connect('obfus.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS ID'+id)
    print('Dropping done')
    conn.commit()
    c.close()
    conn.close()
    """
    os.remove('client.db')
    os.remove('obfus.db')
    print('Dropping done')

#Get a list of KPIs, based on the booleans in the algorithm database
def get_kpis(id):
    print('Getting kpis')
    conn = sqlite3.connect('main.db')
    conn.row_factory = lambda cursor, row: row[0]
    m = conn.cursor()
    m.execute('SELECT EID FROM algorithm WHERE kpi = 1')
    kpi_list = m.fetchall()
    m.close()
    conn.close()
    print('kpi=1:',kpi_list)

    conn = sqlite3.connect('client.db')
    c = conn.cursor()
    #Create a search in a client table for all EIDs in our KPI List
    search = 'SELECT * FROM ID' + id + ' WHERE EID IN (' + ','.join('?' for eid in kpi_list) + ')'
    #print(search)
    kpis = c.execute(search, (kpi_list)).fetchall()
    #print(kpis)
    c.close()
    conn.close()

    #Turn tuple into dict
    vals = {}
    for tup in kpis:
        vals[tup[0]] = tup[1]
    print('-'*50)
    print('Found values for following keys:')
    print(vals.keys())
    return vals

#Counts the number of Clients in the Client db
def count_clients():
    print('Count clients')
    conn = sqlite3.connect('main.db')
    m = conn.cursor()
    m.execute('SELECT count(*) FROM clients')
    count = m.fetchall()
    m = conn.cursor()
    print('Number of clients:', count[0][0])
    return count[0][0]


#Check if a funtion x can be removed from the todo dict given a dict of new values
def check_removal(func, val_dict):
    #print('Check removal')
    if func[1] in val_dict:
        return True
    return False



def check_todos(id):
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' CheckTodos Start')
        times.write('\n')
    print('Check todos')
    todos = []
    todo_list = client_todo_dict[id]
    #print('TODO LIST', todo_list)
    conn = sqlite3.connect('client.db')
    c = conn.cursor()

    #Get list of values we aready have for this client
    values = []
    c.execute("SELECT EID FROM ID" + id)
    tmp = c.fetchall()
    for e in tmp:
        values.append(e[0])
    #print(values)

    c.close()
    conn.close()

    #Check which functions we can now calculate, puts their EIDs in a list
    for func in todo_list:
        if is_doable(func, values):
            todos.append(func[1])

    #Check if there are no more todos
    if not todos:
        if log:
            times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
            times.write(str(time.perf_counter_ns()) + ' CheckTodos Start')
            times.write('\n')
        return todos


    #Get the algorithm for the EIDs based on previous list
    todos = lookup_algorithms(todos)
    #print('TODOS:', todos)
    #Output:
    #[['aa101', '*', 'va110 va112'], ['aa102', '/', 'va200 2'], ['aa103', '-', 'va300 10'], ['bb100', 'Min', 'vb100 vb101 vb102'], ['cc102', '+', 'vc201 vc202'], ['cc201', '+', '3 4'], ['cc202', '-', '4 3']]

    #Get the values for the args in the todo
    value_ids = []
    for funcs in todos:
        try:
            value_ids = value_ids + (funcs[2].split(' '))
        #Catch singular values
        except:
            value_ids = value_ids + [funcs[2]]
    print('VALUE IDs:', value_ids)

    #Remove args which are already numbers
    for arg in value_ids:
        if is_number(arg):
            value_ids.remove(arg)
    vals = lookup_values(value_ids, id)
    #print(vals)

    #Replace arg names with their values
    tmp = []
    for func in todos:
        #Contruct a temporary function
        tmp_fnc = [func[0], func[1]]
        try:
            args = func[2].split(' ')
        #Catch singular values
        except:
            args = [func[2]]
        for arg in args:
            #Check if number, and if not replace with vals. Then append to temp function
            if not is_number(arg):
                val = vals.get(arg)
                tmp_fnc.append(val)
            else:
                tmp_fnc.append(float(arg))
        tmp.append(tmp_fnc)

    todos = tmp

    #Create a temporary fake ID and obfuscate
    #fid_lookup[id] = TODO

    #print(todos)
    print('End check todos')
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.perf_counter_ns()) + ' CheckTodos End')
        times.write('\n')
    return todos

#Returns a list of algorithms for a given list of EIDs
def lookup_algorithms(eid_list):
    print('Lookup algorithm')
    conn = sqlite3.connect('main.db')
    m = conn.cursor()
    #print(len(eid_list), eid_list)
    lookup_list = []

    #SQLite can only do 999 variables, so we need to split them
    #Chunks of 950, just to be safe
    chunks = [eid_list[x:x+950] for x in range(0, len(eid_list), 950)]

    for chunk in chunks:
        #Create a variable search, probably a bit hacky
        search = 'SELECT * FROM algorithm WHERE EID IN (' + ','.join('?' for eid in chunk) + ')'

        m.execute(search, (chunk))
        lookup_list.extend(m.fetchall())

    m.close()
    conn.close()
    return lookup_list

#Returns a dict of values for a given list of EIDs
def lookup_values(eid_list, id):
    print('Lookup values')
    #print('EID List:', eid_list)
    vals = {}
    conn = sqlite3.connect('client.db')
    m = conn.cursor()

    #SQLite can only do 999 variables, so we need to split them
    #Chunks of 950, just to be safe
    chunks = [eid_list[x:x+950] for x in range(0, len(eid_list), 950)]

    for chunk in chunks:
        #Create a variable search, probably a bit hacky
        search = 'SELECT * FROM ID'+id+' WHERE EID IN (' + ','.join('?' for eid in chunk) + ')'

        m.execute(search, (chunk))

        #Tuple here
        tmp = m.fetchall()

        #Turn tuple into dict
        for tup in tmp:
            vals[tup[0]] = tup[1]
    m.close()
    conn.close()

    return vals


def is_doable(func, values):
    #print('Is doable')
    for arg in func[0]:
        #print('Func', func, 'Arg:', arg)
        if arg is None or not (arg in values or is_number(arg) or is_encrypted(arg)):
            #print('Not doable', arg)
            return False
    #print('Doable')
    return True

#Returns true if x is a number
def is_number(x):
    #print('Is number')
    try:
        x = float(x)
        return True
    except:
        return False

#Returns true if x is an encrypted number
def is_encrypted(x):
    #print('Is encrypted')
    #Phe
    if isinstance(x, Ciphertext):
        return True
    #FHE
    if isinstance(x, Ciphertext):
       return True
    return False


#Adds the given values for a given client ID to the database, sql injection might be possible
#Expects a dict of values with their EID as key
def add_values(id, vals):
    print('Add values')

    conn = sqlite3.connect('client.db')
    c = conn.cursor()

    c.execute('CREATE TABLE IF NOT EXISTS ID'+ id +' (EID string, value blob)')
    for key in vals:
        #Deal fhe encrypted numbers, since they cannot be saves in sqlite
        #print(key)
        if encryption == 'fhe':
            vals[key] = fhe_to_string(vals[key])

        #print('Key:', key, 'Val:', vals[key])
        #print('Inserting into Table ID'+ id+ ': EID '+ key + ' and value '+ str(vals[key]))
        c.execute('INSERT OR IGNORE INTO ID'+ id +' (EID, value) VALUES (?,?)', (key, vals[key]))
    conn.commit()
    c.close()
    conn.close()
    #printTable('client','ID'+id)

    #Remove todos from the list for the values we got
    print('Removing from todo list')
    tmp = [x for x in client_todo_dict.get(id) if not check_removal(x, vals)]
    print('tmp',tmp)
    client_todo_dict[id] = tmp
    #print('New todo list:', client_todo_dict.get(id))

def fhe_to_string(val):
    #print('Fhe to string')
    #Take care of unencrypted numbers
    if not isinstance(val, Ciphertext):
        return val
    else:
        #Save to file
        val.save('v_save')
        #Read as binary string
        f = open('v_save', 'rb')
        string_val = f.read()
        f.close()

        return string_val

def fhe_from_string(string_val):
    #print('Fhe from string')
    #Take care of unencrypted numbers
    if isinstance(string_val, Ciphertext):
        return string_val
    elif is_number(string_val):
        return string_val
    else:
        #Write binary string to a file
        f = open('v_load','wb')
        f.write(string_val)
        f.close()
        #Load from file using SEAL method and context
        v_loaded = Ciphertext()
        v_loaded.load(context,'v_load')

        return v_loaded


#Takes an algorithm and sets up a database and a list for fast searches
def process_algorithm(alg, kpi):
    print('Process algorithm')

    conn = sqlite3.connect('main.db')
    m = conn.cursor()
    for e in alg:
        EID = e[0]
        symbol = e[1]
        args = e[2]
        #Boolean if the EID is a KPI we want. Does not support initial raw values from client
        boo = EID in kpi
        m.execute("INSERT OR REPLACE INTO algorithm (EID, symbol, args, kpi) VALUES (?,?,?,?)", (EID, symbol, args, boo))
        try:
            a = args.split(' ')
        #Catch singular values
        except:
            a = [str(args)]
        alg_lookup.append([a, EID])
    print('Populated Algorithm Table')
    #m.execute("SELECT * FROM algorithm")
    #print(m.fetchall())
    #print(alg_lookup)
    conn.commit()
    m.close()
    conn.close()

    print('-'*50)
    print(alg_lookup)
    printTable('main', 'algorithm')
    print('TODO delete old db beforehand')

#Gets the lookup list from an existing database
def get_lookup():
    print('Get lookup')
    conn = sqlite3.connect('main.db')
    m = conn.cursor()

    m.execute("SELECT * FROM algorithm")
    funcs = m.fetchall()

    for func in funcs:
        EID = func[0]
        args = func[2]

        try:
            a = args.split(' ')
        #Catch singular values
        except:
            a = [str(args)]
        alg_lookup.append([a, EID])
    m.close()
    conn.close()


#From an initial contact generates a unique ID for the client in string form
def generate_id():
    return str(count_clients()+1)

#Adds a main.db entry for a client in the clients table
def add_client(cid, pub_key):

    print('Setting up client value database')
    conn2 = sqlite3.connect('client.db')
    c = conn2.cursor()
    conn2.commit()
    c.close()
    conn2.close()

    print('Add client')
    conn = sqlite3.connect('main.db')
    m = conn.cursor()

    if encryption == 'phe':
        print('TODO')
    #print("INSERT INTO clients (CID, pub_key, pwd, done) VALUES (?,?,?,?)", (cid, pub_key, 'todo?', False))
    m.execute("INSERT INTO clients (CID, pub_key, pwd, done) VALUES (?,?,?,?)", (cid, pub_key, 'todo?', False))
    #printTable('main','clients')
    conn.commit()
    m.close()
    conn.close()
    
#Adds a main.db entry for a client in the clients table considering FHE encryption
def add_client_fhe(cid, pub_key, relin_key):

    print('Setting up client value database')
    conn2 = sqlite3.connect('client.db')
    c = conn2.cursor()
    conn2.commit()
    c.close()
    conn2.close()

    print('Add client')
    conn = sqlite3.connect('main.db')
    m = conn.cursor()

    #print("INSERT INTO clients (CID, pub_key, pwd, done) VALUES (?,?,?,?)", (cid, pub_key, 'todo?', False))
    m.execute("INSERT INTO clients (CID, pub_key, pwd, done, relin_keys) VALUES (?,?,?,?,?)", (cid, pub_key, 'todo?', False, relin_key))
    #printTable('main','clients')
    conn.commit()
    m.close()
    conn.close()


#Sets up the database anew
def db_setup():
    #Flushing old database for testing TODO remove after done
    if os.path.isfile('./main.db'):
        os.remove('main.db')
    if os.path.isfile('./client.db'):
        os.remove('client.db')

    #Setting up main Database
    print('Setting up database')
    conn = sqlite3.connect('main.db')
    m = conn.cursor()
    print('Setting up tables')

    #Creating Tables
    m.execute('CREATE TABLE algorithm (EID string PRIMARY KEY, symbol string, args string, kpi boolean)')
    m.execute('CREATE TABLE clients (CID string PRIMARY KEY, pub_key blob, pwd string, done boolean, relin_keys blob)')
    m.execute('CREATE TABLE kpi (CID string NOT NULL, EID string NOT NULL, value blob, ope blob, done boolean, PRIMARY KEY(CID, EID))')
    conn.commit()
    m.close()
    conn.close()

    #Setting up client value database
    print('Setting up client value database')
    conn2 = sqlite3.connect('client.db')
    c = conn2.cursor()
    conn2.commit()
    c.close()
    conn2.close()
    
    #Setting up obfuscation database
    print('Setting up obfuscation database')
    conn2 = sqlite3.connect('obfus.db')
    c = conn2.cursor()
    conn2.commit()
    c.close()
    conn2.close()

def flush_db():
    print('Flushing old databases')
    conn = sqlite3.connect('main.db')
    m = conn.cursor()
    m.execute('DELETE FROM clients')
    m.execute('DELETE FROM kpi')
    conn.commit()
    m.close()
    conn.close()

    if os.path.isfile('./client.db'):
        os.remove('client.db')
    if os.path.isfile('./obfus.db'):
        os.remove('obfus.db')   
        
    conn2 = sqlite3.connect('client.db')
    c = conn2.cursor()
    conn2.commit()
    c.close()
    conn2.close()
    
    conn2 = sqlite3.connect('obfus.db')
    c = conn2.cursor()
    conn2.commit()
    c.close()
    conn2.close()


def printTable(db, table):
    print('Printing table', table, 'from database', db)
    conn = sqlite3.connect(db+'.db')
    c = conn.cursor()
    c.execute("SELECT * FROM "+table)
    print(c.fetchall())
    c.close()
    conn.close()


def level_array(level):
    lev = [60]
    for i in range(level):
        lev.append(40)
    lev.append(60)
    return lev

def setup_context():
    print('Setting up context')
    parms = EncryptionParameters(scheme_type.CKKS)
    poly_modulus_degree = 16384
    parms.set_poly_modulus_degree(poly_modulus_degree)
    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, LEVEL))

    global scale
    scale = pow(2.0, 40)

    global context
    context = SEALContext.Create(parms)

    global evaluator
    evaluator = Evaluator(context)

    global encoder
    encoder = CKKSEncoder(context)

    global parm_levels
    parm_levels = get_parms()
    
    lowest_parms(context)

#Main
if __name__ == '__main__':
    
    pythoneval.duration_start('setup')
    parser = argparse.ArgumentParser('Run Proxy')
    parser.add_argument('-l', '--level', type=int, default=7, help='Level for ckks as int')
    parser.add_argument('-p', '--polymod', type=int, default=16384, help='Poly modulus degree as int')
    parser.add_argument('-g', '--logging', action='store_true', help='Logging Flag')
    parser.add_argument('-e', '--encryption', type=str, default='fhe', help='Encryption type. Supported are clear and fhe. PHE ready for implementation.')
    parser.add_argument('-z', '--zero', action='store_true', help='Flag for the set_zero function used to reduce message sizes')
    parser.add_argument('-t', '--latency', action='store_true', help='Flag for enabling a naive latency method')
    parser.add_argument('-tu', '--latency_upload', type=float, default=0.05, help='Latency for uploading in seconds')
    parser.add_argument('-td', '--latency_download', type=float, default=0.05, help='Latency for downloadin in seconds')
    parser.add_argument('-d', '--dummies', action='store_true', help='Flag for enabling dummy functions, to obfuscate algorithm')
    parser.add_argument('-ds', '--dummies_scheme', type=str, default='random', help='Scheme to decide how many dummies are inserted. Implemented: random, fixed')
    parser.add_argument('-dn', '--dummies_number', type=int, default=3, help='Number of dummies the fixed scheme inserts')
    parser.add_argument('-dri', '--dummies_random_min', type=int, default=1, help='Minimum number of dummies the random scheme inserts')
    parser.add_argument('-dra', '--dummies_random_max', type=int, default=5, help='Maximum number of dummies the random scheme inserts')
    parser.add_argument('-dai', '--dummies_arguments_min', type=int, default=2, help='Minimum number of arguments a dummy which supports multiple arguments generates')
    parser.add_argument('-daa', '--dummies_arguments_max', type=int, default=5, help='Maximum number of arguments a dummy which supports multiple arguments generates')
    parser.add_argument('-drs', '--dummies_range_start', type=int, default=-1000, help='How low the value for a dummy argument can go')
    parser.add_argument('-dre', '--dummies_range_end', type=int, default=1000, help='How high the value for a dummy argument can go')
    parser.add_argument('-b', '--blinding', action='store_true', help='Flag for enabling blinding, to obfuscate algorithm')
    parser.add_argument('-bs', '--blinding_range_lower', type=int, default=1, help='Lower end of the factor we blind with')
    parser.add_argument('-be', '--blinding_range_upper', type=int, default=100, help='Upper end of the factor we blind with')
    parser.add_argument('-r', '--randomization', action='store_true', help='Flag for enabling random function names, to obfuscate algorithm')
    parsed_args, other_args = parser.parse_known_args()
    args = vars(parsed_args)

    #Create level array
    global LEVEL
    LEVEL = level_array(args['level'])
    
    #Set poly modulus degree
    global polmod
    polmod = args['polymod']
    
    global log
    log = args['logging']
    
    global encryption
    encryption = args['encryption']
    #Catch for older version
    if 'fhe' in other_args:
        encryption = 'fhe'
    
    #Enable latency
    latency = args['latency']
    #Upload/download latency in seconds
    if latency:
        upload = args['latency_upload']
        download = args['latency_download']
    
    #Wether we want to set all encrypted fhe ciphertexts to level 0 before sending
    set_zero = args['zero']
    
    #Enable dummies
    dummies = args['dummies']
    #Dummy setting
    if dummies:
        dummy_scheme = args['dummies_scheme']  #random, fixed
        dummy_number = args['dummies_number']   #Number of dummies to be inserted
        #Range for randomized number of dummies
        dummy_lower = args['dummies_random_min']
        dummy_upper = args['dummies_random_max']
        #Range for the number of arguments functions get, that can support multiple args
        dummy_mult_start = args['dummies_arguments_min'] 
        dummy_mult_end = args['dummies_arguments_max']
        #Range for dummy arguments
        dummy_arg_start = args['dummies_range_start']
        dummy_arg_end = args['dummies_range_end']
    
    #Enable blinding
    blinding = args['blinding']
    #Blinding settings
    if blinding:
        blind_lower = 1
        blind_upper = 100
    
    #Enable randomization
    randomization = args['randomization']


    print('Starting up Proxy')
    print('Looking for existing databases')
    if (os.path.isfile('./main.db') and os.path.isfile('./client.db') and os.path.isfile('./obfus.db')):
        print('Using existing databases')
        get_lookup()
    else:
        print('Database not found, creating new one')
        db_setup()

    try:
        if sys.argv[2] == 'old':
            print('Keeping old entries')
    except:
        flush_db()

    args = sys.argv
    #Get the encryption type
    if 'fhe' in args or encryption == 'fhe':
        encryption = 'fhe'
        print('Using fully homomorphic encryption')
        setup_context()
    elif 'phe' in args or encryption == 'phe':
        encryption = 'phe'
        print('Using partially homomorphic encryption')
    else:
        print('Using cleartexts')

    #Determine the symbols which can be done internally
    if encryption == 'phe':
        internal_symbols = ['+','-','=']
    elif encryption == 'fhe':
        internal_symbols = ['+','=','*','-']

    pythoneval.duration_stop('setup')

    print('Starting Server')
    #fake_client()
    api.run(debug=False, port=PORT_PROXY)
