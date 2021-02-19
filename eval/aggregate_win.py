#!/usr/bin/env python

import subprocess
import pathlib
import time
import datetime
import os
import shutil
import sys

lpath = os.path.join(pathlib.Path().absolute(), 'log')

max_abs = 0
max_rel = 0
ma_folder = 0
mr_folder = 0
r_kpi = ''
a_kpi = ''

#Numer of folders
fo = 30

sending = ['Analyst', 'ServerKeys', 'Initial', 'NewVals', 'Client', 'Statistics', 'ServerKPI', 'End']

actual_kpi = {'bi0390': 2.6666666666666665, 'bi0400': 2.1666666666666665, 'bi0410': 2.1666666666666665, 'bi0420': 3.0, 'bi0540': 3.5, 'bi0550': 2.0, 'bi0560': 4.5, 'bi0740': 676.8666666666667, 'ci5170': 0.4895833333333333, 'ci5221': 0.4953703703703703, 'ci5222': 0.5925925925925926, 'ci5223': 0.3287037037037037, 'ci6090': 0.5432858878201363, 'ci6150': 0.509258518481483, 'ci6160': 0.29725909162188174, 'ci6190': 0.41487003184014054, 'ci6200': 0.48486111111111113, 'ci7050': 0.4413936186520309, 'ci7060': 0.34928313021519547, 'cw001': 38185.82399391302, 'cw002': -3333333365.113439, 'cw003': -33123837.663934782, 'cw014': -5849999865.67902, 'cw307': -124184.66250483935, 'cw308': -189560.64034693342, 'cw309': 134.72498887004357, 'cw411': 20.4916274287561, 'cw412': 72.47279907614914, 'cw413': -5555484.365017465, 'cw414': 29.93634291944058, 'pi6120': 0.23871044786803608, 'pi6130': 0.12619997632451632, 'pi7050': 0.4413936186520309, 'pi7060': 3.003014635485288, 'pi8010': 35.658816185140694, 'pw005': -7.686143364305739e+18, 'pw010': 12203.333605038171, 'pw011': -1110772.849171003, 'pw012': -661582.3760605865, 'pw013': -52002811.49681986, 'pw014': -3.842859682884341e+18, 'pw022': -165976795.90737885, 'pw028': 573.9059381618645, 'pw036': -42250698.47353628, 'pw046': 51232925764370.5, 'pw082': 51232925781174.375, 'pw092': -142635.0193777449, 'pw097': -37071928.54123815}

def data_sizes(path):
    loads = ['Analyst-download.txt','Analyst-upload.txt','Client-download.txt','Client-upload.txt','Server-download.txt','Server-upload.txt']
    sizes = {}
    for lo in loads:
        f = open(os.path.join(path, lo), 'r')
        string = f.read()
        string = string.split('\n')
        add = 0
        for val in string:
            try:
                add += int(val)
            except:
                add += 0
        sizes[lo] = add
        
    comb_sizes = {}
    comb_sizes['AnalystStorage'] = (sizes['Analyst-download.txt'] +sizes['Analyst-upload.txt'])/10**9
    comb_sizes['ClientStorage'] = (sizes['Client-download.txt'] +sizes['Client-upload.txt'])/10**9
    comb_sizes['ServerStorage'] = (sizes['Server-download.txt'] +sizes['Server-upload.txt'])/10**9
    
    return comb_sizes
    
def KPI(path):
    f = open(os.path.join(path, 'KPI-aggregated.txt'), 'r')
    string = f.read()
    string = string.replace('"','')
    string = string.replace(' ','')
    string = string.replace('}','')
    string = string.replace('{','')
    
    lstring = string.split(',')
    
    kpi_dict = {}
    for kpi in lstring:
        kpi_val = kpi.split(':')
        kpi_dict[kpi_val[0]] = float(kpi_val[1])
    
    return kpi_dict
    
def runtimes(path, folder):
    f = open(os.path.join(path, 'times.txt'), 'r')
    string = f.read()
    string = string.split('\n')
    string = [x.split(' ') for x in string]
    string.sort(key=lambda x: int(x[0]))
    times = {}
    for entry_num in range(len(string)):
        t = 0
        entry = string[entry_num]
        time = entry[0]
        pos = entry[1]
        se = entry[2]
        if se == 'Start':
            for entry_num2 in range(len(string[(entry_num):])):
                entry2 = string[entry_num2+entry_num]
                time2 = entry2[0]
                pos2 = entry2[1]
                se2 = entry2[2]
                #print(folder, time, pos, se, time2, pos2, se2)
                if (se2 == 'End' and pos2 == pos) or (pos == 'Start' and pos2 == 'End'):
                    t = (int(time2) - int(time))/1000000000
                    break
                if pos == 'CheckTodos' and pos2 == 'End':
                    break
        #New entry or existing one
        if pos in times.keys():
            times[pos] += t
        else:
            times[pos] = t

    prog = 0
    pr = ['EncryptionClient', 'DecryptionClient', 'NewVals', 'Analyst', 'ServerKeys', 'ClientInitial', 'Aggregate', 'ServerKPI']
    for n in pr:
        try:
            prog += times[n]
        except:
            continue
    times['Network'] = times['Start']-prog
            
    cli = 0
    cl = ['EncryptionClient', 'DecryptionClient']
    for n in cl:
        try:
            cli += times[n]
        except:
            continue
    times['ClientCalcs'] = cli
    
    obfs = 0
    ob = ['DeObfuscate', 'Obfuscate']
    for n in ob:
        try:
            obfs += times[n]
        except:
            continue
    times['Obfuscation'] = obfs    
    
    times.pop('Initial')
    init = 0
    inis = ['Analyst', 'ServerKeys', 'ClientInitial']
    for n in inis:
        try:
            init += times[n]
        except:
            continue
    times['Initial'] = init   
   
    return times

