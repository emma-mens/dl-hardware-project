# -*- coding: utf-8 -*-

from nnsim.module import Module
import numpy as np

class mac_sparse(Module):
    
    # --------------------------------------------------------------------
    # Instantiate the module 
    # --------------------------------------------------------------------  
    def instantiate(self, setup):
        
        # -----------------------------------------------------------------
        # Stats Related (DO NOT CHANGE)
        # ----------------------------------------------------------------
        self.class_name            = 'MAC'
        self.predefined_class      = True
        self.debug                 = setup['debug']
        
        self.access_stats          = {'mac_normal': {'count': 0}, \
                                      'mac_gated':  {'count': 0}, \
                                      'idle':       {'count':0},\
                                      'mac_reuse':  {'count':0}}
        self.component_with_action = True
        self.curr_cycle            = 0
        
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data 
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  
        self.component_class_as_topclass           = 'show'  
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
        
        # --------------------------------------------------------------
        # Hardware Setup
        # --------------------------------------------------------------
        self.latency               = setup['latency']
        self.data_width            = setup['data_width'] if 'data_width' in setup else 8
        self.attrs                 = {'pipeline_stage': 1,\
                                      'data_width': 8}
        self.final_result_chn      = setup['result_chn']
        self.opa_chn               = setup['opa_chn']  # ifmap
        self.opb_chn               = setup['opb_chn']  # weights 
        self.opc_chn               = setup['opc_chn']  # the psum
        

        
    def configure(self, config ):
        self.clk_gated  = config['clk_gated']
        self.op1 = np.nan
        self.op2 = np.nan
        self.computation_in_progress = False
        
        # for recording access stats
        self.old_op1 = np.nan
        self.old_op2 = np.nan
    
    # what does the component do during every clock tick    
    def tick(self):
        if self.clk_gated:
            return
        if self.curr_cycle == 0:
            if self.opa_chn.valid() and self.opb_chn.valid() and self.opc_chn.valid():
                self.op1   = int (self.opa_chn.pop()[0])  # ifmap
                self.op2   = int (self.opb_chn.pop()[0])  # weight
                self.op3   = int (self.opc_chn.pop()[0])  # psum
                self.curr_cycle += 1
                self.computation_in_progress = True
                
                if self.op1 == 0 or self.op2 == 0: # emazuh
                    self.computation_in_progress = False # emazuh
                    self.final_result_chn.push([self.op3]) # emazuh
                    self.curr_cycle = 0
            else:
                # waiting for operands to arrive
                self.access_stats['idle']['count'] += 1
                
        # if the computation has been going on for correct number of cycles           
        if self.curr_cycle == self.latency:
            if self.final_result_chn.vacancy():
                if self.op1 == 0 or self.op2 == 0:
                    self.access_stats['mac_gated']['count']+= 1
                elif self.old_op1 == self.op1 or self.old_op2 == self.op2:
                    self.access_stats['mac_reuse']['count']+= 1
                else:
                    self.access_stats['mac_normal']['count']+= 1
                        
                # keep track of the reuse pattern
                self.old_op1  = self.op1
                self.old_op2  = self.op2
                
                if self.op1 == 0 or self.op2 == 0:
                    mac_result = self.op3
                else:
                    mult_result = np.int32(self.op1 * self.op2)  
                    mac_result =  mult_result + self.op3
                self.final_result_chn.push([mac_result])
                
                # a multi-cycle mac is performed, start the next one in next cycle
                self.curr_cycle = 0
                self.computation_in_progress = False
            else:
                # mac stays idle and waits for the output channel to be cleared up
                self.access_stats['idle']['count'] += 1
        else:
            if self.computation_in_progress:
                # still in the process of processing a multi-cycle mac
                self.curr_cycle += 1
            else:
                # nothing is going on, ilde mac
                self.access_stats['idle']['count'] += 1
        
        

