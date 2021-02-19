import statistics
import numpy
import xlrd
import argparse

incorrect = ['pi7050','pi7060','pi8010','pw046','pw092']
kpis = ['pw097','pw092','pw046','pw082','pw022','pi8010','pw028','pw036','bi0540','bi0550','bi0560','pw005','pw013','pw014','cw003','cw001','cw002','cw014','pw011','pw010','pw012','cw411','cw412','cw413','cw414','cw308','cw307','cw309','pi7050','pi7060','pi6120','pi6130','bi0390','bi0400','bi0420','bi0410','ci5170','ci6090','ci6150','ci6160','ci7050','ci6190','ci6200','ci7060','bi0740','ci5221','ci5222','ci5223']
missing_kpi = ['pw067','pw054','pw072','pi8020','pi8030','pi7040','pi6140']
inaccurate = ['ci5170', 'ci6090', 'ci7050', 'cw412', 'pi6120', 'pi6130', 'pi7050', 'pi8010', 'pw011', 'pw012', 'pw022', 'pw028', 'pw092']
internal = ['+','*','-']
zeroes = ['O','[]','0',0]
false_flags = ['bi0571','bi0581','bi0621','bi0601','bi0611','bi0572']
counts = {'Min': 0, 'Max': 0, '+':0 , '*':0, '/':0, '-': 0, 'Wurzel': 0, '^': 0, 'Abs': 0}

#Returns true if x is a number
def is_number(x):
    #print('Is number')
    try:
        x = float(x)
        return True
    except:
        return False

def getFunc(string):
    #print(string)
    s = string.split(' ')
    #Get EID
    EID = s[0]
    #Get symbol
    sym = s[1]
    #Get vars into a string for db
    var = s[2:]
    func = [EID, sym, var]
    return func

def readParsed(path):
    todo = {}
    parsed = open(path, 'r')
    for line in parsed:
        #Remove newline at the end of each string
        string = line.rstrip()
        func = getFunc(string)
        todo[func[0]] = func[1:]
    parsed.close()
    return todo

def contains_var(func):
    print('Contains var')
    print(func)
    try:
        args = func[1]
    except:
        return False
    for arg in args:
        if is_eid(arg):
            return True
    return False

def is_eid(arg):
    try:
        if arg[0].islower():
            if arg[1].islower():
                if arg[2].isdigit():
                    return True
            elif arg[1].isdigit():
                return True
    except:
        return False

def check_rek(eid):
    print(eid)
    func, client, leaves, proxy, depth = 0, 0, 0, 0, 0
    symbol = eid[0]
    args = eid[1]
    if symbol == '=':
        if '[' in args[0]:
            if not args[0] in done_leaves:
                done_leaves.append(args[0])
                #Found a leaf
                leaves += 1
                depth += 1
        else:
            if not is_number(args[0]) and not args[0] in done:
                done.append(args[0])
                rek_func, rek_client, rek_leaves, rek_proxy, rek_depth = check_rek(pars[args[0]])
                func += rek_func
                client += rek_client
                leaves += rek_leaves
                proxy += rek_proxy
                depth = max(depth, rek_depth)+1
    else:
        func += 1
        counts[symbol] = 1 + counts[symbol]
        if eid not in used_funcs:
            used_funcs.append(eid)
        if symbol in internal:
            proxy += 1
        else:
            client += 1
        for arg in args:
            if not is_number(arg) and not arg in done:
                done.append(arg)
                rek_func, rek_client, rek_leaves, rek_proxy, rek_depth = check_rek(pars[arg])
                func += rek_func
                client += rek_client
                leaves += rek_leaves
                proxy += rek_proxy
                depth = max(depth, rek_depth)+1
    return func, client, leaves, proxy, depth

def rek_functions(eid):
    symbol = pars[eid][0]
    args = pars[eid][1]
    used_eid.append(eid)
    if symbol == '=':
        if '[' in args[0]:
            if not args[0] in used_eid:
                used_eid.append(eid)
        else:
            if not is_number(args[0]) and args[0] not in used_eid:
                used_eid.append(eid)
                rek_functions(args[0])
    else:
        if eid not in used_funcs2:
            used_funcs2.append(eid)
        if symbol in internal and eid not in used_proxy:
            used_proxy.append(eid)
        if symbol not in internal and eid not in used_client:
            used_client.append(eid)    
            
        for arg in args:
            if not is_number(arg) and arg not in used_eid:
                rek_functions(arg)

