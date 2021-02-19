from seal import *
import jsonpickle
import pickle
from phe import paillier
import sys
import json
import ctypes
import dill
import flask
from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
import requests
import base64
import sqlite3


def test_fhe():
    print('Testing FHE json/pickle')
    parms = EncryptionParameters(scheme_type.BFV)

    poly_modulus_degree = 4096
    parms.set_poly_modulus_degree(poly_modulus_degree)
    parms.set_coeff_modulus(CoeffModulus.BFVDefault(poly_modulus_degree))
    parms.set_plain_modulus(1000000000)

    context = SEALContext.Create(parms)

    #keygen = KeyGenerator(context)
    
    #pub_key = keygen.public_key()
    #priv_key = keygen.secret_key()

    #encryptor = Encryptor(context, pub_key)

    global evaluator
    evaluator = Evaluator(context)

    decryptor = Decryptor(context, priv_key)
    
    x = "5"
    x_plain = Plaintext(x)
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    print(x_encrypted)
    add = id(x_encrypted)
    print('Address:', add)
    print(ctypes.cast(add, ctypes.py_object).value)
    print(type(x_encrypted))
    
    print('-'*50)
    print('Serializing public key')
    print('Tryig json')
    try:
        json.dumps(pub_key)
    except:
        print('Json failed')
    print('Trying pickle')
    try:
        pickle.dumps(pub_key)
    except:
        print('Pickle failed')
        
    print('-'*50)
    print('Serializing evaluator')
    print('Tryig json')
    try:
        json.dumps(evaluator)
    except:
        print('Json failed')
    print('Trying pickle')
    try:
        pickle.dumps(evaluator)
    except:
        print('Pickle failed')
    
    print('-'*50)
    print('Serializing encrypted numbers')
    print('Tryig json')
    try:
        json.dumps(x_encrypted)
    except:
        print('Json failed')
    print('Trying pickle')
    try:
        pickle.dumps(x_encrypted)
    except:
        print('Pickle failed')
        
    print('-'*50)
    print('Looking at context')
    print(context)
    print(type(context))
    context_data = context.key_context_data()
    print(context_data)
    print(type(context_data))
    try:
        json.dumps(context)
    except:
        print('Json failed')
    print('Trying pickle')
    try:
        pickle.dumps(context)
    except:
        print('Pickle failed')
    print('Testing Dill')
    try:
        dill.dumps(context)
    except:
        print('Dill failed')


def test_phe():
    print('Testing PHE json/pickle')
    pub_key, priv_key = paillier.generate_paillier_keypair()
    print('Tryig json')
    
    x = 5
    
    x_encrypted = pub_key.encrypt(x)
    
    
    print('Serializing public key')
    print(pub_key)
    try:
        json.dumps(pub_key)
    except:
        print('Json failed')
    try:
        pickle_key = pickle.dumps(pub_key)
        unp_key = pickle.loads(pickle_key)
        print(unp_key)
        print(type(unp_key))
    except:
        print('Pickle failed')

    print('-'*50)
    print('Serializing encrypted numbers')
    print('Tryig json')
    try:
        json.dumps(x_encrypted)
    except:
        print('Json failed')
    print('Trying pickle')
    try:
        print(x_encrypted)
        p_x = pickle.dumps(x_encrypted)
        unp_x = pickle.loads(p_x)
        print(unp_x)
        print(type(unp_x)) 
    except:
        print('Pickle failed')
        
    

    
        
def test_keys():
    parms = EncryptionParameters(scheme_type.BFV)

    poly_modulus_degree = 4096
    parms.set_poly_modulus_degree(poly_modulus_degree)
    parms.set_coeff_modulus(CoeffModulus.BFVDefault(poly_modulus_degree))
    parms.set_plain_modulus(256)

    context = SEALContext.Create(parms)
    context2 = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    keygen2 = KeyGenerator(context2)
    
    pub_key = keygen.public_key()
    priv_key = keygen.secret_key()
    
    pub_key2 = keygen2.public_key()
    priv_key2 = keygen2.secret_key()

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)  
    evaluator2 = Evaluator(context2)

    decryptor = Decryptor(context, priv_key)
    decryptor2 = Decryptor(context2, priv_key2)
    
    
    x = "5"
    x_plain = Plaintext(x)
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    
    
    print('Trying to decrypt')
    x_decrypted = Plaintext()
    x_decrypted2 = Plaintext()
    
    decryptor.decrypt(x_encrypted, x_decrypted)
    decryptor2.decrypt(x_encrypted, x_decrypted2)
    
    print(x_decrypted.to_string())
    #print(x_decrypted2.to_string())
    
    
    plain_one = Plaintext("1")
    evaluator2.add_plain_inplace(x_encrypted, plain_one)
    
    decrypted_result = Plaintext()
    decryptor.decrypt(x_encrypted, decrypted_result)
    print(decrypted_result.to_string())
    
    """
    parms = EncryptionParameters(scheme_type.BFV)

    poly_modulus_degree = 4096
    parms.set_poly_modulus_degree(poly_modulus_degree)
    parms.set_coeff_modulus(CoeffModulus.BFVDefault(poly_modulus_degree))
    parms.set_plain_modulus(256)
    """
    
    print(parms.poly_modulus_degree)
    print(parms.coeff_modulus)
    print(parms.plain_modulus)
    print(scheme_type.BFV)
    """
    du = json.dumps([scheme_type.BFV, 4096, 256])
    loa = json.loads(du)
    
    parms3 = EncryptionParameters(loa[0])
    poly_modulus_degree3 = loa[1]
    parms3.set_poly_modulus_degree(poly_modulus_degree3)
    parms3.set_coeff_modulus(CoeffModulus.BFVDefault(poly_modulus_degree3))
    parms3.set_plain_modulus(loa[2])
    context3 = SEALContext.Create(parms3)
    evaluator3 = Evaluator(context3) 
    plain_one = Plaintext("1")
    evaluator2.add_plain_inplace(x_encrypted, plain_one)
    decrypted_result = Plaintext()
    decryptor.decrypt(x_encrypted, decrypted_result)
    print(decrypted_result.to_string())
    """
    
