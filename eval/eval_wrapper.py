import sys
import os
import signal
import pythoneval

if len(sys.argv) <= 1:
    raise ValueError('Code file not specified')

code_file = sys.argv[1]
sys.argv = sys.argv[1:]

with open(code_file, 'r') as fd:
    code = compile(fd.read(), code_file, 'exec')

global_vars = globals()
global_vars.update({
    '__file__': code_file
})

pythoneval.duration_start('_runtime', considerOverall=False)
try:
    exec(code, global_vars)
except SystemExit:
    pass
finally:
    pythoneval.duration_stop('_runtime')
    pythoneval.write_duration()
    pythoneval.write_traffic()
