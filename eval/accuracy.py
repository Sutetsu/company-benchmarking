#!/usr/bin/env python

import argparse
import os
import glob
import re
import json
import numpy as np
import pythoneval


def parse_logfile(logfile):
    file_kpis = {}

    if not hasattr(parse_logfile, 'regex_client'):
        parse_logfile.regex_client = re.compile(r'\AKPIs (?P<kpis>\{.*\})\Z')

    if not hasattr(parse_logfile, 'regex_server'):
        parse_logfile.regex_server = re.compile(r'\AMEAN VALS (?P<kpis>\{.*\})\Z')

    with open(logfile, 'r') as fd:
        for line in fd:
            line = line.rstrip()

            match = parse_logfile.regex_client.match(line)
            if match:
                file_kpis = eval(match.group('kpis'))
                break

            match = parse_logfile.regex_server.match(line)
            if match:
                file_kpis = eval(match.group('kpis'))
                break

    return file_kpis


def parse_logdir(logdir):
    kpis = {}

    exclude = [('20200725-11h10m00s', '7'), ('20200725-11h10m00s', '20')]

    logfiles = glob.glob(logdir + '/*output.log')
    regex = re.compile(logdir + r'/log-(?P<date>\d{8}-\d\dh\d\dm\d\ds)_s-(?P<scenario>[a-zA-Z-]+)(_pm-(?P<parameter>[\w-]+))?_r-(?P<run>\d+)_p-(?P<program>[a-zA-Z-]+)(?P<execution>\d*)_t-(?P<logtype>[\w-]+).log')

    for logfile in logfiles:
        match = regex.match(logfile)
        if not match:
            raise FileException(f'Unexpected log file \'{logfile}\'')

        date = match.group('date')
        scenario = match.group('scenario')
        parameter = match.group('parameter')
        run = match.group('run')
        program = match.group('program')
        execution = int(match.group('execution')) + 1
        logtype = match.group('logtype')

        if program not in ['client', 'server'] or logtype not in ['output'] or (program in ['server'] and (execution - 1) != 6):
            print(f'Skipping {logfile}')
            continue

        if (date, run) in exclude:
            print(f'Excluding {logfile}')
            continue

        if program in ['server']:
            execution = 'server'

        scenario_base = '-'.join(scenario.split('-')[:-1])
        encryption = scenario.split('-')[-1]

        file_kpis = parse_logfile(logfile)
        for kpi in file_kpis:
            kpis.setdefault(date, {})
            kpis[date].setdefault(scenario_base, {})
            kpis[date][scenario_base].setdefault(execution, {})
            kpis[date][scenario_base][execution].setdefault(kpi, {})
            kpis[date][scenario_base][execution][kpi].setdefault(run, {})
            kpis[date][scenario_base][execution][kpi][run][encryption] = file_kpis[kpi]

    return kpis


def aggregate(kpis):
    result = {}

    for date in kpis:
        for scenario in kpis[date]:
            for execution in kpis[date][scenario]:
                if execution in ['server']:
                    result.setdefault(date, {})
                    result[date].setdefault(scenario, {})
                    result[date][scenario]['server'] = kpis[date][scenario]['server']
                    continue

                for kpi in kpis[date][scenario][execution]:
                    for run in kpis[date][scenario][execution][kpi]:
                        for encryption in kpis[date][scenario][execution][kpi][run]:
                            result.setdefault(date, {})
                            result[date].setdefault(scenario, {})
                            result[date][scenario].setdefault('aggregate', {})
                            result[date][scenario]['aggregate'].setdefault(kpi, {})
                            result[date][scenario]['aggregate'][kpi].setdefault(run, {})
                            result[date][scenario]['aggregate'][kpi][run].setdefault(encryption, [])
                            result[date][scenario]['aggregate'][kpi][run][encryption].append(kpis[date][scenario][execution][kpi][run][encryption])

    for date in result:
        for scenario in result[date]:
            for kpi in result[date][scenario]['aggregate']:
                for run in result[date][scenario]['aggregate'][kpi]:
                    for encryption in result[date][scenario]['aggregate'][kpi][run]:
                        values = result[date][scenario]['aggregate'][kpi][run][encryption]
                        result[date][scenario]['aggregate'][kpi][run][encryption] = np.mean(values)

    return result



