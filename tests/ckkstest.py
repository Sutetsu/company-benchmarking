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
import math


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



def get_level(enc):
    i = 1
    a = scale
    while i <= highest_level:
        if enc <= 2*a:
            return i
        a *= a
        i += 1
    return i
    
def magnitude(x):
    return int(math.log(x))

def test_ckks():
    parms = EncryptionParameters(scheme_type.CKKS)########################################

    poly_modulus_degree = 16384#8192########################################
    parms.set_poly_modulus_degree(poly_modulus_degree)
    
    """
    (1) Choose a 60-bit prime as the first prime in coeff_modulus. This will
            give the highest precision when decrypting;
    (2) Choose another 60-bit prime as the last element of coeff_modulus, as
            this will be used as the special prime and should be as large as the
            largest of the other primes;
    (3) Choose the intermediate primes to be close to each other.
    We use CoeffModulus::Create to generate primes of the appropriate size. Note
    that our coeff_modulus is 200 bits total, which is below the bound for our
    poly_modulus_degree: CoeffModulus::MaxBitCount(8192) returns 218.
    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [60, 40, 40, 60]))
    """
    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [60, 40, 40, 40, 60]))########################################

    """
    We choose the initial scale to be 2^40. At the last level, this leaves us
    60-40=20 bits of precision before the decimal point, and enough (roughly
    10-20 bits) of precision after the decimal point. Since our intermediate
    primes are 40 bits (in fact, they are very close to 2^40), we can achieve
    scale stabilization as described above.
    """
    global scale
    scale = pow(2.0, 40)########################################

    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    pub_key = keygen.public_key()

    priv_key = keygen.secret_key()
    
    relin_keys = keygen.relin_keys() ########################################

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)  

    decryptor = Decryptor(context, priv_key)
    
    global highest_level
    highest_level = context.key_context_data().chain_index()
    

    encoder = CKKSEncoder(context)########################################
    slot_count = 2#encoder.slot_count()########################################
    #encoder.slot_count(2)
    
    """
    inputs = DoubleVector()########################################
    curr_point = 0.0########################################
    step_size = 1.0 / (slot_count - 1)########################################
    
    
    for i in range(slot_count):########################################
        inputs.append(curr_point)########################################
        curr_point += step_size########################################
    """
    
    x = 0.55########################################
    y = 6########################################
    x_plain = Plaintext()
    y_plain = Plaintext()
    encoder.encode(x, scale, x_plain)########################################
    encoder.encode(y, scale, y_plain)########################################
    
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    y_encrypted = Ciphertext()
    encryptor.encrypt(y_plain, y_encrypted)
    
    ret = x_encrypted.save('x_save')
    
    print('Size y:',y_encrypted.size())
    evaluator.multiply_inplace(y_encrypted, x_encrypted)
    print('Size y:',y_encrypted.size())
    evaluator.multiply_inplace(y_encrypted, x_encrypted)
    print('Size y:',y_encrypted.size())
    evaluator.multiply_inplace(y_encrypted, x_encrypted)
    print('Size y:',y_encrypted.size())
    print('-'*50)
    print('Size y:',x_encrypted.size())
    
    #Read from file
    f = open('x_save', 'rb')
    fs = f.read()
    #print(fs)
    pfs = pickle.dumps(fs)
    
    #Sending here    

    
    print('-'*50)
    l_str = pickle.loads(pfs)
    #print(l_str)
    lf = open('x_load','wb')
    lf.write(l_str)
    
    x_loaded = Ciphertext()
    x_loaded.load(context,'x_load')
    print('Size xl:', x_loaded.size())
    print(type(x_loaded))
    if type(x) == '<class \'seal.Ciphertext\'>':
       print(True)
    if isinstance(x_loaded, Ciphertext):
        print('test')

    decrypted_result = Plaintext()
    decryptor.decrypt(x_loaded, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print(result)
    

    decrypted_result = Plaintext()
    decryptor.decrypt(x_encrypted, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print(result)    
    
    

    decrypted_result = Plaintext()
    decryptor.decrypt(y_encrypted, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print(result)   
    
    
    print(x_loaded.parms_id())
    print(y_encrypted.parms_id())
    
    print('-'*50)
    #print(x_loaded.scale())
    print(x_encrypted.scale())
    print(y_encrypted.scale())
    

    last_parms_id = x_encrypted.parms_id()
    new_enc = Ciphertext()
    #evaluator.mod_switch_to_next_inplace(x_encrypted)
    print('+'*50)
    print(new_enc.scale())
    print(y_encrypted.scale())
    
    print('#'*50)
    print(x_encrypted.parms_id())
    print(y_encrypted.parms_id())
    
    print(x_encrypted)
    
    decrypted_result = Plaintext()
    decryptor.decrypt(y_encrypted, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print(result)
    
    print('Highest level', highest_level)
    L1 = get_level(x_encrypted.scale())
    L2 = get_level(y_encrypted.scale())
    print('Levels',L1, L2)
    print('Size:', x_encrypted.size())
    print('Size:', y_encrypted.size())
    
    
    
    print('-'*50)
    scaled = False
    args = [x_encrypted, y_encrypted]
    while not scaled:
        print('scales')
        """
        print(x_encrypted.scale())
        print(y_encrypted.scale())
        print('relin')
        #evaluator.relinearize_inplace(x_encrypted, relin_keys)
        #evaluator.relinearize_inplace(y_encrypted, relin_keys)
        print(x_encrypted.scale())
        print(y_encrypted.scale())
        print('scaling')
        #x_encrypted.scale(pow(2.0, 40))
        #y_encrypted.scale(pow(2.0, 40))
        #evaluator.rescale_to_next_inplace(x_encrypted)
        #evaluator.rescale_to_next_inplace(y_encrypted)
        print(x_encrypted.scale())
        print(y_encrypted.scale())
        """
        
        mags = [magnitude(arg.scale()) for arg in args]
        mi = min(mags)
        ma = max(mags)
        
        for arg in args:
            if magnitude(arg.scale()) == ma:
                evaluator.rescale_to_next_inplace(arg)
            elif magnitude(arg.scale()) == mi:
                evaluator.mod_switch_to_next_inplace(arg)
        
        
        if magnitude(args[1].scale()) == magnitude(args[0].scale()):
            scaled = True
    x_encrypted = args[0]
    y_encrypted = args[1]
    
    
    x_encrypted.scale(pow(2.0, 40))
    y_encrypted.scale(pow(2.0, 40))
    print(x_encrypted.scale())
    print(y_encrypted.scale())
    
    
    decrypted_result = Plaintext()
    decryptor.decrypt(y_encrypted, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print(result)
    decrypted_result = Plaintext()
    decryptor.decrypt(x_encrypted, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print(result)
        
    print('Add y x')
    evaluator.add_inplace(y_encrypted, x_encrypted)
    print('Size:', y_encrypted.size())
    
    decrypted_result = Plaintext()
    decryptor.decrypt(y_encrypted, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print(result)
    print(y_encrypted.scale())
    #print(y_encrypted.parms_id())
    
    print('Add y x')
    evaluator.add_inplace(y_encrypted, x_encrypted)
    print('Size:', y_encrypted.size())
    
    decrypted_result = Plaintext()
    decryptor.decrypt(y_encrypted, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print('RESULT',result)
    print(y_encrypted.scale())
    #print(y_encrypted.parms_id())
    
    
    print('-'*50)
    decrypted_result = Plaintext()
    decryptor.decrypt(x_loaded, decrypted_result)
    result = DoubleVector()########################################'decode_biguint', 'decode_int32', 'decode_int64', 'decode_uint32', 'decode_uint64', 'encode'
    encoder.decode(decrypted_result, result)
    result = result[0]
    print('RESULT',result)
    print(x_loaded.scale())
    print(x_loaded.parms_id())      
    evaluator.relinearize_inplace(x_loaded, relin_keys)
    print(x_loaded.scale())
    print(x_loaded.parms_id()) 
    evaluator.rescale_to_next_inplace(x_loaded)
    print(x_loaded.scale())
    print(x_loaded.parms_id()) 
  
def magnitude(x):
    return int(math.log2(x))
  
def ckks_scaling():
    parms = EncryptionParameters(scheme_type.CKKS)########################################

    poly_modulus_degree = 16384#8192########################################
    parms.set_poly_modulus_degree(poly_modulus_degree)

    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [60, 40, 40, 40, 40, 40, 40, 40, 60]))########################################

    global scale
    scale = pow(2.0, 40)########################################

    global context
    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    pub_key = keygen.public_key()

    priv_key = keygen.secret_key()
    
    relin_keys = keygen.relin_keys() ########################################

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)  

    decryptor = Decryptor(context, priv_key)
    
    global highest_level
    highest_level = context.key_context_data().chain_index()
    
    
    parms = get_parms()
    print(parms)

    encoder = CKKSEncoder(context)
    slot_count = 2

    x = 2
    y = 3
    z = 16
    x_plain = Plaintext()
    y_plain = Plaintext()
    encoder.encode(x, scale, x_plain)
    encoder.encode(y, scale, y_plain)
    
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    y_encrypted = Ciphertext()
    encryptor.encrypt(y_plain, y_encrypted)
    prnt = x_encrypted
    print('-'*50)
    print('Encrypt')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    print('Scale',prnt.scale())
    
    res = Ciphertext()
    mul1 = Ciphertext()
    evaluator.multiply(x_encrypted, y_encrypted, mul1)
    res = mul1
    prnt = res
    res1 = res
    print('-'*50)
    print('Mult1')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    add = Ciphertext()
    evaluator.add(x_encrypted, y_encrypted, add)
    prnt = add
    print('-'*50)
    print('Add')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    
    rel = res
    evaluator.relinearize_inplace(rel, relin_keys)
    prnt = rel
    print('-'*50)
    print('Relin')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    """
    add2 = Ciphertext()
    evaluator.add(x_encrypted, add, add2)
    prnt = add2
    print('-'*50)
    print('Add2')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    evaluator.multiply(x_encrypted, res, res)
    prnt = res
    res2 = res
    print('-'*50)
    print('Mult2')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    evaluator.multiply(x_encrypted, res, res)
    prnt = res
    res2 = res
    print('-'*50)
    print('Mult2')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    prnt = mul1
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    evaluator.multiply(mul1, mul1, res)
    prnt = mul1
    print('-'*50)
    print('Mult11')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    """
    rel = res
    evaluator.relinearize_inplace(rel, relin_keys)
    prnt = rel
    print('-'*50)
    print('Relin')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    """
    evaluator.multiply(y_encrypted, res, res)
    prnt = res
    res3 = res
    print('-'*50)
    print('Mult3')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    """
    rel = res
    evaluator.relinearize_inplace(rel, relin_keys)
    prnt = rel
    print('-'*50)
    print('Relin')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    """
    tres = res
    evaluator.rescale_to_next_inplace(tres)

    print('-'*50)
    print('Rescale')
    prnt = tres
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    
    evaluator.mod_switch_to_inplace(res, res.parms_id())
    print('-'*50)
    prnt = x_encrypted
    print('Switch to')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    
    evaluator.multiply_inplace(res, x_encrypted)
    prnt = res
    print('Switch to')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    evaluator.multiply_inplace(res, x_encrypted)
    prnt = res
    print('Switch to')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    """
    res12 = Ciphertext()
    evaluator.multiply(res, res2, res12)
    prnt = res12
    print('-'*50)
    print('Mult12')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    
    tres = res
    evaluator.rescale_to_next_inplace(tres)
    """
    print('-'*50)
    print('Rescale')
    prnt = tres
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    print('-'*50)
    print('Res')
    prnt = res
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """
    
    """
    mres = res
    evaluator.mod_switch_to_next_inplace(mres)

    print('-'*50)
    print('mod_switch')
    prnt = mres
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    print('-'*50)
    print('Res')
    prnt = res
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    
    mres = res
    evaluator.mod_switch_to_next_inplace(mres)

    print('-'*50)
    print('mod_switch')
    prnt = mres
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())

    res11 = Ciphertext()
    sc1 = Ciphertext()
    evaluator.rescale_to_next(res1, sc1)
    prnt = sc1
    print('-'*50)
    print('Mult11')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    drop1 = Ciphertext()
    prnt = res1
    print('Before')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    evaluator.mod_switch_to_next(res1, drop1)
    prnt = drop1
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    print(res.scale())
    evaluator.add(res, res2, res11)
    prnt = res11
    print('-'*50)
    print('Mult3')
    print('Parms',prnt.parms_id())
    print('Size',prnt.size())
    print('Scale',prnt.scale())
    """

    decrypted_result = Plaintext()
    decryptor.decrypt(res, decrypted_result)
    result = DoubleVector()
    encoder.decode(decrypted_result, result)
    result = result[0]
    print('RESULT',result)
    
def get_parms():
    context_data = context.first_context_data()
    parms = {}
    i = 1
    while(context_data):
        parms[context_data.parms_id()[0]] = i
        i += 1
        context_data = context_data.next_context_data()
    return parms
    
def encrypt_zero():
    parms = EncryptionParameters(scheme_type.CKKS)########################################

    poly_modulus_degree = 16384#8192########################################
    parms.set_poly_modulus_degree(poly_modulus_degree)

    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [60, 40, 40, 40, 60]))########################################

    global scale
    scale = pow(2.0, 40)########################################

    global context
    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    pub_key = keygen.public_key()

    priv_key = keygen.secret_key()
    
    relin_keys = keygen.relin_keys() ########################################

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)  

    decryptor = Decryptor(context, priv_key)
    
    encoder = CKKSEncoder(context)
    
    val = 0
    
    v_plain = Plaintext()
    #v_plain.set_zero()
    encoder.encode(val, scale, v_plain)
    #Encrypt
    v_encrypted = Ciphertext()
    encryptor.encrypt(v_plain, v_encrypted)
    
    x_plain = Plaintext()
    encoder.encode(1, scale, x_plain)
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    
    y_plain = Plaintext()
    encoder.encode(1, scale, y_plain)
    y_encrypted = Ciphertext()
    encryptor.encrypt(y_plain, y_encrypted)
    
    evaluator.multiply_plain_inplace(v_encrypted, y_plain)
    """
    print(x_encrypted.scale(), v_encrypted.scale())
    evaluator.rescale_to_next_inplace(x_encrypted)
    print(x_encrypted.scale(), v_encrypted.scale())
    print(x_encrypted.parms_id(), v_encrypted.parms_id())
    
    x_encrypted.scale(pow(2.0, 40))
    v_encrypted.scale(pow(2.0, 40))
    evaluator.add_inplace(x_encrypted, v_encrypted)
    """
    evaluator.mod_switch_to_next_inplace(v_encrypted)
    decrypted = Plaintext()
    decryptor.decrypt(v_encrypted, decrypted)
    #From hexadecimal to decimal
    result = DoubleVector()
    encoder.decode(decrypted, result)#TODO we are still getting poly_modulus_degree/2 = 4096 entries here
    print(result[0])
    
    print('Done')
    
def zero_test():
    parms = EncryptionParameters(scheme_type.CKKS)########################################

    poly_modulus_degree = 16384#8192########################################
    parms.set_poly_modulus_degree(poly_modulus_degree)

    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [60, 40, 40, 40, 60]))########################################

    global scale
    scale = pow(2.0, 40)########################################

    global context
    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    pub_key = keygen.public_key()

    priv_key = keygen.secret_key()
    
    relin_keys = keygen.relin_keys() ########################################

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)  

    decryptor = Decryptor(context, priv_key)
    
    encoder = CKKSEncoder(context)

    zero = Ciphertext()
    
    print('before')
    encryptor.encrypt_zero(zero)
    print('after')
    print(zero)
    decrypted = Plaintext()
    decryptor.decrypt(zero, decrypted)
    #From hexadecimal to decimal
    result = DoubleVector()
    encoder.decode(decrypted, result)#TODO we are still getting poly_modulus_degree/2 = 4096 entries here
    print(result[0])
    
    
 
