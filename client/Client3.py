#Client
import argparse
import base64
import sys
import json
import os
import requests
import xlrd
import math
from seal import *
from phe import paillier
from pyope.ope import OPE
import datetime
import pathlib
import time

sys.path.append('../eval')
import pythoneval
pythoneval.enable_measurements(False)

IP_PROXY = 'http://localhost:'
PORT_PROXY = 5005
pub_key = 5
priv_key = 2
client_id = 0

#Path of client data
#path = r'./ClientData.xlsx'
#path = r'./SmallTest.xlsx'
#path = r'./SmallTest3.xlsx'
#path = r'./SmallTest4.xlsx'
#path = r'./SmallTest5.xlsx'
#path = r'./scaling.xlsx'
#path = r'./testcase.xlsx'

pub_key = PublicKey()

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

#Takes a url and returns the get message
def proxy_get(url):
    c_url = IP_PROXY + str(PORT_PROXY) + '/' + url
    ret = requests.get(c_url)
    msg = json.loads(ret.content)
    print(msg)
    return msg

#Takes a url and a message in jsonable form
def proxy_post(url, msg):
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

#Generating initial message for proxy
def initial():
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' ClientInitial Start')
        times.write('\n')
    print('Setting up for proxy message')
    #vals = read_vals()
    if encryption == 'fhe':
        params = [
                parms.poly_modulus_degree,
                parms.coeff_modulus,
                parms.plain_modulus
                ]
        #print(params)

        #Save keys to file
        relin_keys.save('relins')
        global pub_key
        #print(pub_key)
        pub_key.save('pub')
        #Read as binary string
        f = open('relins', 'rb')
        relins = f.read()
        f.close()
        #Read as binary string
        f = open('pub', 'rb')
        pub_key_str = f.read()
        f.close()
        #print(relins)
        msg = {'relin': relins, 'key': pub_key_str}
    else:
        pub_key = 5
        msg = {'key': pub_key}
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' ClientInitial End')
        times.write('\n')
    return proxy_post('initial', msg)

#Get vals, from a .xlsx file, returns a dict
def read_vals(client):
    vals = {}
    sh = xlrd.open_workbook(path).sheets()
    for sh in xlrd.open_workbook(path).sheets():
        for row in range(sh.nrows):
            #print('Row:', row)
            #Get EID
            EID = sh.cell(row,0).value
            #Get val
            val = sh.cell(row,int(client)).value
            #Deal with entries other than numbers here
            if val == 'X':
                val = 1
            elif val == 'O' or val == '[]':
                val = 0
            elif val == 'EMPTY':
                val = -1
            elif not is_number(val):
                #print('Found string:', val)
                val = sys.maxsize
            vals[EID] = val
    #print(vals)
    return vals

#Calculates the functions from the proxy's return list
def do_calcs(todos):
    print('Calculating functions sent by proxy')
    res = {}
    for func in todos:
        eid = func[0]
        symbol = func[1]
        args = func[2:]

        if encryption == 'fhe':
            args = decrypt_fhe(args)
        elif encryption == 'phe':
            args = decrypt_phe(args)

        #print('Calculating EID', eid, 'with function', symbol, args)
        val = functions(symbol, args)
        if isinstance(val, complex):
            val = val.real
        #print('Result: ' + eid + ' = ' + str(val))
        res[eid] = val
    return res

def functions(symbol, args):
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
            res *= arg
        return res
    #Division
    if symbol == '/':
        if args[1] == 0:
            return 0
        if args[1] > (-1*10**(-6)) and args[1] < (1*10**(-6)):
            #input('Number too small')
            return 0
        return (args[0]/args[1])
    #Root
    if symbol == 'Wurzel':
        return math.sqrt(args[0])
    if symbol == '^':
        return args[0] ** args[1]
    #Minimum
    if symbol == 'Min':
        return min(args)
    #Maximum
    if symbol == 'Max':
        return max(args)
    #Absolute
    if symbol == 'Abs':
        return abs(args[0])


def setup_phe():
    global pub_key, priv_key
    pub_key, priv_key = paillier.generate_paillier_keypair()


#Given a dict of values, encrypts them using FHE and returns a dict of encrypted values in binary string format
def encrypt_fhe(vals):
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' EncryptionClient Start')
        times.write('\n')
    print('Encrypting values')
    ret = {}
    #print(len(vals))
    for i, key in enumerate(vals):
        # print('.', end='')
        # if i % 100 == 0:
        #     print(i, end='')
        #Encode for CKKS
        v_plain = Plaintext()
        encoder.encode(vals[key], scale, v_plain)
        #Encrypt
        v_encrypted = Ciphertext()
        encryptor.encrypt(v_plain, v_encrypted)
        #Save to file
        v_encrypted.save('v_save')
        #Read as binary string
        f = open('v_save', 'rb')
        string_val = f.read()
        f.close()
        ret[key] = string_val
    
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' EncryptionClient End')
        times.write('\n')
    return ret

