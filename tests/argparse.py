import argparse

if __name__ == '__main__':
    print('-'*20)
    parser = argparse.ArgumentParser('Arg parser test')
    parser.add_argument('-a', '--abascus', action='store_true', help='Flag')
    parser.add_argument('-b', '--beans', type=str, default='.', help='String')
    parser.add_argument('-c', '--celestial', type=int, default=1, help='Int')
    
    print('-'*20)

    args = vars(parser.parse_args())
    print(args['abascus'])
    print(args['beans'])
    print(args['celestial'])