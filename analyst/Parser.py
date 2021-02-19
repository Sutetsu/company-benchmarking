import sys
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
import xlrd
import compiler

reverseColours=False
upwards=False
labels=True
letters = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
functions = ['MIN', 'MAX', 'WURZEL', '^', '+', '-', '*', '/', '|']
doubleFunctions = ['^', '+', '-', '*', '/']


nest = 0


path= r'./KennKunststoff_v83.xlsm'

def do_nothing():
    return 0

def functionsInString(String):
    func = []
    if 'WURZEL' in String:
        func.append('r')
    if 'MAX' in String:
        func.append('M')
    if 'MIN' in String:
        func.append('M')
    if '^' in String:
        func.append('p')
    if '|' in String:
        func.append('A')
    if '/' in String:
        func.append('d')
    if '+' in String:
        func.append('a')
    if '-' in String:
        func.append('s')
    if '*' in String:
        func.append('m')
    return func
    
def get_symbol(String):
    func = []
    if 'WURZEL' in String:
        return 'Wurzel'
    if 'MAX' in String:
        return 'Max'
    if 'MIN' in String:
        return 'Min'
    if '^' in String:
        return '^'
    if '|' in String:
        return 'Abs'
    if '/' in String:
        return '/'
    if '+' in String:
        return '+'
    if '-' in String:
        return '-'
    if '*' in String:
        return '*'
    return '='

#Transforms a list into a string, with spaces between each entry
def listToString(lst):
    string = ""    
    for e in lst:  
        string += e
        string += ' '
    string = string[:-1]
    return string

#Returns 1 if a given string contains any of the strings in a given check list
def containsAny(string, check):
    #Catch for constants
    if type(string) == float:
        string = str(string)
    for c in check:
        if c in string: 
            return 1
    return 0

'''
def findNested(string):
    bracket = 1
    tmp = i+1
    while bracket > 0:
        #print(tmp, bracket)
        if func[tmp] == '(':
            bracket += 1
        if func[tmp] == ')':
            bracket -= 1
        tmp += 1
'''

#TODO
def parseMinMax(func, EID, minmax, sym):
    print('Parsing MINMAX', func, EID, minmax)
    sub_list = func.split(';')
    var_list = []
    for f in sub_list:
        new_id = create_ID(EID)
        parse(f, new_id)
        var_list.append(new_id)
    if minmax == 'MAX':
        sym = 'Max'
    else:
        sym = 'Min'
    
    varString = listToString(var_list)
    parseFile.write(EID + ' ' + sym + ' ' + varString + '\n')
    
    return 0
    
def parseAbs(func, EID):
    print(func, EID)
    new_id = create_ID(EID)
    print('Adding function ' + EID + ' Abs ' + new_id)
    parseFile.write(EID + ' Abs ' + new_id + '\n')
    parse(func, new_id)
    return 0
    
def parseWurzel(func, EID):
    print(func, EID)
    new_id = create_ID(EID)
    print('Adding function ' + EID + ' Wurzel ' + new_id)
    parseFile.write(EID + ' Wurzel ' + new_id + '\n')
    parse(func, new_id)
    return 0
    
def create_ID(EID):
    global nest 
    nest = nest+1
    new_id = "fu" + str(nest)
    #print(new_id)
    return new_id
    
def parse_exp(func, EID):
    #print('before func', func)
    #Get position of ^
    pos = func.find('^')
    
    #Get vars on left and right
    start, end = get_next_vars(func, pos)
    
    #Turn into rekursive function
    new_id = create_ID(EID)       
    new_func = func[start:end]
    #Replace in old function
    func = func[:start] + new_id + func[end:]
    #print('OLDFUNC:', func, 'NEWFUNC:', new_func)
    parse(new_func, new_id)   
    return func
    
