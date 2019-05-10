# -*- coding: utf-8 -*-

from nnsim.module import Module
from yaml import load
from nnsim.nnsimUtil import sim_loader
import numpy as np
import os

class TestbenchError(Exception):
    pass

class nnsimTestBench(Module):
    def instantiate(self, setup):
        self.class_name          = 'nnsim_test_bench'
        self.record_class_stats  = True
        
        self.layer_name        = setup['layer_name']
        self.layer             = self.layer_name[0:-5]
        self.mapping_name      = setup['mapping_name']
        self.architectue_name  = setup['architecture_name']
        
        
#        shape_path             = os.path.normpath('../../../../workloads/layer_shapes/' + self.layer_name)   
#        mapping_path           = os.path.normpath('../../mappings/' + self.mapping_name)
#        arch_path              = os.path.normpath('../../arch_parameters/' + self.architectue_name )
#        ifmap_data_path        = os.path.normpath('../../../../workloads/ifmap_data/' + setup['ifmap_data_name'])
#        weights_data_path      = os.path.normpath('../../../../workloads/weights_data/' + setup['weights_data_name'])
        
        
        shape_path         = self.layer_name
        mapping_path       = self.mapping_name
        arch_path          = self.architectue_name
        ifmap_data_path    = setup['ifmap_data_name']
        weights_data_path  = setup['weights_data_name']

        bias_data          = setup['bias_data_name']
        
        print(shape_path)
        self.shape         = load(open(shape_path),sim_loader)
        self.mapping       = load(open(mapping_path),sim_loader)
        self.ifmap_data    = np.load(ifmap_data_path)
        self.weights_data  = np.load(weights_data_path)
        self.bias_data     = np.load(bias_data)
        self.arch          = load(open(arch_path))
        
        
        # ================================================================
        # Stats Related Setup (common setup for the test bench)
        # ================================================================
        self.component_class_specification_stats     = 'hide'
        self.access_counts_stats                     = 'hide'
        self.component_specification_stats           = 'hide'    
                
 





        
          