def agg(old, new):
    for o in new:
        if o in old.keys():
            old[o] = (old[o] + new[o])
        else:
            old[o] = new[o]
    return old

def difference(kpi):
    ab = {}
    rel = {}
    for k in kpi:
        ab[k] = abs(kpi[k]-actual_kpi[k])
        rel[k] = ab[k] / abs(actual_kpi[k])
    return rel, ab

def max_dif(kpi, folder):
    global max_rel, max_abs, mr_folder, ma_folder, r_kpi, a_kpi
    rel, ab = difference(kpi)
    for k in rel:
        if rel[k] > max_rel:
            max_rel = rel[k]
            mr_folder = folder
            r_kpi = k
    for k in ab:
        if ab[k] > max_abs:
            max_abs = ab[k]
            ma_folder = folder
            a_kpi = k
            
def write_dict(f, dic, t):
    relevant = ['Start','Initial','NewVals','Aggregate','ServerKPI','AnalystStorage','ClientStorage','ServerStorage','Network','LoadKeys','Obfuscation','AddVals','CheckTodos','InternalCalcs','LevelZero','ClientCalcs']
    for key in dic:
        if key in relevant:
            f.write(t + ' ' + str(key) + ' ' + str(dic[key]))
            f.write('\n')

def send_times(tpath):
    f = open(os.path.join(tpath, 'times.txt'), 'r')
    string = f.read()
    string = string.split('\n')
    tme = 0
    for entry_num in range(len(string)):
        entry = string[entry_num].split(' ')
        time = entry[0]
        pos = entry[1]
        se = entry[2]
        if se == 'End' and pos in sending:
            for entry_num2 in range(len(string[entry_num-1:])):
                entry2 = string[entry_num2+entry_num].split(' ')
                time2 = entry2[0]
                pos2 = entry2[1]
                se2 = entry2[2]
                if (se2 == 'Start' and pos2 in sending) or (pos2 == 'End'):
                    #print(int(time2), int(time), int(time2)-int(time))
                    tme += (int(time2) - int(time))/1000000000
                    break
    return tme
   
def avg(dic):
    for d in dic:
        dic[d] = dic[d]/fo
    return dic

if __name__ == '__main__':

    parser.add_argument('-n', '--folder-name', type=str, help='Name of folder for the run we wish to aggregate')
    args = vars(parser.parse_args())

    if 'folder-name' not in args:
        raise ValueError('Requires a folder name from within the logs folder')
        
    path = os.path.join(lpath,args['folder-name'])
    print(path)
    sizes = {}
    kpi = {}
    times = {}
    
    for folder in range(fo):
        print('Folder',folder)
        tpath = os.path.join(path, str(folder))
        sizes_new = data_sizes(tpath)
        kpi_new = KPI(tpath)
        times_new = runtimes(tpath, folder)
        if not 'Synth' in path:
            max_dif(kpi_new, folder)
        
        sizes = agg(sizes, sizes_new)
        kpi = agg(kpi, kpi_new)
        times = agg(times, times_new)
        
        if os.path.exists(os.path.join(tpath, 'agg.txt')):
            os.remove(os.path.join(tpath, 'agg.txt'))
        else:
            print('Making new file') 
        
        f = open(os.path.join(tpath, 'agg.txt'), 'a')
        write_dict(f, sizes_new, 'Size')
        write_dict(f, times_new, 'Time')
        f.close()
    
    sizes = avg(sizes)
    kpi = avg(kpi)
    times = avg(times)
    
    
    print(kpi)
    print('-'*50)
    print(sizes)
    print('-'*50)
    print(times)
    
    if not 'Synth' in path:
        rel, ab  = difference(kpi)
        print('-'*50)
        print('Relative')
        print(rel)
        print('-'*50)
        print('Absolute')
        print(ab)
        print('-'*50)
        print('Max Rel', max_rel, mr_folder, r_kpi)
        print('Max Abs', max_abs, ma_folder, a_kpi)
        
        avg = 0
        for key in rel:
            avg += rel[key]
        print('Average Rel', avg/len(rel))
        
        avg = 0
        for key in ab:
            avg += ab[key]
        print('Average Abs', avg/len(ab))
        
    
    
    
    