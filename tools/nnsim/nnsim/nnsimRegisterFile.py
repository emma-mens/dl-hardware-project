# -*- coding: utf-8 -*-
from nnsim.module import Module, HWError
import numpy as np
class RFError(HWError):
    pass
            
class nnsimRF(Module):
    def instantiate(self, setup):
        self.class_name                              = 'RF'
        self.predefined_class                        = True

        self.width                                   = setup['width']
        self.port_used                               = [None] * setup['nports']
        self.nports                                  = setup['nports']
#        self.wr_port_used                            = [None] * setup['nw_ports']
        
        self.data                                    = np.zeros((setup['depth'], setup['width']))
        self.next_data                               = np.zeros((setup['depth'], setup['width']))
        
        self.depth                                   = setup['depth']
        self.width                                   = setup['width']
        
        self.debug                                   = setup['debug']
        
        self.params                                  = {'depth' :     'depth',\
                                                        'width':      'width',\
                                                        'data_width': 'data_width',\
                                                        'nports':     'nports'}
        # -------------------------------------------------------------------
        # Various Access Types for a Memory Component
        # -------------------------------------------------------------------
        #   -read_only
        #   -write_only
        #   -read and write ports active at the same time
        #       - decribes how many of each is active
        
        self.cycle_access_stats = {'read': 0, 'write': 0}
        self.access_stats   = {'idle': 0,\
                               'read_only': 0, \
                               'write_only': 0,\
                               'read_write': {}}
        
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_specification_stats   = 'show'
        self.top_level_class_stats                 = 'hide'
        self.access_counts_stats                   = 'hide'
        self.component_specification_stats         = 'hide'
        self.record_traces                         = False
        self.customized_access                     = False        
        
        self.last_read_addr = None
        self.last_read_data = None
        self.reg_insert_opt = setup['reg_insert_opt']
        
        self.reset()
    # ----------------------------------------------------------------------
    # No Latency Read
    # ----------------------------------------------------------------------
    def rd(self, address, pid):
        
        if self.port_used[pid] is not None:
            raise RFError('2 reads on a RAM with 1 read port')
        
        if not self.reg_insert_opt:
            self.cycle_access_stats['read'] += 1
        else:
            # optimal reg insertion
            if self.last_read_addr is not None:
                if not (self.last_read_addr == address and \
                        self.last_read_data == self.data[address, :]):
                    self.cycle_access_stats['read'] += 1  
            else:
                self.cycle_access_stats['read'] += 1
        
        self.port_used[pid] = address
        self.last_read_addr = address
        self.last_read_data = self.data[address, :]
        
        if self.width == 1:
            return self.data[address]
        else:
            return self.data[address]
    # ----------------------------------------------------------------------
    # One Cycle Latency Write
    # ----------------------------------------------------------------------        
    def wr(self, address, data, pid):
        if self.port_used[pid] is not None:
            raise RFError('2 writes on a RAM with 1 write port')
        else:
            if self.width == 1:
                self.next_data[address,0]            = data[0]
                self.cycle_access_stats['write'] += 1
            else:
                if self.next_data is None:
                    self.next_data[address]          = data
                    self.cycle_access_stats['write'] += 1
                else:
                    raise RFError('write conflict: on the same address')
        
    # ------------------------------------------------------------------------
    # Reset All data Values
    # ------------------------------------------------------------------------
    def reset(self):
        for d in range(self.depth):
            for w in range(self.width):
                self.data[d,w]                       = None
                self.next_data[d,w]                  = None 
        self.port_used                               = [None] * self.nports
    # -----------------------------------------------------------------------
    # Write Data in Low Clock Stage
    # -----------------------------------------------------------------------
    def __ntick__(self):
        self.port_used                               = [None] * self.nports
        for d in range(self.depth):
            for w in range(self.width):
                self.data[d,w]                       = self.next_data[d,w]
        
        # --------------------------------------------------------------------
        # Parse the Stats Information for last high cycle
        # --------------------------------------------------------------------
        if self.cycle_access_stats['read'] != 0 and self.cycle_access_stats['write'] != 0:
            
            # entry name format #read_#write
            entry_name = str(self.cycle_access_stats['read']) + '_' + str(self.cycle_access_stats['write'])
            # create an entry for the type of accesses (if not exist)
            if not entry_name in self.access_stats['read_write'].keys():
                self.access_stats['read_write'][entry_name] = 0
            # record the access type in last cycle
            self.access_stats['read_write'][entry_name] += 1
        
        elif self.cycle_access_stats['read'] != 0:
            self.access_stats['read_only'] += 1
        
        elif self.cycle_access_stats['write'] != 0:
            self.access_stats['write_only'] += 1
            
        elif self.cycle_access_stats['read'] == 0 and self.cycle_access_stats['write'] == 0:
            self.access_stats['idle']  += 1
        
        # clear the read and write stats from last cycle
        self.cycle_access_stats['read'] = 0
        self.cycle_access_stats['write'] = 0       
        
