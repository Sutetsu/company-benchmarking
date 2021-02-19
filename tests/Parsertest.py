import argparse

if __name__ == '__main__':
    print('-'*20)
    parser = argparse.ArgumentParser('Run performance evaluation')
    parser.add_argument('-c', '--codebase', type=str, default='..', help='Path to the code base or code repository (default: \'..\')')
    parser.add_argument('-d', '--docker', action='store_true', help='Set flag to execute system within a docker container')
    parser.add_argument('-l', '--logdir', type=str, default='.', help='Specify the directory for storing evaluation logs (default: \'.\')')
    parser.add_argument('-s', '--scenario', type=str, default='_test', help='Define a scenario or a scenario class to use for the current measurement (default: \'_test\')')
    parser.add_argument('-r', '--runs', type=int, default=1, help='Number of measurement runs to perform (default: 1)')
    
    print('*'*20)
    print(args[logdir])

    args = vars(parser.parse_args())