#!/usr/bin/env python

import argparse
import os
import glob
import re
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.lines as lin
import matplotlib.patches as ptc
import pythoneval


bytes_in_kbytes = 1e3
bytes_in_mbytes = 1e6


class FileException(Exception):
    pass


def get_durations(logdir):
    durations = {}
    duration_files = glob.glob(logdir + '/*duration.log')
    global re_logfile

    for logfile in duration_files:
        m_logfile = re_logfile.match(logfile)
        if not m_logfile:
            raise FileException(f'Unexpected duration log file \'{logfile}\'')

        date = m_logfile.group('date')
        scenario = m_logfile.group('scenario')
        parameter = m_logfile.group('parameter')
        run = int(m_logfile.group('run'))
        program = m_logfile.group('program')
        execution = int(m_logfile.group('execution'))
        logtype = m_logfile.group('logtype')

        if logtype not in ['duration']:
            print(f'Skipping {logfile}')
            continue

        print(f'Importing {logfile}')
        durations.setdefault(date, {})
        durations[date].setdefault(scenario, {})
        durations[date][scenario].setdefault(parameter, {})
        durations[date][scenario][parameter].setdefault(run, {})
        durations[date][scenario][parameter][run].setdefault(program, {})

        if execution in durations[date][scenario][parameter][run][program]:
            raise FileException(f'Redefinition of existing log file {logfile}')

        with open(logfile, 'r') as fd:
            durations[date][scenario][parameter][run][program][execution] = json.load(fd)

    return durations


def get_traffic(logdir):
    traffic = {}
    traffic_files = glob.glob(logdir + '/*traffic.log')
    global re_logfile

    for logfile in traffic_files:
        m_logfile = re_logfile.match(logfile)
        if not m_logfile:
            raise FileException(f'Unexpected traffic log file \'{logfile}\'')

        date = m_logfile.group('date')
        scenario = m_logfile.group('scenario')
        parameter = m_logfile.group('parameter')
        run = int(m_logfile.group('run'))
        program = m_logfile.group('program')
        execution = int(m_logfile.group('execution'))
        logtype = m_logfile.group('logtype')

        if logtype not in ['traffic']:
            print(f'Skipping {logfile}')
            continue

        print(f'Importing {logfile}')
        traffic.setdefault(date, {})
        traffic[date].setdefault(scenario, {})
        traffic[date][scenario].setdefault(parameter, {})
        traffic[date][scenario][parameter].setdefault(run, {})
        traffic[date][scenario][parameter][run].setdefault(program, {})

        if execution in traffic[date][scenario][parameter][run][program]:
            raise FileException(f'Redefinition of existing log file {logfile}')

        with open(logfile, 'r') as fd:
            traffic[date][scenario][parameter][run][program][execution] = json.load(fd)

    return traffic


def aggregate_durations(durations):
    aggregated_durations = {}

    for date in durations:
        for scenario in durations[date]:
            for parameter in durations[date][scenario]:
                for run in durations[date][scenario][parameter]:
                    for program in durations[date][scenario][parameter][run]:
                        for execution in durations[date][scenario][parameter][run][program]:
                            for label in durations[date][scenario][parameter][run][program][execution]:
                                program_execution = f'{program}{execution}'

                                aggregated_durations.setdefault(scenario, {})
                                aggregated_durations[scenario].setdefault(parameter, {})
                                aggregated_durations[scenario][parameter].setdefault(program_execution, {})
                                aggregated_durations[scenario][parameter][program_execution].setdefault(label, {})
                                aggregated_durations[scenario][parameter][program_execution][label].setdefault('values', [])
                                aggregated_durations[scenario][parameter][program_execution][label]['values'].append(durations[date][scenario][parameter][run][program][execution][label])

                                if args['networking']:
                                    if program in ['client'] and label in ['computation']:
                                        networking_duration = durations[date][scenario][parameter][run][program][execution][label]
                                        networking_duration -= durations[date][scenario][parameter][run]['proxy'][execution]['computation']

                                        aggregated_durations[scenario][parameter][program_execution].setdefault('networking', {})
                                        aggregated_durations[scenario][parameter][program_execution]['networking'].setdefault('values', [])
                                        aggregated_durations[scenario][parameter][program_execution]['networking']['values'].append(networking_duration)

                                    elif program in ['server'] and label in ['aggregation_avg']:
                                        networking_duration = durations[date][scenario][parameter][run][program][execution][label]
                                        networking_duration -= durations[date][scenario][parameter][run]['proxy'][execution]['aggregation_avg']

                                        aggregated_durations[scenario][parameter][program_execution].setdefault('networking', {})
                                        aggregated_durations[scenario][parameter][program_execution]['networking'].setdefault('values', [])
                                        aggregated_durations[scenario][parameter][program_execution]['networking']['values'].append(networking_duration)

    for scenario in aggregated_durations:
        for parameter in aggregated_durations[scenario]:
            for program in aggregated_durations[scenario][parameter]:
                for label in aggregated_durations[scenario][parameter][program]:
                    values = aggregated_durations[scenario][parameter][program][label]['values']
                    del aggregated_durations[scenario][parameter][program][label]['values']
                    aggregated_durations[scenario][parameter][program][label]['avg'] = np.mean(values)
                    aggregated_durations[scenario][parameter][program][label]['conf'] = pythoneval.confidence_value(values, confidence=0.99)
                    aggregated_durations[scenario][parameter][program][label]['num'] = len(values)

    return aggregated_durations


