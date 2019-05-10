from nnsim.module import Module
from nnsim.nnsimChannel import Channel
from nnsim.nnsimNoC import nnsimNoC
from nnsim.nnsimBCNoC import nnsimBCNoC
from nnsim.nnsimDeserializer import nnsimDeserializer
import numpy as np
import math
INT_32_MAX = 2147483647

# read NoC means data comes out in order and out in order
# write network means there is randomness invovled in the outgoing data's order
#       i.e. an associated address needs to be proveded and pused into an addr channel

class WeightsNoC(nnsimNoC):
    
    def instantiate(self, setup):
        nnsimNoC.instantiate(self, setup)
        self.class_name = 'WeightsNoC'
        # -----------------------------------------------
        # Flags for Stats Collection
        # ------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
        self.attrs = {'data_width':  8,\
                      'nRequesters': 1,\
                      'FIFO_width': 8,\
                      'FIFO_depth': 2}
        self.predefined_class                      = True
        self.base_class_name                       = 'noc'
class IFMapNoC(nnsimNoC):
    
    def instantiate(self, setup):
        nnsimNoC.instantiate(self, setup)
        self.class_name = 'IFMapNoC'
        #======================================================================
        #                  Stats Collection Info
        #======================================================================  
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
        self.attrs = {'data_width':  8,\
                      'nRequesters': 1,\
                      'FIFO_width': 8,\
                      'FIFO_depth': 2}
        self.predefined_class                      = True
        self.base_class_name                       = 'noc'
class PsumRdNoC(nnsimNoC):
    
    def instantiate(self, setup):
        nnsimNoC.instantiate(self, setup)
        self.class_name = 'PsumRdNoC'
        #======================================================================
        #                  Stats Collection Info
        #======================================================================  
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
        self.attrs = {'data_width':  8,\
                      'nRequesters': 1,\
                      'FIFO_width': 8,\
                      'FIFO_depth': 2}
        self.predefined_class                      = True
        self.base_class_name                       = 'noc'
class PsumWrNoC(Module):
    
    def instantiate(self, setup):
        self.class_name              = 'PsumWrNoC'
        self.rd_chns                 = setup['rd_chns']
        self.wr_chns                 = setup['wr_chns']
        self.debug                   = setup['debug']
 
        self.pe_array_to_deseri_chn  = Channel()
        self.deserialized_data_chn   = Channel()
        
        self.deseri_ratio            = 2
        
        self.deserializer            = nnsimDeserializer({'in_chn':  self.pe_array_to_deseri_chn, \
                                                          'out_chn': self.deserialized_data_chn,\
                                                          'ratio':   self.deseri_ratio,\
                                                          'debug':   'psum_deserializer'})
        #======================================================================
        #                  Stats Collection Info
        #======================================================================  
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'  
        self.attrs = {'data_width':  8,\
                      'nRequesters': 1,\
                      'FIFO_width': 8,\
                      'FIFO_depth': 2}
        self.predefined_class                      = True
        self.base_class_name                       = 'noc'
    def configure(self, config):
        self.mapping                 = config['mapping']
        self.shape                   = config['shape']
        
        # 2D shape of the datatype
        self.S                       = config['shape']['S']  # number of filter cols 
        self.W                       = config['shape']['W']  # number of ifmap cols
        self.F                       = config['shape']['F']  # number of ofmap cols
        
        self.R                       = config['shape']['R']  # number of filter rows
        self.H                       = config['shape']['H']  # number of ifmap  rows
        self.E                       = config['shape']['E']  # number of ofmap  rows 
        
        self.N                       = config['shape']['N']  # total number of ifmaps
        self.M                       = config['shape']['M']  # total number of filters
        self.C                       = config['shape']['C']  # total number of input channels
        
        self.U                       = config['shape']['U']  # stride size
        
        # mapping parameters needed 
        self.k                    = config['mapping']['C0'] # number of tile input channels
        self.m                    = config['mapping']['M0'] # number of tile output channels
        self.n                    = config['mapping']['N0'] # number of tile ifmaps
        self.e                    = math.ceil((self.H - self.R + 1) /self.U) 
        self.f                    = math.ceil((self.W - self.S + 1) /self.U)   
        
        self.n_in_chn_tile        = math.ceil(self.C / self.k)
        self.n_out_chn_tile       = math.ceil(self.M / self.m)
        self.n_batch_tile         = math.ceil(self.N / self.n)
        
        self.curr_data_to_be_deseri = 0
        self.curr_data_out        = 0
        self.curr_out_chn         = 0
        self.curr_weights_col     = 0
        self.curr_weights_row     = 0
        self.curr_in_chn_tile     = 0
        self.curr_out_chn_tile    = 0
        self.curr_batch_tile      = 0
        self.layer_done           = False
  
        self.deserializer.configure()
        self.configure_new_out_tile()
        
        
    def configure_new_out_tile(self):
        self.curr_out_chn_to_be_deseri = 0
        self.curr_batch_to_be_deseri = 0
