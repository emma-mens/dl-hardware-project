# -*- coding: utf-8 -*-

# the sepcialized PyYaml loader with addintional custom parsing:
#      1) !include: loads another yaml file into the the current file

import os
import yaml

# ===================================
#   Energy Estimator YAML Loader
# ===================================
class ee_loader(yaml.SafeLoader):    
    def __init__(self, stream):
        
        self._root = os.path.split(stream.name)[0]
        super(ee_loader, self).__init__(stream)

# =========================================================================================
#   !inldue relative_file_path
#   loads the file from relative_file_path and inser the values into the original file   
# =========================================================================================
def include_constructor(self, node):
    filepath = self.construct_scalar(node)
    if filepath[-1] == ',':
        filepath = filepath[:-1]
    filename = os.path.join(self._root, filepath )
    with open(filename, 'r') as f:
        return yaml.load(f, ee_loader)

yaml.add_constructor('!include', include_constructor, ee_loader)

# ===================================
#   Energy Estimator YAML Dumper
# ===================================

class ee_dumper(yaml.SafeDumper):
    
    def ignore_aliases(self, _data):
        return True




