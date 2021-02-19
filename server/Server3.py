#Server
import base64
import socket
import struct
import sys
import json
import sqlite3
from flask import Flask, json
import requests
from pyope.ope import OPE
from seal import *
import datetime
import os
import pathlib
import time
import argparse


sys.path.append('../eval')
import pythoneval
pythoneval.enable_measurements(False)

IP_PROXY = 'http://localhost:'
PORT_PROXY = 5005

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

def is_number(x):
    try:
        x = float(x)
        return True
    except:
        return False

def fhe_to_string(val):
    print('Fhe to string')
    #Take care of unencrypted numbers
    if not isinstance(val, PublicKey):
        return val
    else:
        #Save to file
        val.save('v_save')
        #Read as binary string
        f = open('v_save', 'rb')
        string_val = f.read()

        return string_val

def fhe_from_string(string_val):
    #print('Fhe from string')
    #Take care of unencrypted numbers
    if is_number(string_val):
        return string_val
    else:
        #Write binary string to a file
        f = open('v_load','wb')
        f.write(string_val)
        #Load from file using SEAL method and context
        v_loaded = Ciphertext()
        v_loaded.load(context,'v_load')

        return v_loaded

def send_keys(url, msg):
    #Post algorithm
    c_url = IP_PROXY + str(PORT_PROXY) + '/' + url
    headers = {'Authorization' : '(auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}

    msg_base = encode_dict(msg)
    msg = json.dumps(msg_base)

    print('Posting message to proxy')
    ret = requests.post(c_url, data = msg, headers=headers)
    #print(ret.text)
    #print(ret.content)

    msg_base = json.loads(ret.content)
    data = decode_dict(msg_base)

    return data


def save_keys(ope, he):
    print('Saving keys')
    fo = open('ope_key', 'wb')
    fo.write(ope)

    he.save('he_key')

@pythoneval.duration_function('setup')
def load_keys():
    print('Loading keys')
    global priv_key, ope_key, cipher

    create_context()

    priv_key = SecretKey()
    priv_key.load(context, 'he_key')

    global decryptor
    decryptor = Decryptor(context, priv_key)

    global encoder
    encoder = CKKSEncoder(context)

    fo = open('ope_key', 'rb')
    ope_key = fo.read()
    cipher = OPE(ope_key)


def generate_keys():
    print('Setting up OPE encryption')
    global cipher
    ope_key = OPE.generate_key()
    cipher = OPE(ope_key)

    print('Setting up HE encryption')
    create_context()

    keygen = KeyGenerator(context)

    global priv_key
    pub_key = keygen.public_key()
    priv_key = keygen.secret_key()

    global encryptor
    encryptor = Encryptor(context, pub_key)

    global evaluator
    evaluator = Evaluator(context)

    global decryptor
    decryptor = Decryptor(context, priv_key)

    global encoder
    encoder = CKKSEncoder(context)

    #Save keys for when we retrieve the kpis
    save_keys(ope_key, priv_key)

    return ope_key, pub_key

@pythoneval.traffic_function('aggregation_all', PORT_PROXY)
@pythoneval.duration_function('aggregation_all')
def get_statistics():
    c_url = IP_PROXY + str(PORT_PROXY) + '/' + '/statistics'
    headers = {'Authorization' : '(auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}

    ret = requests.get(c_url, headers=headers)
    #print(ret.content)
    print('Loading return message')

    msg_base = json.loads(ret.content)
    data = decode_dict(msg_base)

    he_sum = data.get('mean')
    ope_max = data.get('max')
    ope_min = data.get('min')
    client_count = data.get('count')

    print('Starting decryption')

    min_vals = decrypt_ope(ope_min)
    max_vals = decrypt_ope(ope_max)
    means = decrypt_he(he_sum, client_count)

    print('-'*50)
    print('MAX VALS', max_vals)

    print('-'*50)
    print('MIN VALS', min_vals)

    print('-'*50)
    print('MEAN VALS', means)
    
    if log:
        current_time = datetime.datetime.now()
        date = str(current_time.day)+'-'+str(current_time.month)+'__'+str(current_time.hour)+'-'+str(current_time.minute)+'-'+str(current_time.second)
        f = open(os.path.join('log', 'KPI-aggregated.txt'), 'w')
        f.write(json.dumps(means))
        f.close()


@pythoneval.traffic_function('aggregation_avg', PORT_PROXY)
@pythoneval.duration_function('aggregation_avg')
def get_statistics_avg():
    c_url = IP_PROXY + str(PORT_PROXY) + '/' + '/statistics-avg'
    headers = {'Authorization' : '(auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}

    ret = requests.get(c_url, headers=headers)
    #print(ret.content)
    print('Loading return message')

    msg_base = json.loads(ret.content)
    data = decode_dict(msg_base)

    he_sum = data.get('mean')
    client_count = data.get('count')

    print('Starting decryption')
    means = decrypt_he(he_sum, client_count)

    print('-'*50)
    print('MEAN VALS', means)


def decrypt_ope(ope):
    dec = {}
    for eid in ope:
        try:
            dec[eid] = cipher.decrypt(ope[eid])/100
        except:
            dec[eid] = ope[eid]/100
    return dec

def decrypt_he(he, number):
    dec = {}
    for eid in he:
        try:
            #From string representation
            enc_val = fhe_from_string(he[eid])
            #Decrypt
            decrypted = Plaintext()
            decryptor.decrypt(enc_val, decrypted)
            #From hexadecimal to decimal
            result = DoubleVector()
            encoder.decode(decrypted, result)
            dec[eid] = result[0]/number
        except:
            return he
    return dec


def create_context():
    global parms
    parms = EncryptionParameters(scheme_type.CKKS)

    poly_modulus_degree = polmod
    parms.set_poly_modulus_degree(poly_modulus_degree)
    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, LEVEL))

    scale = pow(2.0, 40)

    global context
    context = SEALContext.Create(parms)
    
def level_array(level):
    lev = [60]
    for i in range(level):
        lev.append(40)
    lev.append(60)
    return lev
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser('Run Server')
    parser.add_argument('-l', '--level', type=int, default=7, help='Level for ckks as int')
    parser.add_argument('-p', '--polymod', type=int, default=16384, help='Poly modulus degree as int')
    parser.add_argument('-g', '--logging', action='store_true', help='Logging Flag')
    parser.add_argument('-e', '--encryption', type=str, default='fhe', help='Encryption type. Supported are clear and fhe. PHE ready for implementation.')
    parsed_args, other_args = parser.parse_known_args()
    args = vars(parsed_args)
    print(args, other_args)
    
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
    
    
    if 'clear' in other_args:
        encryption = 'clear'
    if 'keys' in other_args:
        pythoneval.duration_start('setup')
        ope_key, fhe_pub_key = generate_keys()
        string_he_key = fhe_to_string(fhe_pub_key)
        msg = {'pwd': 6, 'ope': ope_key, 'he': string_he_key}
        print('Sending keys to proxy')
        send_keys('key', msg)
        pythoneval.duration_stop('setup')
    elif 'kpi' in other_args:
        print('Getting KPI from proxy')
        load_keys()
        get_statistics_avg()
        get_statistics()