#Given a list of encrypted values in binary string format, decrypts them using FHE and returns a list of decrypted values
def decrypt_fhe(vals):
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' DecryptionClient Start')
        times.write('\n')
    #print('Decrypting values')
    ret = []
    for val in vals:
        #print('.', end='')
        #Catch unencrypted values
        if is_number(val):
            ret.append(val)
        else:
            #Write binary string to a file
            f = open('v_load','wb')
            f.write(val)
            f.close()
            #Load from file using SEAL method and context
            v_loaded = Ciphertext()
            v_loaded.load(context,'v_load')
            #Decrypt
            decrypted = Plaintext()
            decryptor.decrypt(v_loaded, decrypted)
            #From hexadecimal to decimal
            result = DoubleVector()
            encoder.decode(decrypted, result)#TODO we are still getting poly_modulus_degree/2 = 4096 entries here
            #print(result[0])
            ret.append(result[0])
            
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' DecryptionClient End')
        times.write('\n')
    return ret

#Given a dict of values, encrypts them using FHE and returns a dict of encrypted values
def encrypt_phe(vals):
    print('TODO')

#Given a dict of encrypted values, decrypts them using PHE and returns a dict of decrypted values
def decrypt_phe(vals):
    print('TODO')

def get_encryption():
    print('TODO')
    return encryption

#Since decrypt_fhe expects a list, we give it lists of singular kpi values. Returns a list of decrypted kpis
def format_kpi(kpi_d):
    kpi = {}
    for key in kpi_d:
        t_val = [kpi_d[key]]
        val = decrypt_fhe(t_val)[0]
        kpi[key] = val
    return kpi


#Expects a dict of kpis and returns two dicts of encryptd kpis, one for he, one for ope
def kpi_aggregation(kpi, ope_key, he_key_string):
    print('Prerparing message for aggregation')
    cipher = OPE(ope_key)
    he_kpi = {}
    ope_kpi = {}

    #Figure out what we do with the he key
    if encryption == 'fhe':
        #Use save/load function
        #Write binary string to a file
        f = open('he_key','wb')
        f.write(he_key_string)
        #Load from file using SEAL method and context
        pub_he_key = PublicKey()
        pub_he_key.load(context, 'he_key')
        encryptor = Encryptor(context, pub_he_key)
    elif encryption == 'phe':
        print('TODO')
    else:
        #Should be clear text here
        print('Cleartext, no encryption needed')
        return kpi, kpi

    #Iterate through dict and encrypt
    for key in kpi:
        #Ope
        #print(kpi[key])
        #TODO deal with negative and too big numbers
        val = int(float(kpi[key])*100)%(2**14-3)
        if val < 0:
            val = val * -1
        ope_kpi[key] = cipher.encrypt(val)

        #HE
        if encryption == 'fhe':
            #Encrypt value
            v_encrypted = Ciphertext()
            #print('Encrypting',kpi[key])
            plain_val = Plaintext()
            encoder.encode(kpi[key], scale, plain_val)
            encryptor.encrypt(plain_val, v_encrypted)
            #Save to file
            v_encrypted.save('v_save')
            #Read as binary string
            f = open('v_save', 'rb')
            string_val = f.read()

            he_kpi[key] = string_val
        elif encryption == 'phe':
            print('TODO')

    return he_kpi, ope_kpi

def setup_fhe():
    global parms
    parms = EncryptionParameters(scheme_type.CKKS)

    poly_modulus_degree = polmod
    parms.set_poly_modulus_degree(poly_modulus_degree)
    parms.set_coeff_modulus(CoeffModulus.Create(poly_modulus_degree, LEVEL))

    global scale
    scale = pow(2.0, 40)

    global context
    context = SEALContext.Create(parms)

    keygen = KeyGenerator(context)
    global pub_key, priv_key, encryptor, evaluator, decryptor, relin_keys, encoder
    pub_key = keygen.public_key()
    priv_key = keygen.secret_key()
    relin_keys = keygen.relin_keys()

    encryptor = Encryptor(context, pub_key)

    evaluator = Evaluator(context)

    decryptor = Decryptor(context, priv_key)

    encoder = CKKSEncoder(context)


def ope_clear(kpi):
    ope = {}
    for key in kpi:
        val = int(float(kpi[key])*100)%(2**14-3)
        #print(key, kpi[key], val)
        if val < 0:
            val = val * -1
        ope[key] = val
    return ope
    