#        print('################### WrNoC my_m:', self.my_m, 'curr_out_chn_tile:', self.curr_out_chn_tile)
        
        
# for each input tile, going through a round of weight pixels means each output partial sum is completely accumulated one more time
# at the last weight pixel (every single ofmap data needs to accumulate until the last weight pixel), and the last input tile, 
# the computed data should be able to go out
    def tick(self):
        update_index_GLB = False
        update_index_offchip = False
        if self.layer_done:
#            print(self.debug, 'layer done')
            return
        curr_pe_col = self.curr_data_to_be_deseri % self.m
        
        total_to_glb = math.ceil(self.m * self.n * self.f * self.e / self.deseri_ratio) * self.deseri_ratio
        if self.curr_data_to_be_deseri < total_to_glb and self.pe_array_to_deseri_chn.vacancy():
            if self.curr_data_to_be_deseri < self.m * self.n * self.f * self.e: 
                if self.wr_chns[self.k][curr_pe_col].valid() :
                    computed_data = self.wr_chns[self.k][curr_pe_col].pop()
                    self.pe_array_to_deseri_chn.push(computed_data)
                    self.curr_data_to_be_deseri += 1
            else:
                self.pe_array_to_deseri_chn.push([INT_32_MAX])
                self.curr_data_to_be_deseri += 1
            
            
        if self.deserialized_data_chn.valid():
            # data needs to be pushed offchip
            if self.curr_in_chn_tile == self.n_in_chn_tile - 1 and \
               self.curr_weights_row == self.R -1 and\
               self.curr_weights_col == self.S -1:
               if self.rd_chns[1].vacancy():
                   data = [d for d in self.deserialized_data_chn.pop()]
                   self.rd_chns[1].push(data)
                   update_index_offchip = True
                   
            # data needs to go back to GLB
            else:
                if self.rd_chns[0].vacancy():
                    data = [d for d in self.deserialized_data_chn.pop()]
                    self.rd_chns[0].push(data)
                    update_index_GLB = True
#                    print('>>>', self.debug, 'pushing to GLB: ', data)
#                    print('curr_in_tile:', self.curr_in_chn_tile, 'curr_weights_row:', self.curr_weights_row, 'curr_weights_col:', self.curr_weights_col)
        
        if update_index_GLB or update_index_offchip:
            update_index_offchip = False
            update_index_GLB = False
            self.curr_data_out += self.deseri_ratio
            if self.curr_data_out == total_to_glb:
                self.curr_data_out = 0
                self.curr_data_to_be_deseri = 0
                self.curr_weights_col += 1
#                self.push_nan_to_glb = True
                if self.curr_weights_col == self.S:
                    self.curr_weights_col = 0
                    self.curr_weights_row += 1
                    if self.curr_weights_row == self.R:
                        self.curr_weights_row = 0
                        self.curr_in_chn_tile += 1
                        if self.curr_in_chn_tile == self.n_in_chn_tile:
                            self.curr_in_chn_tile = 0
                            self.curr_out_chn_tile += 1
                            self.configure_new_out_tile()
                            if self.curr_out_chn_tile == self.n_out_chn_tile:
                                self.curr_out_chn_tile = 0
                                self.curr_batch_tile += 1
                                if self.curr_batch_tile == self.n_batch_tile:
                                    self.curr_batch_tile = 0
                                    self.layer_done = True
                                        
        