# -*- coding: utf-8 -*-

from nnsim.module import Module, ModuleList
from nnsim.nnsimChannel import NoLatencyChannel
import numpy as np
# ================================================================================
#                        nnsimNoC
#    provides a paramterizable framework for network construction
#              
#          setup:
#              set of read channels
#              set of write channels  
#   compatible with any dimension of read channels and write channels   
# ================================================================================

class nnsimNoC(Module):
    
    def instantiate(self, setup):
        
        self.class_name = 'nnsimNoC'
        
        self.debug      = None if 'debug' not in setup \
                               else setup['debug']
        
        self.rd_chns    = setup['rd_chns']
        self.wr_chns    = setup['wr_chns']
        self.dest_chns  = setup['dest_chns']
        self.component_with_action = True
        self.customized_access = True

        # ----------------------------------------------------
        # Interpret dimension of channels
        # ----------------------------------------------------
        self.raw_rd_chn_size = self.rd_chns.getsize()
        self.raw_wr_chn_size = self.wr_chns.getsize()
        
        if len(self.raw_rd_chn_size) == 1:
            col = self.raw_rd_chn_size[0]
            self.rd_chn_size = (1,col)
        else:
            self.rd_chn_size = self.raw_rd_chn_size
        if len(self.raw_wr_chn_size) == 1:
            col = self.raw_wr_chn_size[0]
            self.wr_chn_size = (1, col)
        else:
            self.wr_chn_size = self.raw_wr_chn_size
        
        self.raw_dest_chn_size = self.raw_wr_chn_size 

        # --------------------------------------------
        # Access counts related setup
        # --------------------------------------------
        self.setup_access_info()
        self.curr_data = None
        self.curr_dests = None      
        self.last_data = None
        self.last_dests = None      
        
    def configure(self):
        # make sure there is no double push for the same read channels
        #     possible when two data needs to be written to the same read channel        
        self.vacancy_record = np.ones(self.rd_chn_size, dtype = np.int8)  
    
    def identify_chn(self, chns, r, c, size):
        
        if len(size) == 1:
            if issubclass(type(chns), Module):
                chn = chns
            else:
                chn = chns[c]
        else:
            chn = chns[r][c]
        return chn

    def setup_access_info(self):
        self.access_stats =   {'idle': {'count': 0},\
                               'transfer': {}, \
                               'repeated_transfer': {}, \
                               'blocked_transfer':{'count': 0}}
        self.raw_access_stats = {'idle': {'count': 0},\
                                'transfer': {}, \
                                'repeated_transfer': {}, \
                                'blocked_transfer':{'count': 0}}          
    def tick(self):
        if self.clk_gated:
            return          
        # detect the channel vacancy state, 
        # you don't know when the other of the channel will pull data out
        self.vacancy_record = np.ones(self.rd_chn_size)
        for r in range(self.rd_chn_size[0]):
            for c in range(self.rd_chn_size[1]):
                chn = self.identify_chn(self.rd_chns, r, c, self.raw_rd_chn_size)
                
                if not chn.vacancy():
                    self.vacancy_record[r][c] = 0

        # data is from write chns 
        # data is sent to read chns  
        for rw in range(self.wr_chn_size[0]):
            for cw in range(self.wr_chn_size[1]):
                wchn = self.identify_chn(self.wr_chns, rw, cw, self.raw_wr_chn_size)
                dchn = self.identify_chn(self.dest_chns, rw, cw, self.raw_dest_chn_size)
                if wchn.valid() and dchn.valid():
                    dests = [dest for dest in dchn.peek()]
                    vacancy = True
                    for dest in dests:
                            
                        if len(dest) == 1:
                            rd_chn = self.identify_chn(self.rd_chns, 0, dest[0], self.rd_chn_size)
                            vacancy = vacancy and rd_chn.vacancy()\
                              and self.vacancy_record[(0,dest)]
                        else:
                            vacancy = vacancy and self.rd_chns[dest[0]][dest[1]].vacancy()\
                              and self.vacancy_record[dest[0]][dest[1]]
                              
                    if vacancy:
                        data = wchn.pop()
                        dests = dchn.pop() 
                        for dest in dests:  
                            if len(dest) == 1:
                                rd_chn = self.identify_chn(self.rd_chns, 0, dest[0], self.rd_chn_size)
                                rd_chn.push(data)
                                self.vacancy_record[(0,dest)] = 0
                            else:
                                self.rd_chns[dest[0]][dest[1]].push(data)
                                self.vacancy_record[dest[0]][dest[1]] = 0 
                        
                        # save info to record repeated transfer
                        self.curr_dests = [d for d in dests]
                        self.curr_data  = data
                        
                        # argument is the number of destinations
                        arguments = (len(dests),)
                        if self.last_data is not None and self.last_dests is not None and \
                           self.curr_dests == self.last_dests and self.curr_data == self.last_data:
                           # repeated transfer
                            if arguments in self.raw_access_stats['repeated_transfer']:
                                self.raw_access_stats['repeated_transfer'][arguments]['count'] += 1
                            else:
                                self.raw_access_stats['repeated_transfer'][arguments] = {'count': 1}
                        else:
                            # normal transfer
                            if arguments in self.raw_access_stats['transfer']:
                                self.raw_access_stats['transfer'][arguments]['count'] += 1
                            else:
                                self.raw_access_stats['transfer'][arguments] = {'count': 1}
                    else:
                        # blocked transfer
                        self.raw_access_stats['blocked_transfer']['count'] += 1
                else:
                    self.raw_access_stats['idle']['count'] += 1
                    
    def summerize_access_stats(self):
        for access_name, access_dict in self.raw_access_stats.items():
            if access_name == 'idle':
                self.access_stats['idle'] = access_dict
            elif access_name == 'blocked_transfer':
                self.access_stats['blocked_transfer'] = access_dict
            else:
                if self.raw_access_stats[access_name]:
                    self.access_stats[access_name] = []
                    for arg_tuple, access_info in access_dict.items():
                        self.access_stats[access_name].append({'arguments': arg_tuple[0], 'count': access_info['count']})

#                       
                                           
    def __ntick__(self):
        Module.__ntick__(self)
        self.last_data = self.curr_data
        self.last_dests = self.curr_dests
        
        self.curr_data = None
        self.curr_dests = None              