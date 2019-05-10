# -*- coding: utf-8 -*-

import os, sys
from yaml import dump
from estimator.utility.ee_yaml_parser import ee_dumper

def create_folder(directory):
    
    ''' create a new folder if not exist '''
    
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('ERROR: Creating directory. ' +  directory)
        sys.exit()
        
    
def write_yaml_file(filepath, content):
    
    ''' os invloved yaml dumping
    
        - new directory (if does not exsit) will be made
        - the exsiting file with same name will be removed
    '''
    
    if os.path.exists(filepath):
        os.remove(filepath)
        
    create_folder(os.path.dirname(filepath))  
      
    out_file = open(filepath, 'a')
    
    out_file.write(dump( content, \
                         default_flow_style=False, \
                         Dumper= ee_dumper))        
    
def remove_qoutes_yaml(filepath):
   
    ''' remove the uncessary qoutes in the yaml files 
    
        - make sure the ! commands can be interpreted by the loader
    
    '''
   
    if os.path.exists(filepath):
        new_content = ''
        f = open(filepath, 'r')
        
        for line in f:
            if '\'' in line:
                line = line.replace('\'', '')
                new_content += line
        f.close()
        os.remove(filepath)
        newf = open(filepath, 'w')
        newf.write(new_content)
        newf.close()
                