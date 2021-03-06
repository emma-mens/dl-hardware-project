# -*- coding: utf-8 -*-
from nnsim.nnsimAddressGenerator import nnsimAddressGenerator as AG
import math

# ================================================================================================================
#
#  Address Generators for various buffering unit
#     Approach:
#           certain various are controlled by the index of the pixel
#           while incrementing the pixel index, update the variable
#     Drop:
#           only drop data for count and freeze
#           since they are the end of a "addressing sequence"
#           easier action generation
#    Action generated  in runtime and passed to smartbuffer
#           amount of buffering depends the depth of the channels connecting the generators and smartbuffer
#
#================================================================================================================


class WeightsSpFillAG(AG):
    def instantiate(self, setup):
        AG.instantiate(self, setup)
        self.class_name       = 'weights_sp_fill_addr_generator'
        self.predefined_class = True
        self.base_class_name  = 'AddressGenerator'
        
    def configure(self, config):
        
        self.S = config['shape']['S']    # number of filter cols
        self.R = config['shape']['R']
        self.M = config['shape']['M']    # number of output channels
        self.N = config['shape']['N']    # number of output images
        self.C = config['shape']['C']


        self.k = config['mapping']['C0'] # number of tile input channels
        self.m = config['mapping']['M0'] # number of tile output channels
        self.n = config['mapping']['N0'] # number of tile ifmaps

        # number of passes each PE needs to perform
#        self.nreset = self.m // (self.p * self.t) * \
#                      self.k // (self.q * self.r) * \
#                      self.C // self.k *\
#                      self.M // self.m *\
#		             self.N // self.n
#                      
        self.set     = False
        self.count   = False
        self.params  = {'count_max': self.S * self.R  - 1 }
        AG.configure(self)

    def get_next_action(self):
        
        action = []
        
        if self.set and self.count:
            # >> each combo of set and count is a pass of data 
            self.set = False
            self.count = False
#            print(self.debug, 'finishes filling a input tile')
            return ('reset_phead',{})  # no more action needed
            
        if not self.set:
            action = ('Set', {'action_config': {'addr': 0}})
            self.set = True
            return action
        else:
            nsteps = self.S * self.R - 1
            action = ('Count', {'action_config': {},
                                'round_meta': {'nsteps': nsteps}})
            self.count = True
            return action    


class WeightsSpDrainAG(AG):
    def instantiate(self, setup):

        AG.instantiate(self, setup)
        self.class_name       = 'weights_sp_drain_addr_generator'
        self.predefined_class = True
        self.base_class_name  = 'AddressGenerator'
        

    def configure(self, config):
        
        self.S = config['shape']['S']    # number of filter cols
        self.R = config['shape']['R']    # number of filter rows
        self.H = config['shape']['H']
        self.W = config['shape']['W']
        self.E = config['shape']['E']    # number of ofmap rows
        self.F = config['shape']['F']    # number of ofmap cols
        self.M = config['shape']['M']    # number of output channels
        self.N = config['shape']['N']    # batch size
        self.C = config['shape']['C']    # number of input channels
        self.U = config['shape']['U']    # stride

        self.k = config['mapping']['C0'] # number of tile input channels
        self.m = config['mapping']['M0'] # number of tile output channels
        self.n = config['mapping']['N0'] # number of tile ifmaps
        
        self.e = math.ceil((self.H - self.R + 1) /self.U) 
        self.f = math.ceil((self.W - self.S + 1) /self.U) 

        # number of passes each PE needs to perform
        self.nreset = math.ceil(self.C / self.k) *\
                      math.ceil(self.M / self.m) *\
		             math.ceil(self.N / self.n) 
        
        self.new_pass_config()
        
        AG.configure(self)
        
        self.nrepeat = self.e * self.f * self.n
        self.params  = {'count_max':  self.nrepeat - 1 }

    def new_pass_config(self):
        
        self.set   = False
        self.count = False
        
        # current location of the weight pixel in 2D space
        self.curr_row = 0
        self.curr_col = 0
        
    def get_next_action(self):
        action = []
        if self.curr_row == self.R:
            self.new_pass_config()
#            print(self.debug, 'finish draining an input tile')
            return ('reset_phead',{})
        
        if not self.set:
            action = ('Set', {'action_config': {'addr': 0},\
                              'round_meta': {'ndrop': 0, 'prereq': 'fill'}})
            self.set = True
        else:
            nsteps = self.nrepeat - 1
            action = ('Freeze', {'action_config':{},\
                                 'round_meta': {'nsteps': nsteps, 'prereq': 'fill', 'ndrop': 1}})
            self.count = True 
            
        if self.set and self.count:
           self.set = False
           self.count = False
           self.curr_col += 1
           if self.curr_col == self.S:
               self.curr_col = 0
               self.curr_row += 1
        return action





