# -*- coding: utf-8 -*-
from nnsim.nnsimUtil import create_folder

class nnsimRecorder():
    
    def __init__(self, enable = False):
        self.records   = {}
        
    def record(self, filename, value):
        
        if filename in self.records.keys():
            self.records[filename] += str(value) + '\n'
        else:
            self.records[filename] = str(value) + '\n'
   
    def dump_records (self, root_dir):
        
        for filename, filecontent in self.records.items():
            f = open(root_dir + filename, 'a+')
            f.write(filecontent)
            f.close()            
        
        
        
        