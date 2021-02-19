#!/usr/bin/env python

import argparse
import subprocess
import signal
import shlex
import time
import os
import posixpath
import shutil
import glob


class Program(object):
    CODEBASE = os.path.abspath('.')
    USE_PERF_EVAL_WRAPPER = True

    def __init__(self, name, filename, arguments='', workdir='.'):
        self.name = name
        self.filename = filename
        self.arguments = arguments
        workdir_test = os.path.normpath(os.path.join(Program.CODEBASE, workdir))
        if not os.path.isdir(workdir_test):
            raise ValueError(f'Given \'workdir\' {workdir} for program {name} with code base {Program.CODEBASE} is not a valid directory')
        self.workdir = workdir
        self.process_id = 0
        self.processes = {}

    def __del__(self):
        self.terminate()

    def start(self, arguments=None):
        process_id = self.process_id
        self.process_id += 1

        log_file_output = log_file_format.format(program=f'{self.name}{process_id}', type='output')
        log_file_duration = log_file_format.format(program=f'{self.name}{process_id}', type='duration')
        log_file_traffic = log_file_format.format(program=f'{self.name}{process_id}', type='traffic')

        output_fd = open(log_file_output, 'wb')
        cmd = ['python3']
        if Program.USE_PERF_EVAL_WRAPPER:
            cmd.append(os.path.relpath(os.getcwd() + '/eval_wrapper.py', start=os.path.normpath(os.path.join(Program.CODEBASE, self.workdir))))
        cmd.append(self.filename)

        if arguments is None:
            arguments = self.arguments
        cmd.extend(shlex.split(arguments))

        cmd, workdir = docker.get_command_workdir(cmd, self.workdir)
        popen = subprocess.Popen(cmd, stdout=output_fd, stderr=subprocess.STDOUT, cwd=workdir)

        process = Process(self, popen, process_id, log_file_output, log_file_duration, log_file_traffic, output_fd)
        self.processes[process_id] = process

        return process

    def wait(self, timeout=None, terminate=False):
        returncodes = {}
        delete_ids = []
        for process_id in self.processes:
            if terminate:
                ret = self.processes[process_id].terminate()
            else:
                ret = self.processes[process_id].wait(timeout)
            returncodes[process_id] = ret
            delete_ids.append(process_id)

        for process_id in delete_ids:
            del self.processes[process_id]

        return returncodes

    terminate = lambda self : self.wait(terminate=True)


class ProcessException(Exception):
    pass


class Process(object):
    def __init__(self, program, popen, id, log_file_output, log_file_duration, log_file_traffic, output_fd):
        self.program = program
        self.popen = popen
        self.id = id
        self.log_file_output = log_file_output
        self.log_file_duration = log_file_duration
        self.log_file_traffic = log_file_traffic
        self.output_fd = output_fd

    def wait(self, timeout=None):
        ret = self.popen.wait(timeout)
        self._handle_logs()
        return ret

    def terminate(self):
        ret = self.popen.poll()
        if ret is None:
            self.popen.send_signal(signal.SIGINT)
            time.sleep(1)
            ret = self.popen.poll()
            if ret is None:
                self.popen.send_signal(signal.SIGTERM)
                time.sleep(1)
                ret = self.popen.poll()
                if ret is None:
                    self.popen.kill()
                    time.sleep(1)
                    ret = self.popen.poll()
                    if ret is None:
                        raise ProcessException(f'Termination of process {self.program.name}_{self.id} failed')

        self._handle_logs()
        return ret

    def _handle_logs(self):
        self.output_fd.close()

        # move duration logs from workdir to the log directory
        filename = os.path.splitext(self.program.filename)[0] + '_duration.log'
        log_file_duration_local = os.path.normpath(os.path.join(Program.CODEBASE, self.program.workdir, f'{filename}'))
        if os.path.isfile(log_file_duration_local):
            shutil.move(log_file_duration_local, self.log_file_duration)

        # move traffic logs from workdir to the log directory
        filename = os.path.splitext(self.program.filename)[0] + '_traffic.log'
        log_file_traffic_local = os.path.normpath(os.path.join(Program.CODEBASE, self.program.workdir, f'{filename}'))
        if os.path.isfile(log_file_traffic_local):
            shutil.move(log_file_traffic_local, self.log_file_traffic)