def parse_multdiv(func, EID):
    #Get position of symbol
    multpos = func.find('*')
    divpos = func.find('/')
    if divpos == -1 or multpos < divpos and not multpos == -1:
        pos = multpos
    else:
        pos = divpos
        
    #Get vars on left and right
    start, end = get_next_vars(func, pos)
    
    #Turn into rekursive function
    new_id = create_ID(EID)       
    new_func = func[start:end]
    #Replace in old function
    func = func[:start] + new_id + func[end:]
    print('OLDFUNC:', func, 'NEWFUNC:', new_func)
    parse(new_func, new_id)
    return func
    
def parse_addsub(func, EID):
    #Get position of first symbol
    if '(' in func:
        func = take_out_brackets(func, EID)
    addpos = func.find('+')
    subpos = func.find('-')
    if subpos == -1 or addpos < subpos and not addpos == -1:
        pos = addpos
    else:
        pos = subpos
        
    #Get vars on left and right
    start, end = get_next_vars(func, pos)
    
    #Turn into rekursive function
    new_id = create_ID(EID)       
    new_func = func[start:end]
    #Replace in old function
    func = func[:start] + new_id + func[end:]
    #print('OLDFUNC:', func, 'NEWFUNC:', new_func)
    parse(new_func, new_id)
    return func

#Finds brackets in a given func, replaces them with a new EID, and starts a new parsing job for the function in the bracket
def take_out_minmax(func, EID):
    i = 0
    while i < len(func):
            #Check the i'th symbol
            if func[i] == '{':
                #If we find a bracket, we will replace it with and treat it as a new function
                #print('Found bracket')
                start = i
                try:
                    #Looking for closing bracket
                    brackets = 1
                    j = i+1
                    while brackets > 0:
                        if func[j] == '}':
                            brackets = brackets-1
                        if func[j] == '{':
                            brackets = brackets+1
                        j = j+1
                    end = j-1
                    #Treat the found bracket as a new function
                    new_id = create_ID(EID)
                    new_func = func[start+1:end]
                    
                    #Check if we found Max or min
                    if func[i-1] == 'x':
                        sym = 'Max'
                    else:
                        sym = 'Min'
                    
                    parseMinMax(new_func, new_id, func[i-3:i], sym)
                    
                    #Replace bracket in our function
                    func = func[:i-3] + new_id + func[end+1:]
                    
                    #Reset to start
                    i = 0
                    
                    #print('New Function')
                    #print(func)
                    #varList.append(new_id)
                    
                except:
                    print('Something went wrong while checking brackets')
                    print('Most likely a closing bracket is missing for EID', EID)
                    
            i = i+1
    return func

def take_out_abs(func, EID):
    i = 0
    while i < len(func):
        if func[i] == '|':
            #If we find a abs, we will replace it with and treat it as a new function7
            start = i+1
            for j in range(len(func[start:])):
                if func[j+start] == '|':
                    end = j+start-1
                    break
                
            #Treat the found abs as a new function
            new_id = create_ID(EID)
            new_func = func[start:end+1]
            #print('NEW FUNC', new_func)
            parseAbs(new_func, new_id)
                    
            #Replace abs in our function
            func = func[:i] + new_id + func[end+2:]
            #print('OLD FUNC', func)
            
            #Reset to start
            i = 0
                    
        i = i+1
    return func


#Finds brackets in a given func, replaces them with a new EID, and starts a new parsing job for the function in the bracket
def take_out_brackets(func, EID):
    print('Looking for brackets', func, EID)
    i = 0
    func_end = len(func)
    while i < len(func):
        if func[i] == '(':
            #If we find a bracket, we will replace it with and treat it as a new function
            start = i
            #Looking for closing bracket
            brackets = 1
            j = i+1
            while brackets > 0:
                if func[j] == ')':
                    brackets = brackets-1
                if func[j] == '(':
                    brackets = brackets+1
                j = j+1
            end = j-1
            #Treat the found bracket as a new function
            new_id = create_ID(EID)
            
            new_func = func[start+1:end]
            
            #Catch Wurzel
            if func[i-6:i] == 'WURZEL':
                print('Found Wurzel')
                parseWurzel(new_func, new_id)
                #Replace bracket in our function
                func = func[:i-6] + new_id + func[end+1:]
            else:
                print('____Parsing new func', new_func, 'Start, End:', start, end)
                parse(new_func, new_id)
                #Replace bracket in our function
                #print(':i', func[:i], 'new', new_id, 'end', func[end+1:])
                func = func[:i] + new_id + func[end+1:]
            
            i = len(func[:i]) + len(new_id)
            #print(i)
        i = i+1
    #print('Returning from brackets with ', func)
    return func
    