def accuracy(kpis, by='total', server=False):
    result = {}

    for date in kpis:
        for scenario in kpis[date]:
            for execution in kpis[date][scenario]:
                if execution in ['server']:
                    continue

                for kpi in kpis[date][scenario][execution]:
                    for run in kpis[date][scenario][execution][kpi]:

                        if server:
                            # execution always equals 'aggregate'
                            plain = kpis[date][scenario][execution][kpi][run]['fhe']
                            enc = kpis[date][scenario]['server'][kpi][run]['fhe']
                        else:
                            if 'clear' not in kpis[date][scenario][execution][kpi][run]:
                                print(f'Error: KPI {kpi} in fhe but not in clear for {date}-{scenario}-{execution}-{run}')
                                continue
                            plain = kpis[date][scenario][execution][kpi][run]['clear']

                            if 'fhe' not in kpis[date][scenario][execution][kpi][run]:
                                print(f'Error: KPI {kpi} in clear but not in fhe for {date}-{scenario}-{execution}-{run}')
                                continue
                            enc = kpis[date][scenario][execution][kpi][run]['fhe']

                        absolute = abs(plain - enc)
                        if plain == 0:
                            relative = 0
                        else:
                            relative = absolute / abs(plain)

                        if by in ['kpi']:
                            by_value = kpi
                        elif by in ['client']:
                            by_value = execution
                        elif by in ['client-kpi']:
                            by_value = f'client{execution}-{kpi}'
                        elif by in ['total']:
                            by_value = 'total'
                        else:
                            raise ValueError(f'Invalid value for parameter \'by\': {by}')

                        result.setdefault(scenario, {})
                        result[scenario].setdefault(by_value, {})
                        result[scenario][by_value].setdefault('absolute', [])
                        result[scenario][by_value].setdefault('relative', [])

                        result[scenario][by_value]['absolute'].append(absolute)
                        result[scenario][by_value]['relative'].append(relative)

    for scenario in result:
        for by_value in result[scenario]:
            for value_type in result[scenario][by_value]:
                values = result[scenario][by_value][value_type]
                result[scenario][by_value][value_type] = {
                    'avg': np.mean(values),
                    'conf': pythoneval.confidence_value(values, confidence=0.99),
                    'min': min(values),
                    'max': max(values),
                    'num': len(values),
                }

    return result


def write_output(result, path):
    directory, filename = os.path.split(path)
    if not os.path.exists(directory) or not filename:
        raise ValueError(f'Invalid \'path\': {path}')

    with open(path, 'w') as fd:
        json.dump(result, fd)


def main(args):

    if 'logdir' not in args:
        raise ValueError('Argument \'logdir\ not defined')
    logdir = os.path.abspath(args['logdir'])
    if not os.path.isdir(logdir):
        raise ValueError(f'Argument \'logdir\' defines non-existing directory {logdir}')

    if 'by' not in args:
        raise ValueError('Argument \'by\' not defined')

    if 'server' not in args:
        raise ValueError('Argument \'server\' not defined')

    if args['server']:
        args['aggregate'] = True

    if 'aggregate' not in args:
        raise ValueError('Argument \'aggregate\' not defined')

    kpis = parse_logdir(logdir)

    if args['aggregate']:
        kpis = aggregate(kpis)

    result = accuracy(kpis, by=args['by'], server=args['server'])

    if 'file' in args and args['file']:
        write_output(result, args['file'])

    print(result)


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Compute accuracy')
    parser.add_argument('-a', '--aggregate', action='store_true', help='Aggregate KPIs before accuracy computation')
    parser.add_argument('-b', '--by', type=str, default='total', help='Output accuracy by \'kpi\', \'client\' or \'total\' accuracy (default: \'total\')')
    parser.add_argument('-f', '--file', type=str, help='Write accuracy in JSON format to given filename')
    parser.add_argument('-s', '--server', action='store_true', help='Only consider accuracy of server')
    parser.add_argument('-l', '--logdir', type=str, default='.', help='Specify the directory holding the evaluation logs (default: \'.\')')

    args = vars(parser.parse_args())

    main(args)
