# -*- coding: utf-8 -*-

# basic setup class types
from nnsim.module         import Module, ModuleList
from nnsim.nnsimChannel   import Channel as Ch
from nnsim.nnsimRecorder  import nnsimRecorder

# class types depending on the model
from arithmetic               import mac
from sp                       import WeightsSP

# =======================================================================  
#       1. there are three types of scratchpad memory: weights, ifmap, psum
#       2. each scrachpad has only one bank 
#       3. there is only one MAC in the PE
# =======================================================================  

class PE(Module):
    
    def instantiate(self, setup):
        
        self.class_name = 'PE'
        self.row = setup['row']
        self.col = setup['col']
        self.debug = 'PE[' + str(self.row) + ']' + '[' + str(self.col) + ']'
        
        # ================================================================
        # Stats Related Setup 
        # ================================================================
        self.component_class_specification_stats  = 'hide'
        self.component_specification_stats        = 'show'
        self.access_counts_stats                  = 'show'
        self.recorder                             = nnsimRecorder()\
                                                    if self.traces_stats == 'show'\
                                                    else None
        # =================================================================
        # IO Channels
        # =================================================================
        self.weights_data_in_chn      = ModuleList(setup['weights_data_in_chn'])
        self.ifmap_data_in_chn        = ModuleList(setup['ifmap_data_in_chn'])
        self.psum_data_in_chn         = ModuleList(setup['psum_data_in_chn'])
        self.psum_data_out_chn        = ModuleList(setup['psum_data_out_chn'])
        
        # =================================================================
        # Hardware components 
        # =================================================================
        # >>>> weights scratchpad (reg)
        self.weights_reader = ModuleList(Ch())
        weights_sp_setup = {'fill_data_ichns':      self.weights_data_in_chn,\
                            'drain_data_ochns':     self.weights_reader,\
                            'num_logical_managers': 1,\
                            'SRAM':                 {'depth':      setup['wsp_depth'],\
                                                     'width':      setup['wsp_width'],\
                                                     'data_width': setup['wsp_data_width'],\
                                                     'nports':     setup['wsp_nports'],\
                                                     'nbanks':     setup['wsp_nbanks'], \
                                                     'port_type':  setup['wsp_port_type']},\
                            'debug':                 self.debug + '_weights_sp'}
        
        self.weight_sp  = WeightsSP(weights_sp_setup)
        
        
        # >>>> mac unit
        mac_setup = {'opa_chn':     self.ifmap_data_in_chn[0],\
                     'opb_chn':     self.weights_reader[0], \
                     'opc_chn':     self.psum_data_in_chn[0],\
                     'result_chn':  self.psum_data_out_chn[0],\
                     'latency':     setup['mac_latency'],\
                     'debug':       self.debug} 
        
        self.mac = mac(mac_setup)
        
        
    def configure(self, config):
        weights_sp_config                       = config['WeightsSp']
        weights_sp_config['shape_mapping_info'] = config['shape_mapping_info']
        self.weight_sp.configure(weights_sp_config)
        
        self.clk_gated                          = config['clk_gated']
        self.mac.configure({'clk_gated': self.clk_gated})
        


        
       
        