def count_symbols(func):
    amount = 0
    amount = amount + func.count('WURZEL')
    amount = amount + func.count('MAX')
    amount = amount + func.count('MIN')
    amount = amount + func.count('^')
    amount = amount + func.count('|')
    amount = amount + func.count('/')
    amount = amount + func.count('+')
    amount = amount + func.count('-')
    amount = amount + func.count('*')
    return amount
    
#Returns the start of a var on the left, and the end of a var on the right of a given position
def get_next_vars(func, pos):
    start = 0
    end = len(func)-1
    
    #Find start of left variable by reversing string
    for index, char in enumerate(reversed(func[:pos])):
        #print(index+1, len(func[:pos]))
        if char in functions:
            start = pos-index
            break
        #Check if next index would be outside of string
        elif index+1 == len(func[:pos]):
            #print('Reached start of string, breaking')
            start = 0
            break    
            
    #Find end of right variable
    print(func[pos+1:])
    for index, char in enumerate(func[pos+1:]):
        #print('Index', index, 'Char', char, 'Len', len(func[pos+1:]))
        if char in functions:
            #print('Found rightmost', index, char)
            end = index+pos+1
            break
        #Check if the current index is the last one
        elif index+1 == len(func[pos+1:]):
            #print('Reached end of string, breaking')
            end = index+pos+2
            break
    
    return start, end
        
def get_vars(func):
    varList = []
    varNumber = 0
    i = 0
    while i < len(func):
        #Catch numbers
        if func[i].isdigit():
            tmp = i+1
            number = func[i]
            while tmp < len(func):
                #Check for multiple digits or float
                if func[tmp].isdigit() or func[tmp] == '.':
                    number = number + func[tmp]
                    i = tmp
                else:
                    i = tmp-1
                    tmp = len(func)
                tmp += 1
            #print('Appending number', number)
            varList.append(number)
            varNumber += 1
        #Catch variables, relies on the structure of two letters and then an arbitrary amount of numbers
        #TODO mark variables if #, <, or [
        try:
            if func[i] in letters and func[i+1] in letters:
                #print('Found letters at', i)
                tmp = i+2
                while tmp <= len(func):
                    #print(tmp)
                    if tmp == len(func) or not func[tmp].isdigit():
                        #print('Not digit:',func[tmp], tmp)
                        #print('I', i)
                        varList.append(func[i:tmp])
                        varNumber += 1
                        i = tmp-1
                        break
                    else:
                        #print('Digit:',func[tmp], tmp)
                        do_nothing()
                    tmp += 1
                #i = tmp
        #Catches when the variable is at the very end of the string
        except:
            varList.append(func[i:tmp])
            varNumber += 1
            break
        i = i+1
    #print('Vars:',varList, varNumber, func)
    return varList, varNumber
            