def aggregate_traffic(traffic):
    aggregated_traffic = {}

    for date in traffic:
        for scenario in traffic[date]:
            for parameter in traffic[date][scenario]:
                for run in traffic[date][scenario][parameter]:
                    for program in traffic[date][scenario][parameter][run]:
                        for execution in traffic[date][scenario][parameter][run][program]:
                            for label in traffic[date][scenario][parameter][run][program][execution]:
                                program_execution = f'{program}{execution}'

                                aggregated_traffic.setdefault(scenario, {})
                                aggregated_traffic[scenario].setdefault(parameter, {})
                                aggregated_traffic[scenario][parameter].setdefault(program_execution, {})
                                aggregated_traffic[scenario][parameter][program_execution].setdefault(label, {})
                                aggregated_traffic[scenario][parameter][program_execution][label].setdefault('values', [])
                                aggregated_traffic[scenario][parameter][program_execution][label]['values'].append(traffic[date][scenario][parameter][run][program][execution][label])

    for scenario in aggregated_traffic:
        for parameter in aggregated_traffic[scenario]:
            for program in aggregated_traffic[scenario][parameter]:
                for label in aggregated_traffic[scenario][parameter][program]:
                    values = aggregated_traffic[scenario][parameter][program][label]['values']
                    del aggregated_traffic[scenario][parameter][program][label]['values']
                    aggregated_traffic[scenario][parameter][program][label]['avg'] = np.mean(values) / bytes_in_mbytes
                    aggregated_traffic[scenario][parameter][program][label]['conf'] = pythoneval.confidence_value(values, confidence=0.99) / bytes_in_mbytes
                    aggregated_traffic[scenario][parameter][program][label]['num'] = len(values)

    return aggregated_traffic


def json_dump(scenario_class, aggregated_durations, aggregated_traffic):
    d = {
        'durations': aggregated_durations,
        'traffic': aggregated_traffic,
    }

    with open(f'plots/{scenario_class}.json', 'w') as fd:
        json.dump(d, fd)


