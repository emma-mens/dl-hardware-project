# -*- coding: utf-8 -*-
import os, sys, yaml

# ----------------------------------------------------------------------
# util function that creates a folder if not exist
# ----------------------------------------------------------------------     
def create_folder(directory):
    
    ''' create a new folder if not exist '''
    
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('ERROR: Creating directory. ' +  directory)
        sys.exit()

# ----------------------------------------------------------------------
# YAML dumper that eliminate alias pointers in the dumped file
# ----------------------------------------------------------------------
class sim_dumper(yaml.Dumper):
    def ignore_aliases(self, data):
        return True

# ----------------------------------------------------------------------
# YAML loader that recognizes the !include command
# ----------------------------------------------------------------------
class sim_loader(yaml.SafeLoader):    
    def __init__(self, stream):
        
        self._root = os.path.split(stream.name)[0]
        super(sim_loader, self).__init__(stream)

def include_constructor(self, node):
    filepath = self.construct_scalar(node)
    if filepath[-1] == ',':
        filepath = filepath[:-1]
    filename = os.path.join(self._root, filepath )
    with open(filename, 'r') as f:
        return yaml.load(f, sim_loader)
    
yaml.add_constructor('!include', include_constructor, sim_loader)    