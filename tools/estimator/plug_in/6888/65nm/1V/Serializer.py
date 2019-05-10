
import sys

def calculate(info):
    action_name = info['action_name']
    if action_name == 'idle':
        return 0
    else:
        return 1


if __name__ == '__main__':
    
    info = sys.stdin.read()
    value = calculate(info)
    sys.stdout.write(str(value))