#returns true if a function can be computed given a dictionary      Contribution Alexander
def isdoable(algorithm, values):
	#function is already computed
        if algorithm[0] in values:
            return False
        #otherwise checks if parameters are numbers / in the dictionary
        else:
            needed = algorithm[2]
            if is_number(needed):
                return True
            needed = needed.split(" ")
            for i in range(0, len(needed)):
                if is_number(needed[i]):
                    continue
                if not is_number(needed[i]) and not needed[i] in values:
                    return False
            return True


def level_array(level):
    lev = [60]
    for i in range(level):
        lev.append(40)
    lev.append(60)
    return lev

if __name__ == "__main__":

    parser = argparse.ArgumentParser('Run Client')
    parser.add_argument('-l', '--level', type=int, default=7, help='Level for ckks as int')
    parser.add_argument('-p', '--polymod', type=int, default=16384, help='Poly modulus degree as int')
    parser.add_argument('-g', '--logging', action='store_true', help='Logging Flag')
    parser.add_argument('-e', '--encryption', type=str, default='fhe', help='Encryption type. Supported are clear and fhe. PHE ready for implementation.')
    parser.add_argument('-i', '--input', type=str, default='./ClientData.xlsx', help='Path to the input file')
    parser.add_argument('-c', '--clientcol', type=int, help='Column number-1 if our table contains multiple clients.')
    parser.add_argument('-s', '--sendlim', type=int, default=50, help='Number of values the client can send at once, to prevent jamming resources.')
    parsed_args, other_args = parser.parse_known_args()
    args = vars(parsed_args)
    print(parsed_args, other_args)
    
    global log
    log = args['logging']

    #Create level array
    global LEVEL
    LEVEL = level_array(args['level'])
    
    #Set poly modulus degree
    global polmod
    polmod = args['polymod']
    
    global encryption
    encryption = args['encryption']
    
    global SENDING_LIMIT
    SENDING_LIMIT = args['sendlim']
    
    print('Starting Client')
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' Client Start')
        times.write('\n')

    if parsed_args.input:
        if not os.path.isfile(parsed_args.input):
            raise ValueError(f'Argument \'input\' does not point to an existing input file (found: {parsed_args.input})')
        path = parsed_args.input

    pythoneval.traffic_start('setup', PORT_PROXY)
    pythoneval.duration_start('setup')

    #Get the encryption type
    if 'fhe' in args or encryption == 'fhe': #Need the or because of dependencies in other files
        encryption = 'fhe'
        print('Using fully homomorphic encryption')
    elif 'phe' in args:
        encryption = 'phe'
        print('Using partially homomorphic encryption')
    elif 'local' in args:
    	encryption = 'local'
    	print('computing local')
    else:
        print('Using cleartexts')
        print('Increasing sending limit')
        SENDING_LIMIT = 9999
    encryption = get_encryption()

    if encryption == 'fhe':
        setup_fhe()
    elif encryption == 'phe':
        setup_phe()
        
    #get algorithms from proxy
    if encryption == 'local':
    	data = proxy_get('getalgorithm')
    	algorithms = data.get('alg')

    #Get a client id
    	
    ret = initial()

    client_id = ret.get('id')
    ope_key = ret.get('ope')
    he_key = ret.get('he')
    print('Client ID:', client_id)

    pythoneval.duration_stop('setup')
    pythoneval.traffic_stop() # setup
    pythoneval.traffic_start('computation', PORT_PROXY)
    pythoneval.duration_start('computation')

    #Provide initial values
    if parsed_args.clientcol:
        vals = read_vals(parsed_args['clientcol'])
    else:
        vals = read_vals(sys.argv[1])
    print('-'*50)
    result = {}
    #local computation         Contribution Alexander
    if encryption == 'local':
        todo = []
        kpis = []
        allvalues = vals
        print('ALGORITHMS: ', algorithms)
        #check algorithm for kpis
        for i in algorithms:
            if i[3]==1:
                kpis.append(i)
        calcs_done=0
        #loop gets executed as long as we computed a new value
        while True:
             calcs_done = 0
             todo = []
             #go through algorithms
             for i in range(0,len(algorithms)):
                 print('ALGORITHM: ', algorithms[i])
                 #check if operator is '='
                 if algorithms[i][1]=='=':
                    print('=: ', algorithms[i])
                    #checks if '=' can be made 
                    if  not algorithms[i][0] in allvalues and is_number(algorithms[i][2]) or algorithms[i][2] in allvalues:
                    			#execute '=' operation
                        		calcs_done += 1
                        		if not is_number(algorithms[i][2]):
                            			number = allvalues[algorithms[i][2]]
                        		else:
                            			number = algorithms[i][2]
                        		allvalues[algorithms[i][0]]=number
		#checks if operation can be made                        		
                 elif isdoable(algorithms[i], allvalues):
                    		calcs_done += 1
                    		calculate = [algorithms[i][0], algorithms[i][1]]
                    		#checks parameters, brings thhem to the right format
                    		if not is_number(algorithms[i][2]):
                    			arguments = algorithms[i][2].split(" ")
                    		else:
                    			arguments = algorithms[i][2]
                    		if not is_number(arguments):
                    			for j in range(0, len(arguments)):
                    				if not is_number(arguments[j]):
                    					customerval = arguments[j]
                    					arguments[j] = allvalues[customerval]
                    			for k in range(0, len(arguments)):
                    				#print('ARGS: ', arguments[k])
                    				calculate.append(float(arguments[k]))
                    		else:
                    			calculate.append(arguments)
                    		todo.append(calculate)
             print("TODO: ", todo)
             #calculates operations
             result = do_calcs(todo)
             print("RESULTS: ", result)
             #adds results to known values
             for l in range(0, len(todo)):
                 allvalues[todo[l][0]] = result[todo[l][0]]
             #break if no calculation could be done
             if calcs_done == 0:
                 break
        	
        print("calculations complete")
        result = {}
        #checks values for kpis
        for z in range(0, len(kpis)):
            if kpis[z][0] in allvalues:
                result[kpis[z][0]] = allvalues[kpis[z][0]]
        print('KPIs: ', result)
        #pythoneval.duration_stop(computation_local)
        pythoneval.duration_stop('computation')
        pythoneval.traffic_stop() # computation
        pythoneval.traffic_start('aggregation_client', PORT_PROXY)
        pythoneval.duration_start('aggregation_client')
        pythoneval.duration_stop('aggregation_client')
        pythoneval.traffic_stop() # aggregation
        sys.exit()
        
    else:
	    done = None
	    #print(list(vals.items())[:4])
	    computation_local = pythoneval.duration_start('computation_local', considerOverall=False)
	    while 1:
      		#print('TODO', vals.keys())
 	     	sending = dict(list(vals.items())[:SENDING_LIMIT])
      		for key in sending.keys():
      			vals.pop(key)
      		#print(sending)

      	  	#Take care of the encryption here
    	  	if encryption == 'fhe':
      			sending = encrypt_fhe(sending)
      		elif encryption == 'phe':
      			sending = encrypt_phe(sending)

 	     	computation_local_exclude = pythoneval.duration_start('computation_local', exclude=True, considerOverall=False)
      		msg = {'id': client_id, 'values': sending}
      		ret = proxy_post('values', msg)
      		pythoneval.duration_stop(computation_local_exclude)

      		done = ret.get('done')
      		if done == 1:
      			break

      		results = do_calcs(ret.get('todo'))
      		#print('Results', results)
      		vals = {**results, **vals}
    pythoneval.duration_stop(computation_local)

    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' ClientAggregation Start')
        times.write('\n')
    
    #End of encrypted dialogue
    print('-'*50)
    print('Got own KPIs!')
    kpi = format_kpi(ret.get('kpi'))
    print('KPIs', kpi)
    
    #if log:
    #    current_time = datetime.datetime.now()
    #    date = str(current_time.day)+'-'+str(current_time.month)+'__'+str(current_time.hour)+'-'+str(current_time.minute)+'-'+str(current_time.second)
    #    f = open('KPI-' + encryption + '--' + date +'.txt', 'w')
    #    f.write(json.dumps(kpi))
    #    f.close()
    print('In total', len(kpi), 'KPI')

    pythoneval.duration_stop('computation')
    pythoneval.traffic_stop() # computation
    pythoneval.traffic_start('aggregation_client', PORT_PROXY)
    pythoneval.duration_start('aggregation_client')

    if not encryption == 'clear':
        #Decrypt and encrypt with server key here
        he_kpi, ope_kpi = kpi_aggregation(kpi, ope_key, he_key)
        msg = {'id': client_id, 'kpi': he_kpi, 'ope': ope_kpi}
        #print(ope_kpi)
    else:
        ope = ope_clear(kpi)
        #print('Ope', ope)
        msg = {'id': client_id, 'kpi': kpi, 'ope': ope}
    
    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' ClientAggregation End')
        times.write('\n')
    
    proxy_post('kpi', msg)

    if log:
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' Client End')
        times.write('\n')
    
    pythoneval.duration_stop('aggregation_client')
    pythoneval.traffic_stop() # aggregation