def div_test(): 
    parms = EncryptionParameters(scheme_type.CKKS)########################################

    poly_modulus_degree = 16384#8192########################################
    parms.set_poly_modulus_degree(poly_modulus_degree)

    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [60, 40, 40, 40, 60]))########################################

    global scale
    scale = pow(2.0, 40)########################################

    global context
    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    x = 0
    y = 3
    z = 16
    x_plain = Plaintext()
    y_plain = Plaintext()
    encoder.encode(x, scale, x_plain)
    encoder.encode(y, scale, y_plain)
    
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    y_encrypted = Ciphertext()
    encryptor.encrypt(y_plain, y_encrypted)
    
    v = 1
    v_plain = Plaintext()
    encoder.encode(val, scale, v_plain)
    v_encrypted = Ciphertext()
    encryptor.encrypt(v_plain, v_encrypted)
    
def sub_test(): 
    parms = EncryptionParameters(scheme_type.CKKS)########################################

    poly_modulus_degree = 16384#8192########################################
    parms.set_poly_modulus_degree(poly_modulus_degree)

    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [60, 40, 40, 40, 60]))########################################

    global scale
    scale = pow(2.0, 40)########################################

    global context
    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    pub_key = keygen.public_key()

    priv_key = keygen.secret_key()
    
    relin_keys = keygen.relin_keys() ########################################

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)  

    decryptor = Decryptor(context, priv_key)
    
    encoder = CKKSEncoder(context)
    
    x = 0
    y = -3.0
    z = 16
    x_plain = Plaintext()
    y_plain = Plaintext()
    encoder.encode(x, scale, x_plain)
    encoder.encode(y, scale, y_plain)
    
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    y_encrypted = Ciphertext()
    encryptor.encrypt(y_plain, y_encrypted)
    
    v = 1
    v_plain = Plaintext()
    encoder.encode(v, scale, v_plain)
    v_encrypted = Ciphertext()
    encryptor.encrypt(v_plain, v_encrypted)
    #From hexadecimal to decimal
    result = DoubleVector()
    evaluator.mod_switch_to_next_inplace(y_plain)
    encoder.decode(y_plain, result)#TODO we are still getting poly_modulus_degree/2 = 4096 entries here
    print(result[0])
    
    
    
