#!/homes/nelliewu/anaconda3/bin/python

import sys

def calculate(info):
    attrs = info['attributes']
    if   attrs['count_max'] > 1:
        # glb addr generators
        return 1
    else:
        # weight sp addr generator
        return 0



if __name__ == '__main__':
    
    info = sys.stdin.read()
    value = calculate(info)
    sys.stdout.write(str(value))