def parse(func, EID):

    print('Parsing', func, 'with EID', EID)
    
    #Ignore special function
    if 'SpNetz' in str(func) or EID == 'Eingabe_ID':
        return 0
        
    #Replace , with .
    if not func == 1.0:
        if ',' in func:
            print('Replacing')
            func = func.replace(',','.')
    
    #Catch hardcoded and initial variables
    if not containsAny(func, letters):
        print('Initial or hardcoded variable. Adding to functions with =')
        print('Function:', func)
        if containsAny(func, doubleFunctions) and not func == 1.0:
            #Python format
            if '^' in func:
                print('Replacing')
                func = func.replace('^','**')
                
            #Security risk, but the functions should come from an internal place anyway
            print('Evaluating', func)
            func = eval(func)
        parseFile.write(EID + ' = ' + str(func) + '\n')
        return 0
    
    #Catch redirecting variables
    if not containsAny(func, functions):
        print('Initial or hardcoded variable. Adding to functions with =')
        print('Function:', func)
        #Take out brackets eg. <ci8033>
        if '<' in func or '[' in func:
            func = func[1:len(func)-1]
        parseFile.write(EID + ' = ' + str(func) + '\n')
        return 0
    
    #Assert as string so we don't trip over kh1
    func = str(func)
    
    #Reduce function to either one symbol or multiple additions/subtractions or multiplications
    funcs = functionsInString(func)
    while not (count_symbols(func) <= 1 or funcs == ['m'] or funcs == ['s'] or funcs == ['a']):
        #Clean function to only consist of values, EIDs, and symbols
        if 'MAX' in func or 'MIN' in func:
            func = take_out_minmax(func, EID)
            if count_symbols(func) == 1:
                break
        if '|' in func:
            func = take_out_abs(func, EID)
            if count_symbols(func) == 1:
                break
        if '(' in func:
            func = take_out_brackets(func, EID) 
            if count_symbols(func) == 1:
                break


        #Catch hardcoded and initial variables after we took out brackets
        if not containsAny(func, functions):
            print('Hardcoded variable. Adding to functions with =')
            print('Function:', func)
            parseFile.write(EID + ' = ' + func + '\n')
            return 0
            
        symbol = ''
        varList = []
        
        #Function should only consist of vars, +,*,-,/, and ^ here
    


        
        #Do exponents first
        if '^' in func:
            #print('Found exponent')
            func = parse_exp(func, EID)
            if count_symbols(func) == 1:
                break
            
        elif '*' in func or '/' in func:
            #print('Found mult/div')
            func = parse_multdiv(func, EID)
            if count_symbols(func) == 1:
                break
            
            
        elif '+' in func and '-' in func:
            #print('Found both add and sub')
            func = parse_addsub(func, EID)
            if count_symbols(func) == 1:
                break
            
            
        else:
            #print('---------------------------------------------')
            #print('Updating function information')
            #print('Function:', func, 'Old operators:', funcs, 'New operators:', functionsInString(func))
            funcs = functionsInString(func)
    
    #print(symbols)
    
    print('Adding function', func, 'to list')
    
    #Should only be one symbol
    symbol = get_symbol(func)
    
    var_list, var_number = get_vars(func)
    
    
    print('ID:', EID, 'Symbol', symbol, 'Variable List:', var_list, 'Function:', func)
    print('------------')
    varString = listToString(var_list)
    parseFile.write(EID + ' ' + symbol + ' ' + varString + '\n')
    
    


print('This parser still has some bugs. The parsed file for the IKV example has been manually corrected, and would be overwritten if this is executed. Press enter if you want to execute enyway.')
inp = input()

parseFile = open('parsed2.txt', 'w')

sh = xlrd.open_workbook(path).sheets()
#row = sys.argv[1]

nest = 0

"""
func = 'fu1^fu8/20'
pos = 3
start, end = get_next_vars(func, pos)
print(func[start:end])       
new_func = func[start:end]
func = func[:start] + 'IDX' + func[end:]
print('OLDFUNC:', func, 'NEWFUNC:', new_func)
"""

#parse('((xx1+yy2)*zz3)-(3/2)', 'aa1')
#print(take_out_brackets('((xx1+yy1)*zz1)-(3/2)', 'aa1'))
 
#parse('(<xx1>+<yy1>)', 'aa1')

if sys.argv[1] == 'all':
    for sh in xlrd.open_workbook(path).sheets():  
        for row in range(sh.nrows):
            #TODO remove 'if' and the print function, was just to make debugging more readable
            print('Row:', row)
            if parse(sh.cell(row,9).value, sh.cell(row,7).value):
                print('-------------------------------------------------------')
else:
    row = int(sys.argv[1])-1
    print(sh[0].cell(row,9).value)
    parse(sh[0].cell(row,9).value, sh[0].cell(row,7).value)


parseFile.close()


