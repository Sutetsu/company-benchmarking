import traffic

@traffic.traffic_function('foo', 80)
def foo():
    time.sleep(1)

if __name__ == '__main__':
    traffic.traffic_start('init', 80)
    time.sleep(1)
    traffic.traffic_stop(d)

    foo()

    print(traffic.get_traffic())
