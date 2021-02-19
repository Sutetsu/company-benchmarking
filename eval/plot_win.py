#!/usr/bin/env python

import subprocess
import pathlib
import time
import datetime
import os
import shutil
import sys
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as lin
import matplotlib.patches as ptc
import pandas as pd

lpath = os.path.join(pathlib.Path().absolute(), 'log')

fo = 30

#dist = 2.262 #95%
dist = 1.833 #99%

def get_aggs(pth):
    apath = os.path.join(lpath, pth)
    vals = {}
    for folder in range(fo):
        print('Folder',folder)
        tpath = os.path.join(apath, str(folder))
        f = open(os.path.join(tpath, 'agg.txt'), 'r')
        string = f.read()
        string = string.split('\n')
        entries = [x.split(' ') for x in string]
        for entry in entries:
            if entry == ['']:
                continue
            elif entry[1] in vals.keys():
                vals[entry[1]].append(float(entry[2]))
            else:
                vals[entry[1]] = [float(entry[2])]
    return vals
            

def get_avg_conf(pth):
    avgs = {}
    conf = {}
    vals = get_aggs(pth)
    
    for val in vals:
        avgs[val] = sum(vals[val])/len(vals[val])
    
    for val in vals:
        avg = avgs[val]
        sqr = [(x-avg)**2 for x in vals[val]]
        dev = math.sqrt(sum(sqr)/len(sqr))
        conf[val] = (dev/math.sqrt(30))*dist
    print(avgs)
    print(conf)
    return avgs, conf

def build_list(key, l1, l2, l3, l4):
    lsts = [l1, l2, l3, l4]
    ret = []
    for l in lsts:
        try:
            ret.append(l[key])
        except:
            ret.append(0)
    print(ret)
    return ret
    
    
def build_funcs(key, l1, l2, l3, l4, l5, l6, l7, l8, l9, l10):
    lsts = [l1, l2, l3, l4, l5, l6, l7, l8, l9, l10]
    ret = []
    for l in lsts:
        if key == 'Storage':
            tot = 0
            for k in l.keys():
                if 'Storage' in k:
                    tot += l[k]
            ret.append(tot)
        else:
            ret.append(l[key])
    print(ret)
    return ret
    
def build_cli(key, l1, l2, l3, l4, l5):
    lsts = [l1, l2, l3, l4, l5]
    ret = []
    for l in lsts:
        if key == 'Storage':
            tot = 0
            for k in l.keys():
                if 'Storage' in k:
                    tot += l[k]
            ret.append(tot)
        else:
            ret.append(l[key])
    print(ret)
    return ret

