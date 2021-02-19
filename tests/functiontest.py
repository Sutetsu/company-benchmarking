from seal import *
import struct
import math

"""
    'exponentiate', 'exponentiate_inplace'
    'multiply','multiply_inplace','multiply_many','multiply_plain','multiply_plain_inplace'
    'square', 'square_inplace'
    'sub', 'sub_inplace', 'sub_plain', 'sub_plain_inplace'
"""

def float_to_hex(f):
    return hex(struct.unpack('<I', struct.pack('<f', f))[0])

def test_funcs():
    x = 1
    y = 6
    z = 0.5
    a = 8
    b = 9
    
    #print(float_to_hex(z))
    x_plain = Plaintext(str('{:x}'.format(int(x))))    
    y_plain = Plaintext(str('{:x}'.format(int(y))))     
    z_plain = Plaintext(str('{:x}'.format(int(z)))) 
    a_plain = Plaintext(str('{:x}'.format(int(a))))    
    b_plain = Plaintext(str('{:x}'.format(int(b))))
    
    
    x_encrypted = Ciphertext()
    encryptor.encrypt(x_plain, x_encrypted)
    y_encrypted = Ciphertext()
    encryptor.encrypt(y_plain, y_encrypted)
    z_encrypted = Ciphertext()
    encryptor.encrypt(z_plain, z_encrypted)
    
    result = Plaintext()
    decryptor.decrypt(z_encrypted, result)
    s_res = int(result.to_string(), 16)
    print("Z", s_res)

    
    #Addition
    # ([enc], res) -> None
    
    res = Ciphertext()
    lst = [x_encrypted, y_encrypted]
    evaluator.add_many(lst, res)
    
    result = Plaintext()
    decryptor.decrypt(res, result)
    s_res = int(result.to_string(), 16)
    print("x+Y", s_res)
    

    
    """
    #Substraction
    res = Ciphertext()
    evaluator.negate_inplace(x_encrypted)
    evaluator.negate_inplace(y_encrypted)
    lst = [z_encrypted, x_encrypted, y_encrypted]
    evaluator.add_many(lst, res)
    
    result = Plaintext()
    decryptor.decrypt(res, result)
    s_res = result.to_string()
    print(type(s_res))
    #if s_res >= 0x80:
    #    s_res -= 0x100
    print(s_res)
    """

def test_exp():
    print('TODO')
    
  
def test_mult():
    print('TODO')
    
    
def test_hex():
    for i in range(100):
        print('-'*20)
        #print(str(i))
        x = 7
        
        print('{:x}'.format(int(x)))
        x_plain = Plaintext(str('{:x}'.format(int(x))))    
        i_plain = Plaintext(str('{:x}'.format(int(i))))

        x_encrypted = Ciphertext()
        encryptor.encrypt(x_plain, x_encrypted)
        i_encrypted = Ciphertext()
        encryptor.encrypt(i_plain, i_encrypted)
        
        res = Ciphertext()
        lst = [x_encrypted, i_encrypted]
        evaluator.add_many(lst, res)
        
        result = Plaintext()
        decryptor.decrypt(res, result)
        
        
        
        """
        x_plain2 = Plaintext(x) 
        i_plain2 = Plaintext(str(i))
        
        x_encrypted2 = Ciphertext()
        encryptor.encrypt(x_plain2, x_encrypted2)
        i_encrypted2 = Ciphertext()
        encryptor.encrypt(i_plain2, i_encrypted2)
        
        res = Ciphertext()
        evaluator.add(x_encrypted2, i_encrypted2, res)
        result = Plaintext()
        decryptor.decrypt(res, result)
        """
        
        print("Dec " + str(i+int(x)) + " Res " + result.to_string() +  " Hex " + hex(i+int(x)))
        i+=1
    
def fhe_methods():
    print('Evaluator')
    print(type(evaluator))
    object_methods = [method_name for method_name in dir(evaluator) if callable(getattr(evaluator, method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Encryptor')
    print(type(encryptor))
    object_methods = [method_name for method_name in dir(encryptor) if callable(getattr(encryptor, method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Ciphertext')
    x = Ciphertext()
    print(type(x))
    object_methods = [method_name for method_name in dir(x) if callable(getattr(x, method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Plaintext')
    x = Plaintext()
    print(type(x))
    object_methods = [method_name for method_name in dir(x) if callable(getattr(x, method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Parms')
    print(type(parms))
    object_methods = [method_name for method_name in dir(parms) if callable(getattr(parms, method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Context')
    print(type(context))
    object_methods = [method_name for method_name in dir(context) if callable(getattr(context, method_name))]
    print(object_methods)

    print('-'*50)
    print('Public Key')
    print(type(pub_key))
    object_methods = [method_name for method_name in dir(pub_key) if callable(getattr(pub_key, method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Private Key')
    print(type(priv_key))
    object_methods = [method_name for method_name in dir(priv_key) if callable(getattr(priv_key, method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Relinearize Keys')
    print(type(relin_keys))
    object_methods = [method_name for method_name in dir(relin_keys) if callable(getattr(relin_keys, method_name))]
    print(object_methods)
    
    
    print('-'*50)
    print('Encoder')
    print(type(encoder))
    object_methods = [method_name for method_name in dir(encoder) if callable(getattr(encoder, method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Evaluator')
    print(type(DoubleVector()))
    object_methods = [method_name for method_name in dir(DoubleVector()) if callable(getattr(DoubleVector(), method_name))]
    print(object_methods)
    
    print('-'*50)
    print('Decryptor')
    print(type(decryptor))
    object_methods = [method_name for method_name in dir(decryptor) if callable(getattr(decryptor, method_name))]
    print(object_methods)
    
def test_plain():
    x = Plaintext("15")
    print(x.coeff_count)
    print(x.load)
    print(x.parms_id)
    print(x.release)
    print(x.reserve)
    print(x.resize)
    print(x.save("test"))
    print(x.scale)
    print(x.set_zero)
    y = Plaintext()
    print(y.load(context, "test"))
    print(y.to_string())
    
def test_pub_key_load():
    pub_key.save('pub_key')
    
    
    f = open('pub_key', 'rb')
    string_key = f.read()
    
    print(context.get_context_data())
    
    #-----------------------------#
    
    f = open('key2','wb')
    f.write(string_key)
    
    
    pub_key2 = PublicKey()
    pub_key2.load(context, 'key2')
    
    print(pub_key2)

if __name__ == "__main__":
    print('Setting up encryption')
    global parms
    parms = EncryptionParameters(scheme_type.BFV)

    poly_modulus_degree = 4096
    parms.set_poly_modulus_degree(poly_modulus_degree)
    parms.set_coeff_modulus(CoeffModulus.BFVDefault(poly_modulus_degree))
    parms.set_plain_modulus(4096)

    global context
    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    
    global pub_key, priv_key
    pub_key = keygen.public_key()
    priv_key = keygen.secret_key()

    global encryptor
    encryptor = Encryptor(context, pub_key)

    global evaluator
    evaluator = Evaluator(context)

    global decryptor
    decryptor = Decryptor(context, priv_key)
    
    global encoder
    encoder = IntegerEncoder(context)
    
    global relin_keys
    relin_keys = keygen.relin_keys()
    
    print('Printing fhe functions')
    fhe_methods()
    
    #print('Testing decryption output')
    #test_hex()
    
    #print('Testing FHE functions')
    #test_funcs()
    
    #print('Testing plaintext functions')
    #test_plain()
    
    #print('Testing the save/load function of PublicKey')
    #test_pub_key_load()

    
    
    