def fhe_methods():
    object_methods = [method_name for method_name in dir(evaluator) if callable(getattr(evaluator, method_name))]
    print(object_methods)

def pickling():
    parms = EncryptionParameters(scheme_type.BFV)

    poly_modulus_degree = 4096
    parms.set_poly_modulus_degree(poly_modulus_degree)
    parms.set_coeff_modulus(CoeffModulus.BFVDefault(poly_modulus_degree))
    parms.set_plain_modulus(256)

    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    pub_key = keygen.public_key()

    priv_key = keygen.secret_key()

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)  

    decryptor = Decryptor(context, priv_key)
    
    x = "5"
    y = "6"
    x_plain = Plaintext(x)
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    y_plain = Plaintext(y)
    y_encrypted = Ciphertext()
    encryptor.encrypt(y_plain, y_encrypted)
    
    
    #'load', 'parms_id', 'release', 'reserve', 'resize', 'save', 'scale', 'size'
    ret = x_encrypted.save('x_save')
    new_enc = Ciphertext()
    #ret = new_enc.load(context, 'x_save')
    #print(ret)
    
    #with open ("x_save", "r") as myfile:
    #    data=myfile.readlines()
    #with open('x_save', 'r') as f2:
    #    data = f2.read()
    #    print(data)
    
    
    #f = open('x_save', encoding='utf-8', errors='ignore')
    f = open('x_save', 'rb')
    #pickle.dumps(f)
    fs = f.read()
    #print(f)
    #base64.b64encode(f)
    print(fs)
    pfs = pickle.dumps(fs)
    
    
    test_db(pfs)
    
    
    print('-'*50)
    lstr = pickle.loads(pfs)
    print(lstr)
    lf = open('x_load','wb')
    lf.write(lstr)
    
    x_loaded = Ciphertext()
    x_loaded.load(context,'x_load')
    print(type(x_loaded))
    if type(x) == '<class \'seal.Ciphertext\'>':
       print(True)
    if isinstance(x_loaded, Ciphertext):
        print('test')

    decrypted_result = Plaintext()
    decryptor.decrypt(x_loaded, decrypted_result)
    print(decrypted_result.to_string())
    
    #proxy_post('values', f)
    
    
    #enc_lst = [x_encrypted, y_encrypted]
    
    
    
    #enc_lst.save('lst')


    #print(data)
    
    #pickle.dumps(x_encrypted)
    
def test_db(val):
    conn = sqlite3.connect('main.db')
    m = conn.cursor()
    m.execute('CREATE TABLE IF NOT EXISTS enc (EID string PRIMARY KEY, val blob)')
    m.execute("INSERT INTO enc (EID, val) VALUES (?,?)", ('aa1', val))
    conn.commit()
    m.close()
    conn.close()
    
    
    
    
def proxy_post(url, msg):
    #Post algorithm
    IP_PROXY = 'http://localhost:'
    PORT_PROXY = 5005
    c_url = IP_PROXY + str(PORT_PROXY) + '/' + url
    headers = {'Authorization' : '(some auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}
    
    #Try json first, otherwise we have to use pickle
    
    ret = requests.post(c_url, data = msg, headers=headers)
    #print(ret.text)
    print(ret.text)
    return json.loads(ret.text)

if __name__ == "__main__":
    #test_phe()
    #print('X'*70)
    #print('')
    test_fhe()
    #print('X'*70)
    #print('')
    #test_keys()
    #print('X'*70)
    #print('')
    #pickling()
    