def count_functions(fncs):
    i = 0
    for func in fncs:
        counts[func[0]] = 1 + counts[func[0]]
        i += 1
        print(func[0], i)
        print(counts)
    print(counts)

def get_stats():
    global pars
    pars = readParsed('parsed2 - Copy.txt')
    global used_funcs
    used_funcs = []
    kpi_stats = {}
    for kpi in kpis:
        print('-'*50)
        global done, done_leaves
        done = []
        done_leaves = []
        func, client, leaves, proxy, depth = check_rek(pars[kpi])
        kpi_stats[kpi] = [func, client, proxy, leaves, depth]
    print('X'*50)
    print('Kpi: Number of operations, Number of operations on proxy, Number of operations on client Inputs from client')
    funcs = []
    clients = []
    leaves = []
    proxies = []
    depths = []
    for kpi in kpi_stats:
        print(kpi, kpi_stats[kpi])
        funcs.append(kpi_stats[kpi][0])
        clients.append(kpi_stats[kpi][1])
        proxies.append(kpi_stats[kpi][2])
        leaves.append(kpi_stats[kpi][3])
        depths.append(kpi_stats[kpi][4])
    print(counts)
    print('-'*50)
    print('Operations')
    print('Mean', statistics.fmean(funcs), 'Max', max(funcs), 'Min', min(funcs), 'Median', statistics.median(funcs))
    print('Proxy Operations')
    print('Mean', statistics.fmean(proxies), 'Max', max(proxies), 'Min', min(proxies), 'Median', statistics.median(proxies))
    print('Client Operations')
    print('Mean', statistics.fmean(clients), 'Max', max(clients), 'Min', min(clients), 'Median', statistics.median(clients))
    print('Inputs')
    print('Mean', statistics.fmean(leaves), 'Max', max(leaves), 'Min', min(leaves), 'Median', statistics.median(leaves))
    print('Depths')
    print('Mean', statistics.fmean(depths), 'Max', max(depths), 'Min', min(depths), 'Median', statistics.median(depths))
    print('Inputs which are KPI')
    print(funcs.count(0))
    print('Total number of funcs used based on function formula')
    print(len(used_funcs))
    #print(used_funcs)

def get_leaves(eid):
    #print(eid)
    leaves = []
    args = pars[eid][1]
    for arg in args:
        if '[' in arg and not arg in done_leaves:
            #print('Found leaf', eid, args)
            done_leaves.append(arg)
            leaves.append(eid)
        else:
            if not arg in done and not is_number(arg) and not '[' in arg:
                rek_leaves = get_leaves(arg)
                leaves = leaves + rek_leaves
    return leaves

def get_inputs():
    vals = []
    client = 1
    sh = xlrd.open_workbook(r'./ClientData.xlsx').sheets()
    for sh in xlrd.open_workbook(r'./ClientData.xlsx').sheets():
        for row in range(sh.nrows):
            #print('Row:', row)
            #Get EID
            EID = sh.cell(row,0).value
            vals.append(EID)
    return vals   

def find_missing_inputs(kpi):
    global pars
    pars = readParsed('parsed2.txt')
    leaves = []
    for miss in kpi:
        leaves = leaves + get_leaves(miss)
    inputs = get_inputs()
    missing = []
    for leaf in leaves:
        if not leaf in inputs:
            missing.append(leaf)
    print(missing)
    print(len(missing))
    if not len(missing) != len(set(missing)):
        print('No duplicates')
    for ms in missing:
        print(ms, pars[ms][1])

def get_all_eid(path):
    todo = []
    parsed = open(path, 'r')
    for line in parsed:
        #Remove newline at the end of each string
        string = line.rstrip()
        func = getFunc(string)
        todo.append(func[0])
    parsed.close()
    return todo

def purge_parsed(unused_eid):
    with open("parsed2.txt", "r") as f:
        lines = f.readlines()
    with open("parsed2 - purged.txt", "w") as f:
        for line in lines:
            string = line.rstrip()
            func = getFunc(string)
            if func[0] not in unused_eid:
                f.write(line)

