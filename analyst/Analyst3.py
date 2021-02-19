#Analyst
import argparse
import sys
import json
import sqlite3
from flask import Flask, json
import requests
import os
import re

sys.path.append('../eval')
import pythoneval
pythoneval.enable_measurements(False)

algorithm = []
#Missing ['pw067','pw054','pw072','pi8020','pi8030','pi7040','pi6140']
#kpi_list = ['pw097','pw067','pw092','pw054','pw046','pw082','pw072','pw022','pi8020','pi8030','pi8010','pw028','pw036','bi0540','bi0550','bi0560','pw005','pw013','pw014','cw003','cw001','cw002','cw014','pw011','pw010','pw012','cw411','cw412','cw413','cw414','cw308','cw307','cw309','pi7040','pi7050','pi7060','pi8020','pi6120','pi6130','pi6140','bi0390','bi0400','bi0420','bi0410','ci5170','ci6090','ci6150','ci6160','ci7050','ci6190','ci6200','ci7060','bi0740','ci5221','ci5222','ci5223']
kpi_list = ['pw097','pw092','pw046','pw082','pw022','pi8010','pw028','pw036','bi0540','bi0550','bi0560','pw005','pw013','pw014','cw003','cw001','cw002','cw014','pw011','pw010','pw012','cw411','cw412','cw413','cw414','cw308','cw307','cw309','pi7050','pi7060','pi6120','pi6130','bi0390','bi0400','bi0420','bi0410','ci5170','ci6090','ci6150','ci6160','ci7050','ci6190','ci6200','ci7060','bi0740','ci5221','ci5222','ci5223']

proxy_url = 'http://localhost:5005/algorithm'

api = Flask(__name__)

path = 'parsed2.txt' #This is the IKV example
#path = 'parsed.txt' #Small Test
#path = 'parsed3.txt' #One function test
#path = 'parsed4.txt' #Multiplication test
#path = 'parsed5.txt' #Substraction test
#path = 'SyntheticAdd30.txt' #Synthetic

@api.route('/algorithm', methods=['GET'])
def get_algorithm():
    return json.dumps(algorithm)


def getFunc(string):
    s = string.split(' ')
    #Get EID
    EID = s[0]
    #Get symbol
    sym = s[1]
    #Get vars into a string for db
    t = s[2:]
    var = ' '.join([str(ele) for ele in t])
    func = [EID, sym, var]
    return func

#Reads parsed.txt and populates the atomic function database
def readParsed(path):
    todo = {}
    parsed = open(path, 'r')
    for line in parsed:
        #Remove newline at the end of each string
        string = line.rstrip()
        func = getFunc(string)
        print('Inserting', func)
        c.execute("INSERT OR IGNORE INTO funcs (EID, symbol, args) VALUES (?,?,?)", func)
    parsed.close()
    return todo

# Reads list of kpis from path
def readKpis(path):
    kpi_list = []

    re_kpi = re.compile(r'(?P<kpi>[a-zA-Z]+[0-9]+).*')

    with open(path, 'r') as fd:
        for line in fd:
            line = line.rstrip()
            kpi_match = re_kpi.match(line)

            if not kpi_match:
                print(f'Skipping KPI line \'{line}\'')
                continue

            kpi = kpi_match.group('kpi')
            kpi_list.append(kpi)

    print(kpi_list)
    return kpi_list

def printDB():
    with conn:
        c.execute("SELECT * FROM funcs")
        print(c.fetchall())

def getDBlist():
    with conn:
        c.execute("SELECT * FROM funcs")
        return c.fetchall()


#Main
if __name__ == '__main__':

    #path = sys.argv[1]

    parser = argparse.ArgumentParser('Run Analyst')
    parser.add_argument('-a', '--alg', type=str, help='Path to the algorithm file')
    parser.add_argument('-k', '--kpi', type=str, help='Path to the kpi file')
    parser.add_argument('-p', '--sec_path', type=str, help='Secondary path option. Ugly workaround so other code does not break')
    parsed_args, other_args = parser.parse_known_args()
    print(parsed_args)

    # either both or none must be setah
    if bool(parsed_args.alg) != bool(parsed_args.kpi):
        raise ValueError('Need to set both \'-a\'/\'--alg\' and \'-k\'/\'--kpi\' at the same time')

    if parsed_args.alg:
        if not os.path.isfile(parsed_args.alg):
            raise ValueError(f'Argument \'alg\' does not point to an existing algorithm file (found: {parsed_args.alg})')
        path = parsed_args.alg

    if parsed_args.alg:
        if not os.path.isfile(parsed_args.kpi):
            raise ValueError(f'Argument \'kpi\' does not point to an existing kpi file (found: {parsed_args.kpi})')
        kpi_list = readKpis(parsed_args.kpi)

    if parsed_args.sec_path:
        path = vars(parsed_args)['sec_path']

    pythoneval.duration_start('setup')

    #Setting up Database
    print('Setting up database')
    conn = sqlite3.connect('atomics.db')
    c = conn.cursor()
    #For now, later the parser would do this
    print('Setting up tables')
    c.execute('''DROP TABLE IF EXISTS funcs''')
    c.execute('''CREATE TABLE funcs (EID string PRIMARY KEY, symbol string, args string)''')

    pythoneval.duration_stop('setup')
    pythoneval.duration_start('algorithm')

    #Reading in atomic functions
    print('Reading in functions')
    atomicFunctions = readParsed(path)
    #printDB()
    algorithm = getDBlist()

    #Post algorithm
    #TODO remove and add a better way to read kpi ids
    if path == 'parsed.txt':
        kpi_list = ['va110','va112','va200','va300','vb100','vb101','vb102','vc201','vc202','aa100','aa101','aa102','aa103','bb100','cc100','cc101','cc102','cc201','cc202','dd100','ee100','aa001','ff100','ff200','aa001','aa002','ff100','ff101','aa003','ff1000','ff1010','va000','gg100','gg101','gg200','gg201']
    if path == 'parsed3.txt':
        kpi_list = ['bb0000']
    if path == 'parsed4.txt':
        kpi_list = ['va120','va130','va140','va150','va160']
    if path == 'parsed5.txt':
        kpi_list = ['fu855','fu858','fu857','fu856','fu854','ci5211']
    if 'Synthetic' in path:
        kpi_list = ['bb099']
    headers = {'Authorization' : '(auth code)', 'Accept' : 'application/json', 'Content-Type' : 'application/json'}
    msg = json.dumps({'key': 15, 'alg': algorithm, 'kpi': kpi_list})
    print(msg)
    print('Posting algorithm to proxy')
    ret = requests.post(proxy_url, data = msg, headers=headers)
    print(ret.text)

    pythoneval.duration_stop('algorithm')

