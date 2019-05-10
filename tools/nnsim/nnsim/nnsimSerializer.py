
from nnsim.module import Module
import numpy as np

INT_32_MAX = 2147483647
class nnsimSerializer(Module):
    
    def instantiate(self, setup):
        self.in_chn      = setup['in_chn']
        self.out_chn     = setup['out_chn'] 
        self.ratio       = setup['ratio']  # how many segments are the incmong data segmented to 
        self.debug       = setup['debug'] if 'debug' in setup else None
        self.predefined_class = True
        
        
        self.class_name            = 'nnsimSerializer'
        
        self.action                = {'serialize': None, 'idle': None}
        self.attrs                 = {'serialization_ratio': self.ratio}
        self.access_stats          = {'serialize': {'count':0}, 'idle':{'count': 0}}
        self.component_with_action = True
    
    def configure(self, config = {'active_in_chn':0, 'active_out_chn':0}):
        self.busy           = False
        self.data           = [] 
        self.segment_length = None
        self.idx            = 0
        
        self.active_in_chn_idx  = config['active_in_chn']
        self.active_out_chn_idx = config['active_out_chn']   
        
        # determine whether we are dealing with channel list or individual channels 
        self.active_in_chn = self.in_chn if issubclass(type(self.in_chn), Module) \
                                    else self.in_chn[self.active_in_chn_idx]
                                    
        self.active_out_chn = self.out_chn if issubclass(type(self.out_chn), Module) \
                                      else self.out_chn[self.active_out_chn_idx]
    
    def tick(self):
        
        if self.active_in_chn.valid() and not self.busy:
            self.data  = self.active_in_chn.pop()
            self.segment_length = len(self.data) // self.ratio
            self.busy  = True
            self.access_stats['serialize']['count'] += 1
            
        elif self.active_out_chn.vacancy() and self.busy:
            out_data = self.data[self.idx * self.segment_length: (self.idx+1) * self.segment_length]
            self.active_out_chn.push(out_data)
#            print('************', self.debug, 'pushing out ', out_data)
            self.idx += 1
            
            self.access_stats['serialize']['count']  += 1
            if self.idx == self.ratio or self.data[self.idx * self.segment_length] == INT_32_MAX:
#            if self.idx == self.ratio: 
                self.idx  = 0
                self.busy = False
                self.data = []
        else:
            self.access_stats['idle']['count']  += 1
#        if self.active_out_chn.vacancy() is False:
#            if 'PsumSerializer' in self.debug:
#                print('channel full')
#        if self.active_in_chn.valid() is False:
#            if 'PsumSerializer' in self.debug:
#                print('no in data')

