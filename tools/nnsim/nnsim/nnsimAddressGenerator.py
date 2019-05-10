# -*- coding: utf-8 -*-

from nnsim.module import Module
from nnsim.nnsimChannel import NoLatencyChannel as NLCh
import math

class nnsimAddressGenerator(Module):
    def instantiate(self, setup):
        self.class_name       = 'nnsimAddressGenerator'
        self.predefined_class = True
        
        self.type                = setup['type']  
        self.addr_chn            = setup['addr_chn']
        self.debug               = setup['debug'] if 'debug' in setup else None
        
        # channel used to communicate the actions in run time
        self.action_chn          = NLCh()
        
        # address generation is not local
        self.out_source          = False if 'out_source' not in setup else setup['out_source']
        self.out_source_chn      = None if not self.out_source else setup['out_source_chn']
        
#        self.width               = setup['width']
#        self.width               = 4
        
        #------------------------------------------------------------------------
        # Basic Charaterization Info
        #------------------------------------------------------------------------
        self.attrs                = {'count_max': None}
        self.actions              = {'count':     None}
        self.access_stats         = {'count':     0}
        
        
        # if the number of total reset_pheads are not specified, 
        #          do stop generating addresses, only the last wave of addresses will be useless
        #          affects access counts of the address generation (if accounted independent from mem access)
        self.nreset                = math.inf

        
    def configure(self):
        
        self.reset_id              = 0
        self.all_reset_phead       = False
        self.vaddr                 = 0
        
        self.curr_action_name      = None
        self.curr_action_idx       = 0
        self.curr_action           = None
        self.action_config         = None
        self.round_meta            = None
        self.curr_step             = 0
        self.nsteps                = 0
        self.drop                  = False
        self.next_action()
        
    #-----------------------------------------------------------------------
    # increment the address by a certain stride (defualt stride is 1)
    #-----------------------------------------------------------------------
    def Count(self, config):
        step = config['stride'] if 'stride' in config else 1
        self.vaddr += step
        return self.vaddr
    #-----------------------------------------------------------------------
    # set the address to be a certain value
    #-----------------------------------------------------------------------
    def Set(self, config):        
        # offset can be either postive or negative
        
        if 'addr' in config:
            self.vaddr = config['addr']
        elif 'offset' in config:
            self.vaddr += config['offset']
        return self.vaddr

    #-----------------------------------------------------------------------
    # the coutner is idle in the freeze function   
    #-----------------------------------------------------------------------
    def Freeze(self, config):       
        return self.vaddr

    #-------------------------------------------------------------------------------------
    # reset_phead the heads and tails of the smartbuffer for a new iteration (e.g. pass, tile) 
    #-------------------------------------------------------------------------------------
    def reset_phead(self, config):
        self.vaddr = 0
        self.drop = False
        return 'reset_phead'


    def next_action(self):
    # format
    #    [(action, duration, config),(action, duration, config)... ]

        
        if self.curr_step == self.nsteps:
            
            self.curr_step = 0
            
            if self.curr_action_name == 'reset_phead':
                self.reset_id += 1
            # ----------------------------------------------------------------------------
            # there is drop in the sequence, automatically insert a update head action
            #                       this action is not from the generted action stream
            # ----------------------------------------------------------------------------
#            if self.round_meta is not None and\
#              'ndrop' in self.round_meta and\
#               self.round_meta['ndrop'] != 0:
#                   
#                self.curr_action_name  = 'shrink'
#                self.vaddr             = 0
#                self.shrink_chn.push({'ndrop': self.round_meta['ndrop']})
#                if 'ifmap' in self.debug:
#                    print(self.debug, '---------------- shrink operation')

            self.curr_action_info = self.get_next_action() 
#            ###
#            if 'ifmap' in self.debug:
#                print('>>>>', self.debug, '  ', self.curr_action_info)
            ###
            self.curr_action_name = self.curr_action_info[0]
            
#            if self.curr_action_name == 'reset_phead':
#                if self.reset_id == self.nreset:
#                    self.all_reset_phead = True
#                    if 'ifmap' in self.debug:
#                        print(self.debug, 'all reset done: id:', self.reset_id, 'nreset:', self.nreset)
#                    return

            self.curr_action = getattr(self, self.curr_action_name )
            
            # set the default action configure value
            if 'action_config' not in self.curr_action_info[1]:
                self.action_config = {}
            else:
                self.action_config = self.curr_action_info[1]['action_config'] 
            
            
            # set the default round meta and nsteps value
            if 'round_meta' not in self.curr_action_info[1]:
                self.nsteps = 1
                self.round_meta = {}
            else:
                self.round_meta = self.curr_action_info[1]['round_meta']
                self.nsteps = self.curr_action_info[1]['round_meta']['nsteps'] \
                    if 'nsteps' in self.curr_action_info[1]['round_meta'] \
                    else 1 
    
    def tick(self):
        if self.clk_gated:
            return

        if self.all_reset_phead == True:
#            print(self.class_name, 'all reset_phead head done')
            return
        
        if self.addr_chn.vacancy():
           addr_info = {}
#           print(self.type, self.curr_action_name)
           addr_info['addr'] = self.curr_action(self.action_config)
           
               
               
           # set the initial prerequisite 
           #        only drain ports should need to set the prereq, other ports should have default prereqs
           #        this allows other ports to have changing prereq types (unlikely)
           if 'prereq' in self.round_meta:
               addr_info['prereq'] = self.round_meta['prereq']

           if self.curr_step == self.nsteps - 1:
                if self.round_meta is not None and\
                  'ndrop' in self.round_meta and\
                   self.round_meta['ndrop'] != 0:
                   addr_info['shrink'] = self.round_meta['ndrop']
                if self.round_meta is not None and \
                   'reset_phy_head' in self.round_meta  and \
                   self.round_meta['reset_phy_head'] is not None:
                       addr_info['reset_phy_head'] = self.round_meta['reset_phy_head'] 

           self.addr_chn.push(addr_info)
#           if 'PE' in self.debug:
#           print(self.debug, addr_info)
##           
           self.curr_step += 1
           self.next_action()
#        else:
#            if self.class_name == 'weights_sp_addr_generator':
        
        
        
        
        
        
        
        
        