def plot_benchmark(aggregated_durations, aggregated_traffic):
    labels = ['addition', 'multiplication', 'root', 'minimum']

    duration_encrypted = []
    duration_encrypted_conf = []
    duration_baseline = []
    duration_baseline_conf = []

    if args['networking']:
        networking_encrypted = []
        networking_encrypted_conf = []
        networking_baseline = []
        networking_baseline_conf = []

    traffic_encrypted = []
    traffic_encrypted_conf = []
    traffic_baseline = []
    traffic_baseline_conf = []

    for operation in labels:
        duration_encrypted.append(aggregated_durations[f'benchmark-{operation}-fhe'][None]['client0']['computation']['avg'])
        duration_encrypted_conf.append(aggregated_durations[f'benchmark-{operation}-fhe'][None]['client0']['computation']['conf'])
        duration_baseline.append(aggregated_durations[f'benchmark-{operation}-clear'][None]['client0']['computation']['avg'])
        duration_baseline_conf.append(aggregated_durations[f'benchmark-{operation}-clear'][None]['client0']['computation']['conf'])

        if args['networking']:
            networking_encrypted.append(aggregated_durations[f'benchmark-{operation}-fhe'][None]['client0']['networking']['avg'])
            networking_encrypted_conf.append(aggregated_durations[f'benchmark-{operation}-fhe'][None]['client0']['networking']['conf'])
            networking_baseline.append(aggregated_durations[f'benchmark-{operation}-clear'][None]['client0']['networking']['avg'])
            networking_baseline_conf.append(aggregated_durations[f'benchmark-{operation}-clear'][None]['client0']['networking']['conf'])

        traffic_encrypted.append(aggregated_traffic[f'benchmark-{operation}-fhe'][None]['client0']['computation']['avg'])
        traffic_encrypted_conf.append(aggregated_traffic[f'benchmark-{operation}-fhe'][None]['client0']['computation']['conf'])
        traffic_baseline.append(aggregated_traffic[f'benchmark-{operation}-clear'][None]['client0']['computation']['avg'])
        traffic_baseline_conf.append(aggregated_traffic[f'benchmark-{operation}-clear'][None]['client0']['computation']['conf'])

    fig, ax_duration = plt.subplots(figsize=(figure_width,figure_height))
    ax_traffic = ax_duration.twinx()
    fig.subplots_adjust(left=0.1, right=0.9, top=0.92, bottom=0.2)

    x = np.arange(4)
    if args['networking']:
        width = 0.2
        move = 1.2 * width
    else:
        width = 0.3
        move = 0.6 * width

    duration_color = 'tab:orange'
    networking_color = 'saddlebrown'
    traffic_color = 'tab:blue'

    duration_axis_color = '#7F4014'
    traffic_axis_color = '#1C5D7F'

    error_kw = {'capsize':1.4, 'elinewidth':1, 'capthick':1}

    if args['networking']:
        ax_duration.fill([-0.45,-0.45,1.45,1.45], [0,40,40,0], 'lightgray')
        ax_duration.text(0.5, 35, 'local calculations on proxy', horizontalalignment='center')
        ax_duration.text(2.5, 35, 'offloaded complex calculations', horizontalalignment='center')
    else:
        ax_duration.fill([-0.45,-0.45,1.45,1.45], [0,1.9,1.9,0], 'lightgray')
        ax_duration.text(0.5, 1.6, 'local calculations on proxy', horizontalalignment='center')
        ax_duration.text(2.5, 1.6, 'offloaded complex calculations', horizontalalignment='center')
    ax_duration.bar(x - move, duration_encrypted, width, yerr=duration_encrypted_conf, error_kw=error_kw, edgecolor='black', linewidth=1, color=duration_color)
    ax_duration.bar(x - move, duration_baseline, width, yerr=duration_baseline_conf, error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')
    if args['networking']:
        ax_duration.bar(x, networking_encrypted, width, yerr=networking_encrypted_conf, error_kw=error_kw, edgecolor='black', linewidth=1, color=networking_color)
        ax_duration.bar(x, networking_baseline, width, yerr=networking_baseline_conf, error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')
    ax_traffic.bar(x + move, traffic_encrypted, width, yerr=traffic_encrypted_conf, error_kw=error_kw, edgecolor='black', linewidth=1, color=traffic_color)
    ax_traffic.bar(x + move, traffic_baseline, width, yerr=traffic_baseline_conf, error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')

    ax_duration.set_xticks(x)
    ax_duration.set_xticklabels(['Addition', 'Multiplication', 'Square Root', 'Minimum'])
    ax_duration.set_xlabel('Operation')

    legend_elements = [
        ptc.Patch(facecolor=duration_color, edgecolor='black', linewidth=1, label='Runtime'),
        ptc.Patch(facecolor=traffic_color, edgecolor='black', linewidth=1, label='Traffic'),
        ptc.Patch(fill=False, hatch='////', edgecolor='black', linewidth=1, label='Baseline (unenc.)'),
    ]
    if args['networking']:
        legend_elements.insert(1, ptc.Patch(facecolor=networking_color, edgecolor='black', linewidth=1, label='Networking Time'))
    plt.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.125), ncol=len(legend_elements), fancybox=False, framealpha=1, edgecolor='black', borderpad=0.3, handletextpad=0.4, columnspacing=1.3)

    ax_duration.set_ylabel('Time [s]', color=duration_axis_color)
    if args['networking']:
        ax_duration.set_ylim([0, 45])
    else:
        ax_duration.set_ylim([0, 2.2])
    ax_duration.tick_params(axis='y', labelcolor=duration_axis_color)

    ax_traffic.set_ylabel('Traffic [MByte]', color=traffic_axis_color)
    ax_traffic.set_ylim([0, 22])
    ax_traffic.tick_params(axis='y', labelcolor=traffic_axis_color)

    basename = 'benchmark'
    if args['networking']:
        basename += '_networking'
    fig.savefig(f'plots/{basename}.pdf', bbox_inches='tight')
    json_dump(basename, aggregated_durations, aggregated_traffic)


def plot_nested(aggregated_durations, aggregated_traffic):
    operators = ['addition', 'root', 'minimum']
    data = {}
    errors = set()

    for operator in operators:
        data.setdefault(operator, {})
        data[operator].setdefault('x', [])
        data[operator].setdefault('duration', [])
        data[operator].setdefault('duration_conf', [])
        data[operator].setdefault('traffic', [])
        data[operator].setdefault('traffic_conf', [])

        for x in sorted(int(nest_length) for nest_length in aggregated_durations[f'nested-{operator}-fhe']):
            try:
                data[operator]['x'].append(x)
                data[operator]['duration'].append(aggregated_durations[f'nested-{operator}-fhe'][str(x)]['client0']['computation']['avg'])
                data[operator]['duration_conf'].append(aggregated_durations[f'nested-{operator}-fhe'][str(x)]['client0']['computation']['conf'])
                data[operator]['traffic'].append(aggregated_traffic[f'nested-{operator}-fhe'][str(x)]['client0']['computation']['avg'])
                data[operator]['traffic_conf'].append(aggregated_traffic[f'nested-{operator}-fhe'][str(x)]['client0']['computation']['conf'])
            except KeyError:
                errors.add(f'{operator}{x}')

    if errors:
        print(f'Errors: {errors}')

    fig, ax_traffic = plt.subplots(figsize=(figure_width,figure_height))
    ax_duration = ax_traffic.twinx()
    ax_duration.yaxis.tick_left()
    ax_duration.yaxis.set_label_position("left")
    ax_traffic.yaxis.tick_right()
    ax_traffic.yaxis.set_label_position("right")
    fig.subplots_adjust(left=0.08, right=0.91, top=0.92, bottom=0.2)

    duration_color = 'tab:orange'
    traffic_color = 'tab:blue'

    duration_axis_color = '#7F4014'
    traffic_axis_color = '#1C5D7F'

    format_operator = {
        'addition': '+',
        'multiplication': 'x',
        'root': 'd',
        'minimum': 's',
    }

    errorbars = False

    for operator in operators:
        if operator in ['addition', 'multiplication']:
            ms = 10
        else:
            ms = None

        if errorbars:
            ax_duration.errorbar(data[operator]['x'], data[operator]['duration'], yerr=data[operator]['duration_conf'], fmt=format_operator[operator]+'-', ms=ms, color=duration_color)
            ax_traffic.errorbar(data[operator]['x'], data[operator]['traffic'], yerr=data[operator]['traffic_conf'], fmt=format_operator[operator]+'-', ms=ms, color=traffic_color)
        else:
            ax_duration.plot(data[operator]['x'], data[operator]['duration'], format_operator[operator]+'-', mec='black', mfc='black', ms=ms, color=duration_color)
            ax_traffic.plot(data[operator]['x'], data[operator]['traffic'], format_operator[operator]+'-', mec='black', mfc='black', ms=ms, color=traffic_color)

    ax_traffic.set_xticks(data['addition']['x'])
    ax_traffic.set_xlabel('Operator Chain Length')

    legend1_elements = [
        lin.Line2D([0],[0], color=duration_color, label='Runtime (enc.)'),
        lin.Line2D([0],[0], color=traffic_color, label='Traffic (enc.)'),
    ]
    legend1 = plt.legend(handles=legend1_elements, loc='upper center', bbox_to_anchor=(0.5, 1.125), ncol=2, fancybox=False, framealpha=1, edgecolor='black', borderpad=0.3, handletextpad=0.4, columnspacing=1.3)

    legend2_elements = [
        lin.Line2D([0],[0], marker=format_operator['addition'], ms=10, color='black', linestyle='None', label='Addition (on proxy)'),
        #lin.Line2D([0],[0], marker=format_operator['multiplication'], ms=10, color='black', linestyle='None', label='Multiplication'),
        lin.Line2D([0],[0], marker=format_operator['root'], color='black', linestyle='None', label='Square Root (offloaded)'),
        lin.Line2D([0],[0], marker=format_operator['minimum'], color='black', linestyle='None', label='Minimum (offloaded)'),
    ]
    ax_duration.legend(handles=legend2_elements, loc='upper left', bbox_to_anchor=(0,0.9), ncol=1, fancybox=False, framealpha=1, edgecolor='black', labelspacing=0.25, handlelength=1, handletextpad=0.4, columnspacing=0.5)
    ax_duration.add_artist(legend1)

    ax_duration.set_ylabel('Time [s]', color=duration_axis_color)
    ax_duration.set_ylim([-1, 80])
    ax_duration.tick_params(axis='y', labelcolor=duration_axis_color)

    ax_traffic.set_ylabel('Traffic [MByte]', color=traffic_axis_color)
    ax_traffic.set_ylim([-10, 800])
    ax_traffic.tick_params(axis='y', labelcolor=traffic_axis_color)

    basename = 'nested'
    if args['networking']:
        basename += '_networking'
    fig.savefig(f'plots/{basename}.pdf', bbox_inches='tight')
    json_dump(basename, aggregated_durations, aggregated_traffic)


def plot_IKV(aggregated_durations, aggregated_traffic):
    client = {
        'duration': {
            'setup': {},
            'computation': {},
        },
        'networking': {},
        'traffic': {
            'setup': {},
            'computation': {},
        },
    }
    server = {
        'duration': {
            'aggregation_avg': {},
            'aggregation_ope': {},
        },
        'networking': {},
        'traffic': {
            'aggregation_avg': {},
            'aggregation_ope': {},
        },
    }

    for encryption in ['clear', 'fhe']:
        for value_type in ['avg', 'conf']:

            for label in ['setup', 'computation']:
                client['duration'][label].setdefault(encryption, {})
                client['duration'][label][encryption][value_type] = [aggregated_durations[f'IKV-{encryption}']['6'][f'client{n}'][label][value_type] for n in range(6)]
                client['traffic'][label].setdefault(encryption, {})
                client['traffic'][label][encryption][value_type] = [aggregated_traffic[f'IKV-{encryption}']['6'][f'client{n}'][label][value_type] for n in range(6)]

            if args['networking']:
                client['networking'].setdefault(encryption, {})
                client['networking'][encryption][value_type] = [aggregated_durations[f'IKV-{encryption}']['6'][f'client{n}']['networking'][value_type] for n in range(6)]

            for label in ['aggregation_avg']:
                server['duration'][label].setdefault(encryption, {})
                server['duration'][label][encryption][value_type] = [aggregated_durations[f'IKV-{encryption}']['6'][f'server{n+1}'][label][value_type] for n in range(6)]
                server['traffic'][label].setdefault(encryption, {})
                server['traffic'][label][encryption][value_type] = [aggregated_traffic[f'IKV-{encryption}']['6'][f'server{n+1}'][label][value_type] for n in range(6)]

            server['duration']['aggregation_ope'].setdefault(encryption, {})
            server['duration']['aggregation_ope'][encryption][value_type] = [aggregated_durations[f'IKV-{encryption}']['6'][f'server{n+1}']['aggregation_all'][value_type] - aggregated_durations[f'IKV-{encryption}']['6'][f'server{n+1}']['aggregation_avg'][value_type] for n in range(6)]
            server['traffic']['aggregation_ope'].setdefault(encryption, {})
            server['traffic']['aggregation_ope'][encryption][value_type] = [aggregated_traffic[f'IKV-{encryption}']['6'][f'server{n+1}']['aggregation_all'][value_type] - aggregated_durations[f'IKV-{encryption}']['6'][f'server{n+1}']['aggregation_avg'][value_type] for n in range(6)]

            if args['networking']:
                server['networking'].setdefault(encryption, {})
                server['networking'][encryption][value_type] = [aggregated_durations[f'IKV-{encryption}']['6'][f'server{n+1}']['networking'][value_type] for n in range(6)]

    axs_client = {}
    fig_client, axs_client['duration'] = plt.subplots(figsize=(figure_width,figure_height))
    axs_client['traffic'] = axs_client['duration'].twinx()
    fig_client.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)

    axs_server = {}
    fig_server, axs_server['duration'] = plt.subplots(figsize=(figure_width,figure_height))
    axs_server['traffic'] = axs_server['duration'].twinx()
    fig_server.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)

    colors = {
        'client': {
            'duration': {
                'setup': 'moccasin',
                'computation': 'tab:orange',
            },
            'networking': 'saddlebrown',
            'traffic': {
                'setup': 'lightsteelblue',
                'computation': 'tab:blue',
            },
        },
        'server': {
            'duration': {
                'aggregation_avg': 'tab:orange',
                'aggregation_ope': 'moccasin',
            },
            'networking': 'saddlebrown',
            'traffic': {
                'aggregation_avg': 'tab:blue',
                'aggregation_ope': 'lightsteelblue',
            },
        },
    }

    duration_axis_color = '#7F4014'
    traffic_axis_color = '#1C5D7F'

    x = np.arange(6)
    width = 0.2
    if args['networking']:
        offset_factor = 1.2
    else:
        offset_factor = 0.9

    error_kw = {'capsize':1.4, 'elinewidth':1, 'capthick':1}

    for bar in ['duration', 'traffic']:
        if bar in ['duration']:
            move = -offset_factor * width
        else:
            move = +offset_factor * width
        axs_client[bar].bar(x + move, client[bar]['setup']['fhe']['avg'], width, yerr=client[bar]['setup']['fhe']['conf'], error_kw=error_kw, edgecolor='black', linewidth=1, color=colors['client'][bar]['setup'])
        axs_client[bar].bar(x + move, client[bar]['setup']['clear']['avg'], width, yerr=client[bar]['setup']['clear']['conf'], error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')
        axs_client[bar].bar(x + move, client[bar]['computation']['fhe']['avg'], width, yerr=client[bar]['computation']['fhe']['conf'], bottom=client[bar]['setup']['fhe']['avg'], error_kw=error_kw, edgecolor='black', linewidth=1, color=colors['client'][bar]['computation'])
        axs_client[bar].bar(x + move, client[bar]['computation']['clear']['avg'], width, yerr=client[bar]['computation']['clear']['conf'], bottom=client[bar]['setup']['fhe']['avg'], error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')

    if args['networking']:
        axs_client['duration'].bar(x, client['duration']['computation']['fhe']['avg'], width, yerr=client['duration']['computation']['fhe']['conf'], error_kw=error_kw, edgecolor='black', linewidth=1, color=colors['client']['networking'])
        axs_client['duration'].bar(x, client['duration']['computation']['clear']['avg'], width, yerr=client['duration']['computation']['clear']['conf'], error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')

    for bar in ['duration', 'traffic']:
        if bar in ['duration']:
            move = -offset_factor * width
        else:
            move = +offset_factor * width

        axs_server[bar].bar(x + move, server[bar]['aggregation_avg']['fhe']['avg'], width, yerr=server[bar]['aggregation_avg']['fhe']['conf'], error_kw=error_kw, edgecolor='black', linewidth=1, color=colors['server'][bar]['aggregation_avg'])
        axs_server[bar].bar(x + move, server[bar]['aggregation_avg']['clear']['avg'], width, yerr=server[bar]['aggregation_avg']['clear']['conf'], error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')
        # axs_server[bar].bar(x + move, server[bar]['aggregation_ope']['fhe']['avg'], width, yerr=server[bar]['aggregation_ope']['fhe']['conf'], bottom=server[bar]['aggregation_avg']['fhe']['avg'], error_kw=error_kw, edgecolor='black', linewidth=1, color=colors['server'][bar]['aggregation_ope'])
        # axs_server[bar].bar(x + move, server[bar]['aggregation_ope']['clear']['avg'], width, yerr=server[bar]['aggregation_ope']['clear']['conf'], bottom=server[bar]['aggregation_avg']['fhe']['avg'], error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')

    if args['networking']:
        axs_server['duration'].bar(x, server['duration']['aggregation_avg']['fhe']['avg'], width, yerr=server['duration']['aggregation_avg']['fhe']['conf'], error_kw=error_kw, edgecolor='black', linewidth=1, color=colors['server']['networking'])
        axs_server['duration'].bar(x, server['duration']['aggregation_avg']['clear']['avg'], width, yerr=server['duration']['aggregation_avg']['clear']['conf'], error_kw=error_kw, edgecolor='black', linewidth=1, fill=False, hatch='////')

    ### Client plot ###

    axs_client['duration'].set_xticks(x)
    axs_client['duration'].set_xticklabels([1,2,3,4,5,6])
    axs_client['duration'].set_xlabel('Client ID')

    legend_elements = [
        ptc.Patch(facecolor=colors['client']['duration']['setup'], edgecolor='black', linewidth=1, label='Setup Runtime'),
        ptc.Patch(facecolor=colors['client']['duration']['computation'], edgecolor='black', linewidth=1, label='Computation Runtime'),
        ptc.Patch(facecolor=colors['client']['traffic']['setup'], edgecolor='black', linewidth=1, label='Setup Traffic'),
        ptc.Patch(facecolor=colors['client']['traffic']['computation'], edgecolor='black', linewidth=1, label='Computation Traffic'),
        ptc.Patch(fill=False, hatch='////', edgecolor='black', linewidth=1, label='Baseline (unenc.)'),
    ]
    if args['networking']:
        legend_elements.insert(2, ptc.Patch(facecolor=colors['client']['networking'], edgecolor='black', linewidth=1, label='Networking Time'))
    axs_client['traffic'].legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3, fancybox=False, framealpha=1, edgecolor='black', labelspacing=0.2, borderpad=0.3, handletextpad=0.4, columnspacing=1.3)

    axs_client['duration'].set_ylabel('Time [s]', color=duration_axis_color)
    axs_client['duration'].set_yscale('log')
    axs_client['duration'].set_ylim([1e-2, 1e4])
    major_ticks = matplotlib.ticker.LogLocator(base=10,numticks=12)
    axs_client['duration'].yaxis.set_major_locator(major_ticks)
    minor_ticks = matplotlib.ticker.LogLocator(base=10.0,subs=np.arange(0.1,1,0.1),numticks=12)
    axs_client['duration'].yaxis.set_minor_locator(minor_ticks)
    axs_client['duration'].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axs_client['duration'].tick_params(axis='y', labelcolor=duration_axis_color)

    axs_client['traffic'].set_ylabel('Traffic [MByte]', color=traffic_axis_color)
    axs_client['traffic'].set_yscale('log')
    axs_client['traffic'].set_ylim([1e0, 1e5])
    major_ticks = matplotlib.ticker.LogLocator(base=10,numticks=12)
    axs_client['traffic'].yaxis.set_major_locator(major_ticks)
    minor_ticks = matplotlib.ticker.LogLocator(base=10.0,subs=np.arange(0.1,1,0.1),numticks=12)
    axs_client['traffic'].yaxis.set_minor_locator(minor_ticks)
    axs_client['traffic'].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axs_client['traffic'].tick_params(axis='y', labelcolor=traffic_axis_color)

    ### Server plot ###

    axs_server['duration'].set_xticks(x)
    axs_server['duration'].set_xticklabels([1,2,3,4,5,6])
    axs_server['duration'].set_xlabel('KPI Aggregation of k Participants')

    legend_elements = [
        ptc.Patch(facecolor=colors['server']['duration']['aggregation_avg'], edgecolor='black', linewidth=1, label='Runtime'),
        # ptc.Patch(facecolor=colors['server']['duration']['aggregation_ope'], edgecolor='black', linewidth=1, label='Runtime Extrema'),
        ptc.Patch(facecolor=colors['server']['traffic']['aggregation_avg'], edgecolor='black', linewidth=1, label='Traffic'),
        # ptc.Patch(facecolor=colors['server']['traffic']['aggregation_ope'], edgecolor='black', linewidth=1, label='Traffic Extrema'),
        ptc.Patch(fill=False, hatch='////', edgecolor='black', linewidth=1, label='Baseline (unenc.)'),
    ]
    if args['networking']:
        legend_elements.insert(1, ptc.Patch(facecolor=colors['server']['networking'], edgecolor='black', linewidth=1, label='Networking Time'))
    axs_server['traffic'].legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.125), ncol=len(legend_elements), fancybox=False, framealpha=1, edgecolor='black', borderpad=0.3, handletextpad=0.4, columnspacing=1.3)

    axs_server['duration'].set_ylabel('Time [s]', color=duration_axis_color)
    axs_server['duration'].set_yscale('log')
    axs_server['duration'].set_ylim([1e-3, 1e3])
    major_ticks = matplotlib.ticker.LogLocator(base=10,numticks=12)
    axs_server['duration'].yaxis.set_major_locator(major_ticks)
    minor_ticks = matplotlib.ticker.LogLocator(base=10.0,subs=np.arange(0.1,1,0.1),numticks=12)
    axs_server['duration'].yaxis.set_minor_locator(minor_ticks)
    axs_server['duration'].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axs_server['duration'].tick_params(axis='y', labelcolor=duration_axis_color)

    axs_server['traffic'].set_ylabel('Traffic [MByte]', color=traffic_axis_color)
    axs_server['traffic'].set_yscale('log')
    axs_server['traffic'].set_ylim([1e-3, 1e4])
    major_ticks = matplotlib.ticker.LogLocator(base=10,numticks=12)
    axs_server['traffic'].yaxis.set_major_locator(major_ticks)
    minor_ticks = matplotlib.ticker.LogLocator(base=10.0,subs=np.arange(0.1,1,0.1),numticks=12)
    axs_server['traffic'].yaxis.set_minor_locator(minor_ticks)
    axs_server['traffic'].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    axs_server['traffic'].tick_params(axis='y', labelcolor=traffic_axis_color)

    basename = 'IKV'
    if args['networking']:
        basename += '_networking'
    fig_client.savefig(f'plots/{basename}_client.pdf', bbox_inches='tight')
    fig_server.savefig(f'plots/{basename}_server.pdf', bbox_inches='tight')
    json_dump(basename, aggregated_durations, aggregated_traffic)


def print_client_runtime(aggregated_durations):
    runtime = {}

    for client_id in range(6):
        for encryption in ['clear', 'fhe']:
            client = f'client{client_id}'
            runtime.setdefault(encryption, {})

            total_runtime = 0
            total_runtime += aggregated_durations[f'IKV-{encryption}']['6'][f'client{client_id}']['setup']['avg']
            total_runtime += aggregated_durations[f'IKV-{encryption}']['6'][f'client{client_id}']['computation']['avg']

            max_confidence = max(
                aggregated_durations[f'IKV-{encryption}']['6'][client]['setup']['conf'],
                aggregated_durations[f'IKV-{encryption}']['6'][client]['computation']['conf']
            )

            runtime[encryption].setdefault('runtime', {})
            runtime[encryption]['runtime'].setdefault('values', [])
            runtime[encryption]['runtime']['values'].append(total_runtime)
            runtime[encryption].setdefault('max_confidence', {})
            runtime[encryption]['max_confidence'].setdefault('values', [])
            runtime[encryption]['max_confidence']['values'].append(max_confidence)

    for encryption in runtime:
        for label in runtime[encryption]:
            values = runtime[encryption][label]['values']
            del runtime[encryption][label]['values']
            runtime[encryption][label] = np.mean(values)

    print(runtime)



def main(arguments):

    global args
    args = arguments

    if 'logdir' not in args:
        raise ValueError('Argument \'logdir\ not defined')
    logdir = os.path.abspath(args['logdir'])
    if not os.path.isdir(logdir):
        raise ValueError(f'Argument \'logdir\' defines non-existing directory {logdir}')

    global re_logfile
    re_logfile = re.compile(logdir + r'/log-(?P<date>\d{8}-\d\dh\d\dm\d\ds)_s-(?P<scenario>[a-zA-Z-]+)(_pm-(?P<parameter>[\w-]+))?_r-(?P<run>\d+)_p-(?P<program>[a-zA-Z-]+)(?P<execution>\d*)_t-(?P<logtype>[\w-]+).log')

    durations = get_durations(logdir)
    aggregated_durations = aggregate_durations(durations)

    traffic = get_traffic(logdir)
    aggregated_traffic = aggregate_traffic(traffic)

    global figure_width
    global figure_height
    figure_width = 241.14749 * 0.03514# IEEE column width
    figure_height = 2.5

    plt.rcParams.update({'font.size': 12})

    if not 'scenario' in args:
        raise ValueError('Argument \'scenario\' not defined')

    if args['scenario'] in ['benchmark', 'nested', 'IKV', 'network']:
        scenarios = [args['scenario']]
    elif args['scenario'] in ['all']:
        scenarios = ['benchmark', 'nested', 'IKV']
    else:
        raise ValueError(f'Invalid scenario \'{args["scenario"]}\'')

    if not 'networking' in args:
        raise ValueError('Argument \'networking\' not defined')

    if 'benchmark' in scenarios:
        plot_benchmark(aggregated_durations, aggregated_traffic)
    if 'nested' in scenarios:
        plot_nested(aggregated_durations, aggregated_traffic)
    if 'IKV' in scenarios:
        plot_IKV(aggregated_durations, aggregated_traffic)
    if 'network' in scenarios:
        print_client_runtime(aggregated_durations)

    plt.show()


if __name__ == '__main__':

    parser = argparse.ArgumentParser('Plot performance results')
    parser.add_argument('-l', '--logdir', type=str, default='.', help='Specify the directory holding the evaluation logs (default: \'.\')')
    parser.add_argument('-n', '--networking', action='store_true', help='Plot networking time')
    parser.add_argument('-s', '--scenario', type=str, default='all', help='Specify the scenario to be plottedt (default: \'all\')')

    args = vars(parser.parse_args())

    main(args)
