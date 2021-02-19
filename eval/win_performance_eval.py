#!/usr/bin/env python

import subprocess
import pathlib
import time
import datetime
import os
import shutil
import argparse

path = pathlib.Path().absolute().parent
ppath = os.path.join(path, "proxy")
apath = os.path.join(path, "analyst")
cpath = os.path.join(path, "client")
spath = os.path.join(path, "server")

#Move files from where they are generated to the log folder
def move_files(log_folder):
    shutil.move(os.path.join(ppath, 'log', 'Analyst-download.txt'), os.path.join(log_folder, 'Analyst-download.txt'))
    shutil.move(os.path.join(ppath, 'log', 'Analyst-upload.txt'), os.path.join(log_folder, 'Analyst-upload.txt'))
    shutil.move(os.path.join(ppath, 'log', 'Client-download.txt'), os.path.join(log_folder, 'Client-download.txt'))
    shutil.move(os.path.join(ppath, 'log', 'Client-upload.txt'), os.path.join(log_folder, 'Client-upload.txt'))
    shutil.move(os.path.join(ppath, 'log', 'Server-download.txt'), os.path.join(log_folder, 'Server-download.txt'))
    shutil.move(os.path.join(ppath, 'log', 'Server-upload.txt'), os.path.join(log_folder, 'Server-upload.txt'))
    shutil.move(os.path.join(spath, 'log', 'KPI-aggregated.txt'), os.path.join(log_folder, 'KPI-aggregated.txt'))
    shutil.move(os.path.join(path, 'times.txt'), os.path.join(log_folder, 'times.txt'))
  
#Delete files if they were left over from a former run
def del_files():
    try:
        os.remove(os.path.join(ppath, 'log', 'Analyst-download.txt'))
    except OSError:
        pass
    try:
        os.remove(os.path.join(ppath, 'log', 'Analyst-upload.txt'))
    except OSError:
        pass
    try:
        os.remove(os.path.join(ppath, 'log', 'Client-download.txt'))
    except OSError:
        pass
    try:
        os.remove(os.path.join(ppath, 'log', 'Client-upload.txt'))
    except OSError:
        pass
    try:
        os.remove(os.path.join(ppath, 'log', 'Server-download.txt'))
    except OSError:
        pass
    try:
        os.remove(os.path.join(ppath, 'log', 'Server-upload.txt'))
    except OSError:
        pass
    try:
        os.remove(os.path.join(spath, 'log', 'KPI-aggregated.txt'))
    except OSError:
        pass
    try:
        os.remove(os.path.join(path, 'times.txt'))
    except OSError:
        pass

def do_runs(args, c_file, a_file):
    encryption = args['encryption']
    runs = args['runs']
    clients = args['clients']
    obfus = args['obfuscation']
    lev = args['level']
    
    
    current_time = datetime.datetime.now()
    date = str(current_time.day)+'-'+str(current_time.month)+'__'+str(current_time.hour)+'-'+str(current_time.minute)+'-'+str(current_time.second)
    log = os.path.join('log', encryption + '--' + date)
    
    #Declared own name
    if args['folder_name']:
        log = args['folder_name']
    
    os.mkdir(log)
    for run in range(runs):
        t = time.time()
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' Start Start')
        times.write('\n')
        output_proxy = open('proxy_output.txt', 'wb')
        cmd = ['python.exe',ppath + "\Proxy3.py", encryption, '-g', '-l', str(lev), '-z', '-o']
        proxy = subprocess.Popen(cmd, stdout = output_proxy, cwd = ppath)

        print('Analyst')
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' Analyst Start')
        times.write('\n')
        cmd = ['python.exe',apath + "\Analyst3.py", '-p', a_file]
        analyst = subprocess.Popen(cmd, cwd = apath)
        analyst.wait()
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' Analyst End')
        times.write('\n')

        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' ServerKeys Start')
        times.write('\n')
        if encryption == 'fhe':
            print('Server keys')
            cmd = ['python.exe',spath + "\Server3.py", 'keys', encryption, '-g', '-l', str(lev)]
            server = subprocess.Popen(cmd, cwd = spath)
            server.wait()
            print('Keys sent')
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' ServerKeys End')
        times.write('\n')

        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' AllClient Start')
        times.write('\n')
        for cl in range(clients):
            print('Client', cl+1)
            cmd = ['python.exe',cpath + "\Client3.py", str(cl+1), encryption, '-g', '-l', str(lev), '-i', c_file]
            print(cmd)
            client = subprocess.Popen(cmd, cwd = cpath)
            client.wait()
            #os.remove(ppath + '\client.db')
            #os.remove(ppath + '\obfus.db')
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' AllClient End')
        times.write('\n')

        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' ServerKPI Start')
        times.write('\n')
        print('Server kpi')
        cmd = ['python.exe',spath + "\Server3.py", 'kpi', encryption, '-g', '-l', str(lev)]
        server = subprocess.Popen(cmd, cwd = spath)
        server.wait()
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' ServerKPI End')
        times.write('\n')
             
        proxy.terminate()
        os.remove(ppath + '\main.db')
        times = open(os.path.join(pathlib.Path().absolute().parent, 'times.txt'), 'a')
        times.write(str(time.time()) + ' End End')
        times.write('\n')
        times.close()
        l = os.path.join(log,str(run))
        os.mkdir(l)
        move_files(l)    


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Run Performance Eval')
    parser.add_argument('-e', '--encryption', type=str, default='fhe', help='Encryption type. Supported are clear and fhe. PHE ready for implementation.')
    parser.add_argument('-r', '--runs', type=int, default=30, help='Number of runs we want to perform')
    parser.add_argument('-c', '--clients', type=int, default=6, help='Number of clients')
    parser.add_argument('-f', '--folder_name', type=str, help='If we want to set a specific folder name, otherwise it will be \'encryption type--date\' ')
    parser.add_argument('-s', '--synthetic', type=str, help='Synthetic runs. Supported are Abs, Min and Add. Capitalization important')
    parser.add_argument('-o', '--obfuscation', action='store_true', help='Flag for enabling obfuscation')
    parser.add_argument('-l', '--level', type=int, default=7, help='Level for ckks as int')
    parser.add_argument('-z', '--zero', action='store_true', help='Flag for the set_zero function used to reduce message sizes')
    parsed_args, other_args = parser.parse_known_args()
    args = vars(parsed_args)
    print(args, other_args)
    
    del_files()
    
    #Synthetic runs
    if args['synthetic']:
        synth = args['synthetic']
        analyst_runs = ['10']#,'20','30','40','50','60','70','80','90','100']
        if synth == 'Abs':
            c_file = './SyntheticOneArg.xlsx'
        else:
            c_file = './SyntheticTwoArg.xlsx'
        
        for r in analyst_runs:
            a_file = './Synthetic' + synth + r + '.txt'
            args['clients'] = 1
            do_runs(args, c_file, a_file)
            
    
    #IKV runs
    else:
        c_file = './ClientData.xlsx'
        a_file = './parsed2.txt'
        do_runs(args, c_file, a_file)


    
    
    

    
    
    
    