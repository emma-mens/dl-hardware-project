from yaml import dump
import os, sys

def write_yaml_file(filepath, content):
    
    
    if os.path.isfile(filepath):
        os.remove(filepath)
        
      
    out_file = open(filepath, 'a')
    
    out_file.write(dump( content, \
                         default_flow_style=False))    


