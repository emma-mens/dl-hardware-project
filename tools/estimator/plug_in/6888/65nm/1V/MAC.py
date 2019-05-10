#!/homes/nelliewu/anaconda3/bin/python

import sys

def calculate(info):

    action_name = info['action_name']
    
    if action_name == 'mac_normal':
        return 5
    elif action_name == 'mac_reuse':
        return 5
    elif action_name == 'mac_gated':
        return 0
    else:
        return 0


if __name__ == '__main__':
    
    info = sys.stdin.read()
    value = calculate(info)
    sys.stdout.write(str(value))