def find_unused_functions():
    global used_eid
    used_eid = []
    global done, done_leaves
    done = []
    done_leaves = []
    global used_funcs2, used_proxy, used_client
    used_funcs2 = []
    used_proxy = []
    used_client = []
    for kpi in kpis:
        rek_functions(kpi)
    #Remove duplicates
    used_eid = list(dict.fromkeys(used_eid))
    used_funcs2 = list(dict.fromkeys(used_funcs2))
    
    print('Total number of used eid')
    print(len(used_eid))
    print('Total number of used functions based on eid')
    print(len(used_funcs2))
    all_eid = get_all_eid('parsed2.txt')
    print('Total number of used functions proxy')
    print(len(used_proxy))
    all_eid = get_all_eid('parsed2.txt')
    print('Total number of used functions client')
    print(len(used_client))
    all_eid = get_all_eid('parsed2.txt')
    
    unused_eid = [eid for eid in all_eid if eid not in used_eid]
    print('Unused functions')
    print(unused_eid)
    print(len(unused_eid))
    
    inputs = get_inputs()
    unused_inputs = [eid for eid in inputs if eid not in used_eid]
    print('Unused inputs')
    print(unused_inputs)
    print(len(unused_inputs))
    
    #print(used_eid)
    
    
    #purge_parsed(unused_eid)

def find_incorrect(kpi):
    leaves = get_leaves('pw046')
    print(leaves)
    inputs = get_inputs()
    for leaf in leaves:
        if not leaf in inputs:
            print(leaf)

def min_zero_rek(eid):
    if is_number(eid):
        return False
    symbol = pars[eid][0]
    args = pars[eid][1]
    print(eid, symbol, args)
    if symbol == '=':
        if '[' in args[0]:
            print('Returning False')
            return False
        elif args[0] == 0 or args[0] == '0':
            print('Returning False')
            return True
        else:
            return inaccurate_rek(args[0])
    else:
        ret = False
        for arg in args:
            if inaccurate_rek(arg):
                ret = True
    return ret
 
def get_zero_inputs():
    vals = []
    client = 1
    sh = xlrd.open_workbook(r'./ClientData.xlsx').sheets()
    for sh in xlrd.open_workbook(r'./ClientData.xlsx').sheets():
        for row in range(sh.nrows):
            #print('Row:', row)
            #Get EID
            zero = False
            for i in range(1,6):
                if sh.cell(row,i).value in zeroes:
                    zero = True
            if zero:
                EID = sh.cell(row,0).value
                vals.append(EID)
    return vals 

def check_occurrence(of_this, in_this):
    for ele in of_this:
        if ele in in_this and not ele in false_flags:
            print(ele)
            return True
    return False
    
def all_occurrence(of_this, in_this):
    lst = []
    for ele in of_this:
        if ele in in_this and not ele in false_flags:
            lst.append(ele)
    return lst

def inaccurate_funcs():
    z_inputs = get_zero_inputs()
    lst = []
    inaccurate = []
    for kpi in inaccurate:
        print('-'*50)
        print(kpi)
        leaves = get_leaves(kpi)
        if check_occurrence(leaves, z_inputs):
            lst.append(kpi)
    print(lst)
    
def inaccurate_func(kpi):
    z_inputs = get_zero_inputs()
    lst = []
    leaves = get_leaves(kpi)
    ret = all_occurrence(leaves, z_inputs)
    print(ret)

if __name__ == "__main__":
    parser = argparse.ArgumentParser('Graph Stats')
    parser.add_argument('-s', '--single', type=str, help='If we want stats for a single KPI')
    parsed_args, other_args = parser.parse_known_args()
    args = vars(parsed_args)
    print(args, other_args)

    if args['single']:
        kpis = [str(args['single'])]

    print('TODO stats for single kpi over cmd') #Set kpi = ['eid'] over parseargs
    global pars
    pars = readParsed('parsed2.txt')
    global done, done_leaves
    done = []
    done_leaves = []
    get_stats()
    #find_missing_inputs(kpis)
    #find_unused_functions()
    #print('Number of KPI')
    #print(len(kpis))
    #find_incorrect(incorrect)
    #inaccurate_func('ci6090')
    