class Docker(object):
    IMAGE = '2020-ba-wagner-code'
    CONTAINER = 'perf_eval'

    def __init__(self, use_docker=False):
        self.use_docker = use_docker
        self.running = False

    def start(self):
        if not self.use_docker or self.running:
            return

        cmd = f'docker run --mount type=bind,source="{Program.CODEBASE}",destination=/code --rm --cap-add NET_ADMIN --name {Docker.CONTAINER} -dt {Docker.IMAGE}'
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
        self.running = True

    def stop(self):
        if not self.use_docker or not self.running:
            return
        cmd = f'docker kill {Docker.CONTAINER}'
        subprocess.run(shlex.split(cmd), stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, check=True)
        self.running = False

    def get_command_workdir(self, cmd, workdir):
        if not self.use_docker:
            workdir_in_codebase = os.path.normpath(os.path.join(Program.CODEBASE, workdir))
            return (cmd, workdir_in_codebase)

        docker_workdir = posixpath.normpath(f'/code/{workdir}')
        docker_cmd = f'docker exec -it -w "{docker_workdir}" {Docker.CONTAINER} {" ".join(cmd)}'
        return (shlex.split(docker_cmd), None)


def get_log_string():
    timestring = time.strftime("%Y%m%d-%Hh%Mm%Ss")
    return 'log-' + timestring

