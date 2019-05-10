import sys,os
from yaml import load
import math


def calculate(info):
    attr = info['attributes']
    action_args = None if 'arguments' not in info else info['arguments']
     
    if action_args is None:
        # idle
        return 0
    else:
        entry = (action_args['nread'], action_args['nwrite'], action_args['nrepeated_read'], action_args['nrepeated_data_write'])
        
        # component is not switching
        if entry  == (0,0,0,0):
            return 0
        
        if attr['depth'] == 1 and attr['width'] == 1 and attr['data_width']== 8:
            # weight sp
            return 1
        elif attr['width'] == 2 and attr['data_width'] == 8:
            # global buffers
            energy = math.ceil(math.log(attr['depth'])/math.log(50) * 10)
            return energy
    
    


if __name__ == '__main__':
    
    info = sys.stdin.read()
    value = calculate(info)
    sys.stdout.write(str(value))

