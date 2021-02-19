import duration
import time

@duration.duration_function()
def foo():
    time.sleep(1)
    duration.duration_start('foo', exclude=True)
    time.sleep(1)
    duration.duration_stop('foo')
    time.sleep(1)

if __name__ == '__main__':
    d = duration.duration_start('init')
    time.sleep(1)
    duration.duration_stop(d)

    foo()

    print(duration.get_duration())
