import pythoneval.enable
import time
import functools

# global variables
all_durations = {}

class DurationException(Exception):
    pass


class Duration:

    def __init__(self, labels, exclude=False, considerOverall=True):
        if not isinstance(labels, list):
            raise TypeError(f'Given \'label\' must be of type \'list\' (found type \'{type(label)})\'')

        if not isinstance(exclude, bool):
            raise TypeError(f'Given \'exclude\' must be of type \'bool\' (found type \'{type(exclude)}\')')

        if not isinstance(considerOverall, bool):
            raise TypeError(f'Given \'considerOverall\' must be of type \'bool\' (found type \'{type(considerOverall)}\')')

        self.labels = labels
        self.exclude = exclude
        self.considerOverall = considerOverall
        self.start = None
        self.stop = None

    def measure_start(self, t=None):
        if self.start:
            raise DurationException(f'Duration measurement has already been started at {self.start} (current time: {t}, label: \'{self.label}\')')

        if t is None:
            t = time.monotonic()

        self.start = t

    def measure_stop(self, t=None, override=False):
        if t is None:
            t = time.monotonic()

        if self.stop and not override:
            raise DurationException(f'Duration measurement has already been stopped at {self.stop} (current time: {t}, label: \'{self.label}\')')

        self.stop = t

    def get_duration(self):
        if not self.start:
            raise DurationException(f'Start point for duration \'{self.labels}\' not set')

        if not self.stop:
            raise DurationException(f'Stop point for duration \'{self.labels}\' not set')

        sign = 1
        if self.exclude:
            sign = -1

        return sign * (self.stop - self.start)


# Start a duration measurement associated with a given 'label'. To explicitly substract this duration
# from the overall duration for 'label' and '__overall', set 'exclude' to True. To not consider this
# duration for the calculation of the '__overall' duration, set 'considerOverall' to False.
# Returns the newly created Duration object.
def duration_start(labels=None, exclude=False, considerOverall=True):
    if not pythoneval.enable.measurements_enabled:
        return

    if labels is None:
        labels = ['__all']

    if not isinstance(labels, list):
        labels = [labels]

    duration_obj = Duration(labels, exclude=exclude, considerOverall=considerOverall)
    for label in labels:
        all_durations.setdefault(label, [])
        all_durations[label].append(duration_obj)
    duration_obj.measure_start()
    return duration_obj

duration_exclude_start = lambda labels : duration_start(labels, exclude=exclude)


# Stop a duration measurement. 'duration_specifier' may either be a Duration object or a previously used label.
# If 'duration_specifier' is a previously used label, it refers to the last created Duration object with this
# label.
def duration_stop(duration_specifier=None, override=False):
    stop_time = time.monotonic()

    if not pythoneval.enable.measurements_enabled:
        return

    if duration_specifier is None:
        duration_specifier = ['__all']

    if isinstance(duration_specifier, Duration):
        duration_specifier.measure_stop(t=stop_time, override=override)
    else:
        if not isinstance(duration_specifier, list):
            duration_specifier = [duration_specifier]

        for label in duration_specifier:
            try:
                all_durations[label][-1].measure_stop(t=stop_time, override=override)
                break # break for-loop since we must only stop each Duration object once
            except (KeyError, IndexError):
                raise DurationException(f'Given label is not a previously used label: {label}')

duration_exclude_stop = duration_stop


# Decorator for measuring execution durations of entire fuctions
# Usage: @duration_function()
def duration_function(label=None, exclude=False):
    def _duration_function(f):
        @functools.wraps(f)
        def __duration_function(*args, **kwargs):
            measure_label = label
            if not measure_label:
                measure_label = f.__name__

            duration_obj = duration_start(measure_label, exclude)
            result = f(*args, **kwargs)
            duration_stop(duration_obj)

            return result
        return __duration_function
    return _duration_function


# Calculate the overall measured duration and the individual overall duration for each used label.
# Return a dictionary with the according results.
def get_duration():
    result = {}

    for label in all_durations:
        for duration_obj in all_durations[label]:
            try:
                if duration_obj.considerOverall:
                    result.setdefault('__overall', 0)
                    result['__overall'] += duration_obj.get_duration()

                result.setdefault(label, 0)
                result[label] += duration_obj.get_duration()
            except DurationException as e:
                print(e)

    if '__all' in result:
        for label in result:
            if label not in ['__all', '__overall']:
                result[label] += result['__all']

        del result['__all']

    return result


# Write the gathered duration measurement in JSON format to 'filename'
def write_duration(filename=None, forceOutput=False):
    import __main__
    import os
    import json

    if (not all_durations) and (not forceOutput):
        # no duration measurements
        return

    if not filename:
        if '__file__' in dir(__main__):
            base = os.path.splitext(os.path.basename(__main__.__file__))[0] + '_duration'
        else:
            base = 'duration'

        filename = base + '.log'

    try:
        dirname = os.path.dirname(filename)
        if not dirname:
            dirname = '.'

        if not os.path.exists(dirname):
            raise ValueError()
    except:
        raise ValueError(f'Given \'filename\' contains no valid path (found filename \'{filename}\')')

    durations = get_duration()

    with open(filename, 'w') as fd:
        json.dump(durations, fd)


# Decorator for writing the gathered duration measurement after the regarding function
# Usage: @write_duration_after_function()
def write_duration_after_function(filename=None, forceOutput=False):
    def _write_duration_after_function(f):
        @functools.wraps(f)
        def __write_duration_after_function(*args, **kwargs):
            result = f(*args, **kwargs)
            write_duration(filename, forceOutput)
            return result
        return __write_duration_after_function
    return _write_duration_after_function
