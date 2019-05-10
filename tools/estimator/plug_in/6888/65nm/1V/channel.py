#!/homes/nelliewu/anaconda3/bin/python

import sys

def calculate(info):
    return 0


if __name__ == '__main__':
    
    info = sys.stdin.read()
    value = calculate(info)
    sys.stdout.write(str(value))
