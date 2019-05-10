# -*- coding: utf-8 -*-
from nnsim.module import Module, HWError
from nnsim.nnsimChannel import Channel, NoLatencyChannel
from nnsim.nnsimRecorder import nnsimRecorder
from nnsim.nnsimReg import Reg
import numpy as np

class nnsimMultiplier(Module):
    def instantiate(self, setup):
        self.class_name = 'Multiplier'
        self.predefined_class = True
        self.raw_access_stats = {'mul': 0}
        
        # default data width is a byte
        self.debug = setup['debug']
        self.data_width = setup['data_width'] 
        self.result_chn = setup['result_chn']
        self.opa_chn = setup['opa_chn']
        self.opb_chn = setup['opb_chn']
        # the truncation in eyeriss
        self.attrs = {'data_width' : self.data_width, 'out_data_width': int(self.data_width//2)}
       
        self.recorder = nnsimRecorder('test_vectors/mult/') 
    def configure(self, config):
        self.clk_gated = config['clk_gated']
      
    def mul(self):
        self.raw_access_stats['mul'] += 1
        opa = int (self.opa_chn.peek()[0])
        opb = int (self.opb_chn.peek()[0])
#        if 'PE[5][0]' in self.debug:
#        print('------- multing ', opa, ' ', opb)
        return  [opa * opb]
    
    def tick(self):
        if self.clk_gated:
            return        
        if self.opa_chn.valid() and self.opb_chn.valid():
            if self.result_chn.vacancy():
#                print('------- multing  ', self.opa_chn.peek(), ' ', self.opa_chn.peek()) 
                result = self.mul()
                self.result_chn.push(result)
                self.recorder.record('iacts.txt', int(self.opa_chn.pop()[0]))
                self.recorder.record('wegihts.txt',  int(self.opb_chn.pop()[0]))

class nnsimAdder(Module):
    def instantiate(self, setup):
        self.class_name = 'Adder'
        self.predefined_class = True
        self.raw_access_stats = {'add': 0}
        
        # default data width is a byte
        self.debug = setup['debug']
        self.data_width = setup['data_width'] 
        self.result_chn = setup['result_chn']
        
        self.opa_chn = setup['opa_chn']
        self.opb_chn = setup['opb_chn']
        self.params = {'data_width' : self.data_width}
        
#        self.record_test_vector = True
        self.recorder = nnsimRecorder('test_vectors/add/')
    
    def configure(self, config):
        self.clk_gated = config['clk_gated']
      
    def add(self):
        self.raw_access_stats['add'] += 1
        opa = int (self.opa_chn.peek()[0])
        opb = int (self.opb_chn.peek()[0])
#        if 'PE[5][0]' in self.debug:
#        print('------- adding  ', opa, ' ', opb)        
        return [opa + opb]
    
    def tick(self):
        if self.clk_gated:
            return        
        if self.opa_chn.valid() and self.opb_chn.valid(): 

            if self.result_chn.vacancy():
                result = self.add()
                self.result_chn.push(result)
                
                self.recorder.record('multprod.txt', int(self.opa_chn.peek()[0]))
                self.recorder.record('psum_in.txt',int( self.opb_chn.peek()[0]))
                
                self.opa_chn.pop()
                self.opb_chn.pop()
 
        
class nnsimMacTruncated(Module):
    
    ''' does not have the cycle accurate details related to the subcomponents '''
    
    def instantiate(self, setup):
        
        self.class_name          = 'MAC'
        self.predefined_class    = True
        
        self.access_stats = {'mac_normal': {'count': 0}, \
                             'mac_gated': {'count': 0}, \
                             'idle': {'count':0},\
                             'mac_reuse': {'count':0}}
        
        self.debug = setup['debug']
        
        self.data_width = setup['data_width'] if 'data_width' in setup \
                                              else 8
    
        self.attrs = {'data_width' : self.data_width, \
                      'mult_out_data_width': 8}

        self.final_result_chn = setup['result_chn']
        
        self.opa_chn = setup['opa_chn']  # ifmap
        self.opb_chn = setup['opb_chn']  # weights 
        self.opc_chn = setup['opc_chn']  # the psum
        
        if self.traces_stats == 'show':
            self.recorder = nnsimRecorder('test_vectors/mac/')
            self.record   = {}
        
        self.component_with_action = True
        
    def configure(self, config ):
        self.clk_gated  = config['clk_gated']
        
        # for recording access stats
        self.old_ifmap  = np.nan
        self.old_weight = np.nan
        
    def tick(self):
        if self.clk_gated:
            return

        if self.opa_chn.valid() and self.opb_chn.valid() and self.opc_chn.valid():
#            print('input operands valid')
            if self.final_result_chn.vacancy():
                ifmap   = int (self.opa_chn.pop()[0])
                weight  = int (self.opb_chn.pop()[0])
                psum    = int (self.opc_chn.pop()[0])
                
                if ifmap == 0:
                    self.access_stats['mac_gated']['count']  += 1
                elif self.old_ifmap == ifmap or self.old_weight == weight:
                    self.access_stats['mac_reuse']['count']  += 1
                else:
                    self.access_stats['mac_normal']['count']  += 1
                        
                # keep track of the reuse pattern
                self.old_ifmap  = ifmap
                self.old_weight = weight
                
                if self.traces_stats == 'show':
                    self.recorder.record('ifmap.txt', ifmap)
                    self.recorder.record('weights.txt',weight)
                    self.recorder.record('psum_in.txt',psum)
                
                mult_result = np.int32(ifmap * weight)                    
                # --------------------------------------------------------------------------
                #   Normal MAC
                # --------------------------------------------------------------------------                     
                mac_result = mult_result + psum
#                print(ifmap, 'x', weight, '+' , psum, '=', mac_result)
                # --------------------------------------------------------------------------
                #   Implementation of multiplier result truncation that happens in eyeriss
                # --------------------------------------------------------------------------                
                mult_truncated = np.int16(np.right_shift(mult_result, 16))
                mac_result = np.int16(mult_truncated + psum)
                
                self.final_result_chn.push([mac_result])
        else:
            self.access_stats['idle']['count'] +=1
#            print('ifmap:', self.opa_chn.valid(), 'weights:', self.opb_chn.valid(), 'psum:',self.opc_chn.valid())
  


class nnsimMac(Module):
    
    ''' does not have the cycle accurate details related to the subcomponents '''
    
    def instantiate(self, setup):
        
        self.class_name          = 'MAC'
        self.predefined_class    = True
        
        self.access_stats        = {'mac_normal': {'count': 0}, \
                                    'mac_gated': {'count': 0}, \
                                    'idle': {'count':0},\
                                    'mac_reuse': {'count':0}}
        self.latency             = setup['latency']
        self.debug               = setup['debug']
        
        self.data_width          = setup['data_width'] if 'data_width' in setup \
                                              else 8
    
        self.attrs               = {'data_width' : self.data_width,\
                                    'pipeline_stage': 1}

        self.final_result_chn = setup['result_chn']
        
        self.opa_chn = setup['opa_chn']  # ifmap
        self.opb_chn = setup['opb_chn']  # weights 
        self.opc_chn = setup['opc_chn']  # the psum
        
        if self.traces_stats == 'show':
            self.recorder = nnsimRecorder('test_vectors/mac/')
            self.record   = {}
        
        self.component_with_action = True
        self.curr_cycle = 0
#         print('hello darkness my old friend')
        
    def configure(self, config ):
        self.clk_gated  = config['clk_gated']
        self.op1 = np.nan
        self.op2 = np.nan
        self.computation_in_progress = False
        
        # for recording access stats
        self.old_op1 = np.nan
        self.old_op2 = np.nan
        self.mac_result = 0

#     def tick(self):
#             if self.clk_gated:
#                 return
#             if self.curr_cycle == 0:
#                 if self.opa_chn.valid() and self.opb_chn.valid() and self.opc_chn.valid():
#                     self.op1   = int (self.opa_chn.pop()[0])  # ifmap
#                     self.op2   = int (self.opb_chn.pop()[0])  # weight
#                     self.op3   = int (self.opc_chn.pop()[0])  # psum
#                     self.curr_cycle += 1
#                     self.computation_in_progress = True

#                     if self.op1 == 0 or self.op2 == 0: # emazuh
#                         if self.final_result_chn.vacancy():
#                             self.computation_in_progress = False # emazuh
#                             self.final_result_chn.push([self.op3]) # emazuh
#                             self.curr_cycle = 0
#                         else:
#                             self.access_stats['idle']['count'] += 1
#                 else:
#                     # waiting for operands to arrive
#                     self.access_stats['idle']['count'] += 1
# #             if self.curr_cycle == 0:
# #                 if self.opa_chn.valid() and self.opb_chn.valid() and self.opc_chn.valid():
# #                     self.op1   = int (self.opa_chn.pop()[0])  # ifmap
# #                     self.op2   = int (self.opb_chn.pop()[0])  # weight
# #                     self.op3   = int (self.opc_chn.pop()[0])  # psum
# #                     self.computation_in_progress = True  

# #                     if self.op1 == 0 or self.op2 == 0:
# #                         if self.final_result_chn.vacancy():
# #                             self.access_stats['mac_gated']['count']+= 1
# #                             self.final_result_chn.push([self.op3])
# #                             self.computation_in_progress = False  
# #                         else:
# #                             self.curr_cycle += 1
# #         #                 else:
# #                             # mac stays idle and waits for the output channel to be cleared up
# #                             self.access_stats['idle']['count'] += 1                        
# #                 else:
# #                     # waiting for operands to arrive
# #                     self.access_stats['idle']['count'] += 1

#             # if the computation has been going on for correct number of cycles           
#             if self.curr_cycle == self.latency:
#                 if self.final_result_chn.vacancy():
#                     if self.op1 == 0 or self.op2 == 0:
#                         self.access_stats['mac_gated']['count']+= 1
#                     elif self.old_op1 == self.op1 or self.old_op2 == self.op2:
#                         self.access_stats['mac_reuse']['count']+= 1
#                     else:
#                         self.access_stats['mac_normal']['count']+= 1

#                     # keep track of the reuse pattern
#                     self.old_op1  = self.op1
#                     self.old_op2  = self.op2

#                     mult_result = np.int32(self.op1 * self.op2)  
#                     mac_result =  mult_result + self.op3
#                     self.final_result_chn.push([mac_result])

#                     # a multi-cycle mac is performed, start the next one in next cycle
#                     self.curr_cycle = 0
#                     self.computation_in_progress = False
#                 else:
#                     # mac stays idle and waits for the output channel to be cleared up
#                     self.access_stats['idle']['count'] += 1
#             else:
#                 if self.computation_in_progress:
#                     # still in the process of processing a multi-cycle mac
#                     self.curr_cycle += 1
#                 else:
#                     # nothing is going on, ilde mac
#                     self.access_stats['idle']['count'] += 1

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
                
            else:
                # waiting for operands to arrive
                self.access_stats['idle']['count'] += 1
#                print(self.debug, 'ifmap:', self.opa_chn.valid(), 'weights:', self.opb_chn.valid(), 'psum:',self.opc_chn.valid())
           
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

                
                    



class nnsimMacPerformance(Module):
    
    ''' does not have the cycle accurate details related to the subcomponents '''
    
    def instantiate(self, setup):
        
        self.class_name          = 'MAC'
        self.predefined_class    = True
        
        self.access_stats = {'mac_normal': {'count': 0}, \
                             'mac_gated': {'count': 0}, \
                             'idle': {'count':0},\
                             'mac_reuse': {'count':0}}
        
        self.debug = setup['debug']
        
        self.data_width = setup['data_width'] if 'data_width' in setup \
                                              else 8
    
        self.attrs = {'data_width' : self.data_width, \
                      'mult_out_data_width': 8,\
                      'pipeline_stage': 2}

        self.final_result_chn = setup['result_chn']
        
        self.opa_chn = setup['opa_chn']  # ifmap
        self.opb_chn = setup['opb_chn']  # weights 
        self.opc_chn = setup['opc_chn']  # the psum 
        self.component_with_action = True
        
    def configure(self, config ):
        self.clk_gated  = config['clk_gated']
        
        # for recording access stats
        self.old_ifmap  = np.nan
        self.old_weight = np.nan
        
    def tick(self):
        if self.clk_gated:
            return

        if self.opa_chn.valid() and self.opb_chn.valid() and self.opc_chn.valid():
            if self.final_result_chn.vacancy():
#                print(self.debug)
                ifmap   = int (self.opa_chn.pop()[0])
                weight  = int (self.opb_chn.pop()[0])
                psum    = int (self.opc_chn.pop()[0])
                
                if ifmap == 0:
                    self.access_stats['mac_gated']['count']  += 1
                elif self.old_ifmap == ifmap or self.old_weight == weight:
                    self.access_stats['mac_reuse']['count']  += 1
                else:
                    self.access_stats['mac_normal']['count']  += 1
                        
                # keep track of the reuse pattern
                self.old_ifmap  = ifmap
                self.old_weight = weight
                
                if self.traces_stats == 'show':
                    self.recorder.record('ifmap.txt', ifmap)
                    self.recorder.record('weights.txt',weight)
                    self.recorder.record('psum_in.txt',psum)
                if ifmap == 0:
                    mac_result = psum
                else:
                    mult_result = np.int32(ifmap * weight)  
                    mac_result =  mult_result + psum
  
                
                self.final_result_chn.push([mac_result])
#            else:
#                print(self.debug, 'final result chn is full')
        else:
            self.access_stats['idle']['count'] +=1
#            print(self.debug, 'ifmap:', self.opa_chn.valid(), 'weights:', self.opb_chn.valid(), 'psum:',self.opc_chn.valid())
            
    
class nnsimNZeroComp(Module):
    ''' comapres if data from input channel is nonzero '''
    
    def instantiate(self, setup):
        self.class_name       = 'NZComp'
        self.in_chn           = setup['in_chn']
        self.out_chn          = setup['out_chn']
        self.attrs           = {'data_width': 'data_width'}
        self.predefined_class = True
        self.base_class_name = 'comparator'
        
        # -------------------------------------------------------------------
        #  Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_with_action       = True
        self.access_stats                = {'compare': {'count': 0}, 'idle': {'count': 0}}

                        
    def tick(self):
        if self.in_chn.valid() and self.out_chn.vacancy():
            val = self.in_chn.pop()
#            print('zero sp')
            val_to_push = [1] if not val[0] == 0 else [0]
            self.out_chn.push(val_to_push)
            
            self.access_stats['compare']['count'] += 1
        else:
            self.access_stats['idle']['count'] += 1
            
        
        
        
        
        
        
        