def set_network_parameters():
    cmd = 'sudo tcset --add lo --delay 50ms --rate 10mbit/s --dst-port 5005'
    cmd, workdir = docker.get_command_workdir(shlex.split(cmd), '.')
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    cmd = 'sudo tcset --add lo --delay 50ms --rate 100mbit/s --src-port 5005'
    cmd, workdir = docker.get_command_workdir(shlex.split(cmd), '.')
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def main(args):

    log_string = get_log_string()

    # make log directory
    if 'logdir' not in args:
        raise ValueError('Argument \'logdir\' not defined')
    log_dir = os.path.abspath(args['logdir'] + '/' + log_string)
    print(f'Making log directory: {log_dir}')
    if os.path.isdir(log_dir):
        shutil.rmtree(log_dir)
    os.makedirs(log_dir)

    if ('codebase' not in args) or (not os.path.isdir(args['codebase'])):
        raise ValueError('Argument \'codebase\' not defined or points to non-existent directory')
    Program.CODEBASE = os.path.abspath(args['codebase'])

    global scenario_classes
    scenario_classes = {
        'IKV': {
            'encryption': ['clear', 'fhe'],
            'aggregate': True,
            'clients': [6]
        },
        'benchmark': {
            'encryption': ['clear', 'fhe'],
            'operations': ['addition', 'multiplication', 'root', 'minimum'],
        },
        'nested': {
            'encryption': ['clear', 'fhe'],
            'operations': ['addition', 'root', 'minimum'],
            'nest_length': range(10, 101, 10)
        },
        '_test': {
            'encryption': ['fhe'],
            'aggregate': True,
        },
    }

    if 'scenario' not in args:
        raise ValueError('Argument \'scenario\' not defined or invalid')
    elif args['scenario'] in scenario_classes:
        scenarios = [args['scenario']]
    elif args['scenario'] == 'all':
        scenarios = [list(scenario_classes)]
    else:
        raise ValueError(f'Scenario \'{args["scenario"]}\' is not defined')

    # save measurement summary
    with open(log_dir + f'/{log_string}_README.txt', 'w') as fd_readme:
        fd_readme.write(f'\t\tMEASUREMENT SUMMARY \'{log_string}\'\n\n\n')
        fd_readme.write(f'Input arguments: {args}\n')
        fd_readme.write(f'Scenarios: {scenarios}\n\n\n')
        fd_readme.write(f'Scenario classes: {scenario_classes}\n')

    # uniform log file name to be used by Program objects
    global log_file_format

    global docker
    docker = Docker(use_docker=args['docker'])

    try:
        for scenario in scenarios:

            if 'operations' in scenario_classes[scenario]:
                sub_scenarios = scenario_classes[scenario]['operations']
            else:
                sub_scenarios = ['']

            if 'encryption' in scenario_classes[scenario]:
                encryptions = scenario_classes[scenario]['encryption']
            else:
                encryptions = ['fhe']

            if 'clients' in scenario_classes[scenario]:
                parameters = scenario_classes[scenario]['clients']
            elif 'nest_length' in scenario_classes[scenario]:
                parameters = scenario_classes[scenario]['nest_length']
            else:
                parameters = [None]

            if 'runs' not in args:
                raise ValueError('Argument \'runs\' not defined')
            runs = int(args['runs'])

            for run in range(runs):
                for sub_scenario in sub_scenarios:
                    for encryption in encryptions:
                        for parameter in parameters:

                            # define programs to be tested
                            proxy = Program('proxy', 'Proxy3.py', workdir='./proxy')
                            analyst = Program('analyst', 'Analyst3.py', workdir='./analyst')
                            client = Program('client', 'Client3.py', workdir='./client')
                            server = Program('server', 'Server3.py', workdir='./server')
                            all_programs = [proxy, analyst, client, server]

                            if sub_scenario != '':
                                sub_scenario_substring = f'-{sub_scenario}'
                            else:
                                sub_scenario_substring = ''

                            scenario_name = f'{scenario}{sub_scenario_substring}-{encryption}'
                            if parameter is not None:
                                parameter_substring = f'_pm-{parameter}'
                            else:
                                parameter_substring = ''

                            print(f'Performing measurement run {run+1} of {runs} for scenario {scenario_name}{parameter_substring} (started at {time.ctime()})')
                            log_file_format = log_dir + f'/{log_string}_s-{scenario_name}{parameter_substring}_r-{run+1}' + '_p-{program}_t-{type}.log'

                            if 'clients' in scenario_classes[scenario]:
                                clients = parameter
                            else:
                                clients = 1

                            if scenario in ['benchmark', 'nested']:
                                analyst_filename_list = [scenario, sub_scenario]
                                if parameter is not None:
                                    analyst_filename_list.append(str(parameter))
                                analyst_filename_base = '-'.join(analyst_filename_list)
                                analyst_arguments = f'-a algorithms/{analyst_filename_base}.alg -k algorithms/{analyst_filename_base}.kpi'
                                client_arguments = f'-i benchmark_nested_inputs.xlsx'
                            # elif scenario in ['IKV']:
                                # *** use hard-coded algorithm and kpis for now ***
                                # analyst_arguments = f'-a parsed2.txt -k KPIs.txt'
                                # client_arguments = f'-i ClientData.xlsx'
                            else:
                                analyst_arguments = ''
                                client_arguments = ''

                            # remove all existing database files for independence between runs
                            db_files = glob.glob(Program.CODEBASE + '/**/*.db', recursive=True)
                            for db_file in db_files:
                                os.remove(db_file)

                            # start docker
                            docker.start()

                            set_network_parameters()

                            # start actual measurements
                            proxy.start(encryption)
                            time.sleep(2) # wait for correct flask startup

                            analyst.start(analyst_arguments)
                            analyst.wait()

                            server.start('keys')
                            server.wait()

                            for client_id in range(1, clients+1):
                                client.start(f'{str(client_id)} {encryption} {client_arguments}')
                                client.wait()

                                if ('aggregate' in scenario_classes[scenario]) and (scenario_classes[scenario]['aggregate']):
                                    time.sleep(0.5) # grace time
                                    server.start('kpi')
                                    server.wait()

                                time.sleep(1) # grace time

                            proxy.terminate()

                            # stop docker
                            docker.stop()
                            time.sleep(1) # grace time for stopping docker

    finally:
        # stop docker
        docker.stop()

    return


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Run performance evaluation')
    parser.add_argument('-c', '--codebase', type=str, default='..', help='Path to the code base or code repository (default: \'..\')')
    parser.add_argument('-d', '--docker', action='store_true', help='Set flag to execute system within a docker container')
    parser.add_argument('-l', '--logdir', type=str, default='.', help='Specify the directory for storing evaluation logs (default: \'.\')')
    parser.add_argument('-s', '--scenario', type=str, default='_test', help='Define a scenario or a scenario class to use for the current measurement (default: \'_test\')')
    parser.add_argument('-r', '--runs', type=int, default=1, help='Number of measurement runs to perform (default: 1)')

    args = vars(parser.parse_args())

    main(args)