def level_zero():
    parms = EncryptionParameters(scheme_type.CKKS)########################################

    poly_modulus_degree = 16384#8192########################################
    parms.set_poly_modulus_degree(poly_modulus_degree)

    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, [60, 40, 40, 40, 60]))########################################

    global scale
    scale = pow(2.0, 40)########################################

    global context
    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    pub_key = keygen.public_key()

    priv_key = keygen.secret_key()
    
    relin_keys = keygen.relin_keys() ########################################

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)  

    decryptor = Decryptor(context, priv_key)
    
    encoder = CKKSEncoder(context)
    
    prms = get_parms()
    print(prms)
    
    print('xxxxxxxxxxxxxxxxxxxxxx')
    print(context.last_parms_id())

    x = 2
    y = -3.0
    z = 16
    x_plain = Plaintext()
    y_plain = Plaintext()
    encoder.encode(x, scale, x_plain)
    encoder.encode(y, scale, y_plain)
    
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    y_encrypted = Ciphertext()
    encryptor.encrypt(y_plain, y_encrypted)    
    
    
    evaluator.multiply_inplace(x_encrypted, y_encrypted)
    evaluator.multiply_inplace(x_encrypted, y_encrypted)
    evaluator.multiply_inplace(x_encrypted, y_encrypted)
    
    print(x_encrypted.parms_id())
    print(magnitude(x_encrypted.scale()))
    
    print(x_encrypted)
    
    
    print('-'*50)
    print('Rescaling')
    while magnitude(x_encrypted.scale()) > 40 and prms[x_encrypted.parms_id()[0]] < len(prms):
        evaluator.rescale_to_next_inplace(x_encrypted)
    evaluator.mod_switch_to_inplace(x_encrypted, context.last_parms_id())

    

    print(x_encrypted.parms_id())
    print(magnitude(x_encrypted.scale()))
    
    
def lowest_parms():
    context_data = context.first_context_data()
    lowest = []
    i = 1
    while(context_data):
        i += 1
        context_data = context_data.next_context_data()
    lowest = context_data.parms_id()
    return parms

if __name__ == "__main__":
    #print(magnitude(float(sys.argv[1])))
    #test_fhe()
    #test_ckks()
    #ckks_scaling()
    #encrypt_zero()
    #zero_test()
    #sub_test()
    level_zero()