def time_storage():
    fig, tm = plt.subplots()
    strg = tm.twinx()
    fig.subplots_adjust(left=0.1, right=0.9, top=0.92, bottom=0.2)
    
    clear, clear_conf = get_avg_conf('Clear-Obfus')
    fhe_obf, fhe_obf_conf = get_avg_conf('FHE-Obfus')
    fhe, fhe_conf = get_avg_conf('FHE-Obfus-Zero')
    fhe_zer, fhe_zer_conf = get_avg_conf('FHE-Zero')

    # width of the bars
    barWidth = 0.3
    x = np.arange(4)
     
    '''STORAGE'''
    # Analyst
    ana = build_list('AnalystStorage', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    anac = build_list('AnalystStorage', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
     
    # Client
    cli = build_list('ClientStorage', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    clic = build_list('ClientStorage', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
     
    # Server
    ser = build_list('ServerStorage', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    serc = build_list('ServeeStorage', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
     
     
    '''TIMES'''
    # Choose the height of the blue bars
    new = build_list('NewVals', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    newc = build_list('NewVals', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
     
    # Choose the height of the blue bars
    ini = build_list('Initial', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    inic = build_list('Initial', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
     
    # Choose the height of the blue bars
    agg = build_list('Aggregate', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    aggc = build_list('Aggregate', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
     
    # Choose the height of the blue bars
    net = build_list('Network', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    netc = build_list('Network', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
     
    # Choose the height of the blue bars
    kpi = build_list('ServerKPI', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    kpic = build_list('ServerKPI', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
    
    
    

    
    #x position of Time
    r1 = np.arange(len(new))
    
    #x position of Storage
    r2 = [z + barWidth for z in r1]
    r3 = [z + barWidth for z in r1]
     
     
    #bottom = [bars1[j] +bars2[j] +bars3[j] for j in range(len(bars1))]
    # Create time
    tm.bar(r1, agg, width = barWidth, color = 'cyan', edgecolor = 'black', yerr=aggc, capsize=5, label='Aggregation')
    tm.bar(r1, ini, width = barWidth, color = 'slateblue', edgecolor = 'black', yerr=inic, capsize=5, label='Initialization', bottom=agg)
    tm.bar(r1, kpi, width = barWidth, color = 'deepskyblue', edgecolor = 'black', yerr=kpic, capsize=7, label='KPI communication', bottom = [agg[j] +ini[j] for j in range(len(new))])
    tm.bar(r1, net, width = barWidth, color = 'navy', edgecolor = 'black', yerr=netc, capsize=5, label='Network time', bottom = [agg[j] +ini[j]+kpi[j] for j in range(len(new))])
    tm.bar(r1, new, width = barWidth, color = 'blue', edgecolor = 'black', yerr=newc, capsize=5, label='Adding new values', bottom = [agg[j] +ini[j]+kpi[j]+net[j] for j in range(len(new))])
     
    # Create storage
    strg.bar(r2, ana, width = barWidth, color = 'red', edgecolor = 'black', yerr=anac, capsize=5, label='Analyst Data')
    strg.bar(r2, ser, width = barWidth, color = 'brown', edgecolor = 'black', yerr=serc, capsize=5, label='Server Data', bottom=ana)
    strg.bar(r2, cli, width = barWidth, color = 'orangered', edgecolor = 'black', yerr=clic, capsize=5, label='Client Data', bottom = [ana[j] +ser[j] for j in range(len(new))])
     
    # general layout
    tm.set_xticks([r + (barWidth/2) for r in range(len(new))])
    tm.set_xticklabels(['Obf. FHE', 'Obf. Deleveled FHE', 'Deleveled FHE', 'Cleartext'])
    #tm.set_xlabel('Operation')
    
    tm.set_ylabel('Time [s]', color='blue')
    tm.tick_params(axis='y', labelcolor='blue')
    #tm.set_yscale('log')
    
    strg.set_ylabel('Total message sizes [GB]', color='tomato')
    strg.tick_params(axis='y', labelcolor='tomato')
    #strg.set_yscale('log')
    
    
    fig.legend(borderpad=0.3, handletextpad=0.4, columnspacing=1.3, ncol=4)
    
    #plt.legend()
    fig.savefig(f'timestorage.pdf', bbox_inches='tight')
     
    # Show graphic
    #fig.show()

def newvals():

    clear, clear_conf = get_avg_conf('Clear-Obfus')
    fhe_obf, fhe_obf_conf = get_avg_conf('FHE-Obfus')
    fhe, fhe_conf = get_avg_conf('FHE-Obfus-Zero')
    fhe_zer, fhe_zer_conf = get_avg_conf('FHE-Zero')

    # width of the bars
    barWidth = 0.3
    x = np.arange(4)
     
    # Load Keys
    loa = build_list('LoadKeys', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars1)
    loac = build_list('LoadKeys', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
    
    # Add Vals
    add = build_list('AddVals', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars2)
    addc = build_list('AddVals', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
    
    # Check Todos
    tod = build_list('CheckTodos', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars3)
    todc = build_list('CheckTodos', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
    
    # Level Zero
    zer = build_list('LevelZero', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars3)
    zerc = build_list('LevelZero', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
    
    # Obfuscation
    obf = build_list('Obfuscation', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars3)
    obfc = build_list('Obfuscation', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
    
    # Internal Calcs
    cal = build_list('InternalCalcs', fhe_obf, fhe, fhe_zer, clear)
    # Choose the height of the error bars (bars3)
    calc = build_list('InternalCalcs', fhe_obf_conf, fhe_conf, fhe_zer_conf, clear_conf)
    

    #x position of Time
    r1 = np.arange(len(loa))
     
    # Create time
    plt.bar(r1, loa, width = barWidth, color = 'turquoise', edgecolor = 'black', yerr=loac, capsize=5, label='Loading Keys')
    plt.bar(r1, add, width = barWidth, color = 'lightseagreen', edgecolor = 'black', yerr=addc, capsize=5, label='Adding Values', bottom = loa)
    plt.bar(r1, tod, width = barWidth, color = 'teal', edgecolor = 'black', yerr=todc, capsize=5, label='Checking TODOs', bottom = [loa[j] +add[j] for j in range(len(loa))])
    plt.bar(r1, zer, width = barWidth, color = 'deepskyblue', edgecolor = 'black', yerr=zerc, capsize=5, label='Deleveling', bottom = [loa[j] +add[j] +tod[j] for j in range(len(loa))])
    plt.bar(r1, obf, width = barWidth, color = 'dodgerblue', edgecolor = 'black', yerr=obfc, capsize=5, label='Obfuscation', bottom = [loa[j] +add[j] +tod[j]+zer[j] for j in range(len(loa))])
    plt.bar(r1, cal, width = barWidth, color = 'cornflowerblue', edgecolor = 'black', yerr=calc, capsize=5, label='Internal Calc.', bottom = [loa[j] +add[j] +tod[j]+zer[j]+obf[j] for j in range(len(loa))])

    # general layout
    plt.xticks([r for r in range(len(loa))], ['Obf. FHE', 'Obf. Deleveled FHE', 'Deleveled FHE', 'Cleartext'])
    plt.xlabel('Operation')
    
    plt.ylabel('Time [s]', color='blue')
    plt.yticks(color = 'blue')
    
    plt.legend()
    plt.savefig(f'newvals.pdf', bbox_inches='tight')
     
    # Show graphic
    #plt.show()
    
def functionscaling():

    fig, tm = plt.subplots()
    strg = tm.twinx()
    
    x1 = [10,20,30,40,50,60,70,80,90,100]

    # Add
    a10, t = get_avg_conf('SynthAdd10')
    a20, t = get_avg_conf('SynthAdd20')
    a30, t = get_avg_conf('SynthAdd30')
    a40, t = get_avg_conf('SynthAdd40')
    a50, t = get_avg_conf('SynthAdd50')
    a60, t = get_avg_conf('SynthAdd60')
    a70, t = get_avg_conf('SynthAdd70')
    a80, t = get_avg_conf('SynthAdd80')
    a90, t = get_avg_conf('SynthAdd90')
    a100, t = get_avg_conf('SynthAdd100')
    
    add = build_funcs('Start', a10,a20,a30,a40,a50,a60,a70,a80,a90,a100)
    addstore = build_funcs('Storage', a10,a20,a30,a40,a50,a60,a70,a80,a90,a100)
    strg.plot(x1, add, marker='', color='red', linewidth=2, linestyle='-', label="Addition Storage")
    tm.plot(x1, add, marker='x', color='fuchsia', linewidth=2, linestyle='', label="Addition Time")
    
    # Min
    m10, t = get_avg_conf('SynthMin10')
    m20, t = get_avg_conf('SynthMin20')
    m30, t = get_avg_conf('SynthMin30')
    m40, t = get_avg_conf('SynthMin40')
    m50, t = get_avg_conf('SynthMin50')
    m60, t = get_avg_conf('SynthMin60')
    m70, t = get_avg_conf('SynthMin70')
    m80, t = get_avg_conf('SynthMin80')
    m90, t = get_avg_conf('SynthMin90')
    m100, t = get_avg_conf('SynthMin100')
    
    add = build_funcs('Start', m10,m20,m30,m40,m50,m60,m70,m80,m90,m100)
    addstore = build_funcs('Storage', m10,m20,m30,m40,m50,m60,m70,m80,m90,m100)
    strg.plot(x1, add, marker='', color='darkturquoise', linewidth=2, linestyle='-', label="Minimum Storage")
    tm.plot(x1, add, marker='x', color='dodgerblue', linewidth=2, linestyle='', label="Minimum Time")
    
    # Root
    r10, t = get_avg_conf('SynthAbs10')
    r20, t = get_avg_conf('SynthAbs20')
    r30, t = get_avg_conf('SynthAbs30')
    r40, t = get_avg_conf('SynthAbs40')
    r50, t = get_avg_conf('SynthAbs50')
    r60, t = get_avg_conf('SynthAbs60')
    r70, t = get_avg_conf('SynthAbs70')
    r80, t = get_avg_conf('SynthAbs80')
    r90, t = get_avg_conf('SynthAbs90')
    r100, t = get_avg_conf('SynthAbs100')
    
    add = build_funcs('Start', r10,r20,r30,r40,r50,r60,r70,r80,r90,r100)
    addstore = build_funcs('Storage', m10,m20,m30,m40,m50,m60,m70,m80,m90,m100)
    strg.plot(x1, add, marker='', color='black', linewidth=2, linestyle='-', label="Abs Storage")
    tm.plot(x1, add, marker='x', color='brown', linewidth=2, linestyle='', label="Abs Time")
    
    #Labels
    tm.set_xlabel('Operations')
    strg.set_ylabel('Total message sizes [GB]')
    tm.set_ylabel('Time [s]')
    #strg.set_yscale('log')
    
    # Set a title of the current axes.
    #fig.title('Two or more lines on same plot with suitable legends ')
    # show a legend on the plot
    fig.legend(borderpad=0.3, handletextpad=0.4, columnspacing=1.3, ncol=3)
    fig.savefig(f'multifunction.pdf', bbox_inches='tight')
    # Display a figure.
    #fig.show()

def multiclient():
    #steps = [10,20,30,40]
    steps = [1,2,3,4,5]
    
    c1, c1s = get_avg_conf('FHE-1Client')
    c2, c2s = get_avg_conf('FHE-2Client')
    c3, c3s = get_avg_conf('FHE-3Client')
    c4, c4s = get_avg_conf('FHE-4Client')
    c5, c5s = get_avg_conf('FHE-5Client')
    barWidth = 0.5
    
    fig, storage = plt.subplots()
    time = storage.twinx()  # instantiate a second axes that shares the same x-axis

    loa = build_cli('Start', c1,c2,c3,c4,c5)
    # Choose the height of the error bars (bars1)
    loac = build_cli('Start', c1s,c2s,c3s,c4s,c5s)


    # line 1 points
    x1 = steps
    y1 = [600,800,1200,1700,2000]
    # plotting the line 1 points 

    # Choose the height of the blue bars
    bars1 = steps
    # Choose the height of the error bars (bars1)
    yer1 = [0.5, 0.4, 0.5, 0.2,0.3,0.2] 
    
    # Choose the height of the blue bars
    bars2 = steps
    # Choose the height of the error bars (bars1)
    yer2 = [0.5, 0.4, 0.5, 0.2,0.3,0.2] 
    
    storage.bar(steps, loa, width = barWidth, color = 'deepskyblue', edgecolor = 'black', yerr=loac, capsize=7, label='sorgho')
    time.plot(x1, loa, marker='', color='orange', linewidth=2, linestyle='-', label="toto")
     
    
    
    
    #Labels
    storage.set_xlabel('Clients')
    storage.set_ylabel('Total message sizes [GB]', color='deepskyblue')
    time.set_ylabel('Time [s]', color='orange')
    storage.tick_params(axis='y', labelcolor='deepskyblue')
    time.tick_params(axis='y', labelcolor='orange')

    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.savefig(f'multiclient.pdf', bbox_inches='tight')
    #plt.show()

if __name__ == '__main__':
    print('Which graphic would you like to generate?')
    print('1: Overall time and message sizes')
    print('2: Times of the newvals function')
    print('3: Scaling for multiple values')
    print('4: Scaling for multiple functions')
    temp = input('Method: ')
    
    #time_storage()
    #newvals()
    #functionscaling()
    #multiclient()