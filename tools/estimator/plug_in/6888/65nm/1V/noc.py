 
import sys

def calculate(info):
    action_name = info['action_name']
    if action_name == 'transfer':
        return 10
    else:
        return 0


if __name__ == '__main__':
    
    info = sys.stdin.read()
    value = calculate(info)
    sys.stdout.write(str(value))