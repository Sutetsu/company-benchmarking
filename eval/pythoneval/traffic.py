import pythoneval.enable
import subprocess
import shlex
import os
import functools

# global variables
active_measurement = None
all_traffic = {}

class TraffcException(Exception):
    pass

class Traffic:
    USE_TCPDUMP = False # Warning, when not using tcpdump, measurement is per interface, not per (interface, port)
    MEASUREMENT_FILE = './traffic_measurement.tcpdump'

    def __init__(self, label, port, interface='lo'):
        if not isinstance(port, int):
            raise TypeError(f'Given \'port\' must be of type \'int\' (found type \'{type(port)})\'')

        if not port in range(1, 65536):
            raise ValueError(f'Given \'port\' {port} must be in range [1,65535]')

        if not isinstance(label, str):
            raise TypeError(f'Given \'label\' must be of type \'str\' (found type \'{type(label)})\'')

        if not isinstance(interface, str):
            raise TypeError(f'Given \'interface\' must be of type \'str\' (found type \'{type(interface)})\'')

        self.label = label
        self.port = port
        self.interface = interface
        self.popen = None
        self.start = None

    def measure_start(self):
        if self.popen or self.start:
            return

        if Traffic.USE_TCPDUMP:
            cmd = shlex.split(f'tcpdump -i {self.interface} port {self.port} -w {Traffic.MEASUREMENT_FILE}')
            self.popen = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        else:
            with open(f'/sys/class/net/{self.interface}/statistics/rx_bytes', 'r') as fd:
                self.start = int(fd.read().rstrip())

    def measure_stop(self):
        if Traffic.USE_TCPDUMP:

            if not self.popen:
                raise TraffcException('Traffic measurement has not been started before')

            self.popen.terminate()
            self.popen.wait()

            traffic_bytes = os.path.getsize(Traffic.MEASUREMENT_FILE)
            os.remove(Traffic.MEASUREMENT_FILE)

            self.popen = None

        else:
            if not self.start:
                raise TraffcException('Traffic measurement has not been started before')

            with open(f'/sys/class/net/{self.interface}/statistics/rx_bytes', 'r') as fd:
                stop = int(fd.read().rstrip())

        return stop - self.start


def traffic_start(label, port, interface='lo'):
    global active_measurement

    if not pythoneval.enable.measurements_enabled:
        return

    if active_measurement:
        raise TraffcException('Traffic measurement already running, multiple measurements currently not supported')

    active_measurement = Traffic(label, port, interface=interface)
    active_measurement.measure_start()


def traffic_stop():
    global active_measurement

    if not pythoneval.enable.measurements_enabled:
        return

    if not active_measurement:
        return

    traffic_bytes = active_measurement.measure_stop()

    all_traffic.setdefault(active_measurement.label, [])
    all_traffic[active_measurement.label].append(traffic_bytes)

    active_measurement = None


def traffic_function(label, port, interface='lo'):
    def _traffic_function(f):
        @functools.wraps(f)
        def __traffic_function(*args, **kwargs):

            traffic_start(label, port, interface=interface)
            result = f(*args, **kwargs)
            traffic_stop()

            return result
        return __traffic_function
    return _traffic_function


def get_traffic():
    result = {}

    for label in all_traffic:
        for traffic_bytes in all_traffic[label]:
            result.setdefault('__overall', 0)
            result['__overall'] += traffic_bytes

            result.setdefault(label, 0)
            result[label] += traffic_bytes

    return result


def write_traffic(filename=None, forceOutput=False):
    import __main__
    import json

    if (not all_traffic) and (not forceOutput):
        # no traffic measurements
        return

    if not filename:
        if '__file__' in dir(__main__):
            base = os.path.splitext(os.path.basename(__main__.__file__))[0] + '_traffic'
        else:
            base = 'traffic'

        filename = base + '.log'

    try:
        dirname = os.path.dirname(filename)
        if not dirname:
            dirname = '.'

        if not os.path.exists(dirname):
            raise ValueError()
    except:
        raise ValueError(f'Given \'filename\' contains no valid path (found filename \'{filename}\')')

    traffic = get_traffic()

    with open(filename, 'w') as fd:
        json.dump(traffic, fd)


def write_traffic_after_function(filename=None, forceOutput=False):
    def _write_traffic_after_function(f):
        @functools.wraps(f)
        def __write_traffic_after_function(*args, **kwargs):
            result = f(*args, **kwargs)
            write_traffic(filename, forceOutput)
            return result
        return __write_traffic_after_function
    return _write_traffic_after_function
