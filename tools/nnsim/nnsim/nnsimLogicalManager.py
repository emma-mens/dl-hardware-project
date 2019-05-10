from nnsim.module  import Module
from nnsim.nnsimChannel import NoLatencyChannel as NLCh
from nnsim.nnsimChannel import Channel as Ch
from nnsim.nnsimReg     import Reg
import sys

class nnsimLogicalManager(Module):
    def instantiate(self, setup):
        
        self.class_name     = 'nnsimLogicalManager'
        # ---------------------------------------------------------------
        # debug 
        # ---------------------------------------------------------------                                    
        self.debug          = setup['debug'] + '_logical_manager'        
        # ---------------------------------------------------------------
        # input channels & hardware info
        # ---------------------------------------------------------------
        self.fill_addr_ichn    = setup['fill_addr_ochn']
        self.drain_addr_ichn   = setup['drain_addr_ochn']
        self.update_addr_ichn  = setup['update_addr_ochn']\
                                 if 'update' in setup['AGs'] else None
        self.memory_width      = setup['memory_width']
        # ---------------------------------------------------------------
        # address generators
        # ---------------------------------------------------------------          
        self.fill_AG        = setup['AGs']['fill']({'type': 'fill',\
                                                    'addr_chn': self.fill_addr_ichn,\
                                                    'width': self.memory_width,\
                                                    'debug': self.debug + '_fill'})
        
        self.drain_AG       = setup['AGs']['drain']({'type': 'drain',\
                                                     'addr_chn': self.drain_addr_ichn,\
                                                     'width': self.memory_width,\
                                                     'debug': self.debug + '_drain'})
        
        self.update_AG      = setup['AGs']['update']({'type': 'update',\
                                                      'addr_chn': self.update_addr_ichn,\
                                                      'width': self.memory_width,\
                                                      'debug': self.debug + '_update'})\
                              if 'update' in setup['AGs'] else None
                                  
        # ---------------------------------------------------------------
        # head and tail pointers for record keeping
        # --------------------------------------------------------------- 
                                  
        self.filled_head       = Reg(0)  
        self.filled_tail       = Reg(0)
        self.updated_head      = Reg(0)
        self.updated_tail      = Reg(0) 
        self.filled_all_valid  = Reg(False)
        self.updated_all_valid = Reg(False) 
        self.fill_round_done   = Reg(False)
        self.drain_round_done  = Reg(False)
        self.book_keeping      = {'fill_region':    {'head': self.filled_head, \
                                                     'tail': self.filled_tail, \
                                                     'all_valid': self.filled_all_valid},\
    
                                 'update_region':   {'head': self.updated_head,\
                                                     'tail': self.updated_tail,\
                                                     'all_valid': self.updated_all_valid}}    
        self.approved_write_addr_in_cycle = {'fill': None, 'update': None}
        # -----------------------------------------------------------------
        # Static and Runtime information
        # -----------------------------------------------------------------
        self.component_class_as_subclass = 'show'
        self.base_class_name             = 'counter'
        self.attrs                       = {'count_max': 'depth'}                      

        
    def configure(self, config):
        # ---------------------------------------------------------------
        # allocated amount of underlying physical memory
        # ---------------------------------------------------------------
        self.base                   = config['base'] 
        self.bound                  = config['bound']
        self.allocated_depth        = self.bound - self.base + 1
        
        # ---------------------------------------------------------------
        # reference pointers
        # ---------------------------------------------------------------
        self.fill_phead             = self.base
        self.update_phead           = self.base
        self.drain_phead            = self.base
        
        # ---------------------------------------------------------------
        # bookkeeping dictionary for gating check
        # ---------------------------------------------------------------

        self.reset_book_keeping_pointers()
                
        # ---------------------------------------------------------------
        # address generators
        # ---------------------------------------------------------------
        self.fill_AG.configure(config['AGs'])
        self.drain_AG.configure(config['AGs'])
        if self.update_AG is not None:
            self.update_AG.configure(config['AGs'])

    def reset_book_keeping_pointers(self):
        
        self.fill_round_done.wr(False)
        self.drain_round_done.wr(False)
        self.filled_all_valid.wr(False)  
        self.updated_all_valid.wr(False)
        
        self.filled_head.wr(self.base)
        self.updated_head.wr(self.base)
        self.filled_tail.wr(self.base)
        self.updated_tail.wr(self.base) 
        
    def check_request(self, request_type):
        
        if request_type == 'fill' :
            if not self.fill_round_done.rd():
                addr_info = self.check_fill_request()
                if addr_info['addr'] is not None:
                    self.approved_write_addr_in_cycle['fill'] = addr_info['addr']
                return addr_info
            else:
#                if 'psum' in self.debug:
#                    print('last round is not done')
                return {'addr': None}
        elif request_type == 'update':
            addr_info = self.check_update_request()
            if addr_info['addr'] is not None:
                self.approved_write_addr_in_cycle['update'] = addr_info['addr']
            return addr_info
#            else:
#                return {'addr': None}
        else:
            if not self.drain_round_done.rd():
                addr_info = self.check_drain_request()
                return addr_info
            else:
#                print('drain:', self.drain_round_done.rd(), 'fill:', self.fill_round_done.rd())
                return {'addr': None, 'forwarded': False}
                
        
        
    def update_book_keeping(self, ack_packet):
#        if 'IFmapPsumGLB' in self.debug:
#            print(self.debug, 'ack: ', ack_packet)        
        ack_type = ack_packet['type']
#        if 'ifmap' in self.debug and ack_type == 'fill':
#            print(self.debug, ack_packet)
        
        if ack_type == 'fill':
            self.process_fill_ack(ack_packet)
        elif ack_type == 'update':
            self.process_update_ack(ack_packet)
        else:
            self.process_drain_ack(ack_packet)
            
#        if 'ifmap' in self.debug:
#            print(self.debug, ack_packet)
        

    def process_fill_ack(self, ack_packet):
        ignore_other_update = False
        if 'reset_phy_head' in ack_packet and ack_packet['reset_phy_head']:
            self.fill_phead = self.base
            if self.drain_round_done.rd():
                self.reset_book_keeping_pointers()
                ignore_other_update = True
            else:
                self.fill_round_done.wr(True)    
        if not ignore_other_update:
            new_tail = (ack_packet['addr'] + 1 - self.base) % self.allocated_depth + self.base 
    #        if 'WeightsGLB' in self.debug:
    #        print('### ',self.debug, ack_packet, 'new tail:', new_tail, 'old_tail:', self.filled_tail.rd())
            self.filled_tail.wr(new_tail)
            if new_tail == self.filled_head.rd():
                self.filled_all_valid.wr(True)
            
         
 

    def process_update_ack(self, ack_packet):
        
        new_tail = (ack_packet['addr'] + 1 - self.base) % self.allocated_depth + self.base 
        self.updated_tail.wr(new_tail)
#        print('%% update ack', self.debug, ack_packet)
        if new_tail == self.updated_head.rd():
            self.updated_all_valid.wr(True)
        
        if 'reset_phy_head' in ack_packet and ack_packet['reset_phy_head']:
            self.update_phead = self.base
#        print('filled_head:', self.filled_head.rd(),\
#              'filled_tail:', self.filled_tail.rd(),\
#              'updated_head:', self.updated_head.rd(),\
#              'updated_tail:', self.updated_tail.rd(),\
#              'new_tail:', new_tail)
            
    def process_drain_ack(self, ack_packet):
        
        ignore_other_update = False
        if 'reset_phy_head' in ack_packet and ack_packet['reset_phy_head']:
            self.drain_phead = self.base
            if self.fill_round_done.rd():
                self.reset_book_keeping_pointers()
                ignore_other_update = True
            else:
                self.drain_round_done.wr(True)        

        if 'shrink' in ack_packet and ack_packet['shrink'] is not None and not ignore_other_update:
            
#            if not 'PE' in self.debug:
#                print('!!!!', self.debug, 'Shrink Operation on State:\n',\
#                                          'filled_head:', self.filled_head.rd(), \
#                                          'filled_tail:', self.filled_tail.rd(),\
#                                          'filled_all_valid:', self.filled_all_valid.rd(),\
#                                          'updated_head:', self.updated_head.rd(),\
#                                          'updated_tail:', self.updated_tail.rd(),\
#                                          'updated_all_valid:', self.updated_all_valid.rd(),\
#                                          'drain_pointer:', self.drain_phead,\
#                                          'shrinked_depth:',ack_packet['shrink'])
            
            shrink_depth = ack_packet['shrink']
            
            # ----------------------------------------------------------------
            # update physcial head for drain port
            # ----------------------------------------------------------------
            self.drain_phead = (self.drain_phead + shrink_depth - self.base) % self.allocated_depth  + self.base 
           
            # ----------------------------------------------------------------
            # update bookkeeping for filled region
            # ----------------------------------------------------------------            
            new_filled_head = (self.filled_head.rd() + shrink_depth - self.base) % self.allocated_depth  + self.base  
            self.filled_head.wr(new_filled_head)
            if new_filled_head == self.filled_tail.rd():
                self.filled_all_valid.wr(False)            
            # ----------------------------------------------------------------
            # raise flags for illegal cases
            # ----------------------------------------------------------------
            if self.filled_head.rd() < self.filled_tail.rd():
                if new_filled_head > self.filled_tail.rd()\
                   and not self.filled_all_valid.rd() :
                    raise Exception(self.debug, 'Shrinked more than live region', \
                                                'new_filled_head:', new_filled_head,\
                                                'filled_head:', self.filled_head.rd(),\
                                                'filled_tail:', self.filled_tail.rd())
            
            else:
                if new_filled_head > self.filled_tail.rd()\
                   and new_filled_head < self.filled_head.rd()\
                   and not self.filled_all_valid.rd() :
                    raise Exception(self.debug, 'Shrinked more than live region',  \
                                                'new_filled_head:', new_filled_head,\
                                                'filled_head:', self.filled_head.rd(),\
                                                'filled_tail:', self.filled_tail.rd())        
        
        # ----------------------------------------------------------------
        # update bookkeeping for updated region
        # ----------------------------------------------------------------
        if 'prereq' in ack_packet and ack_packet['prereq'] == 'update' and not ignore_other_update:
            new_updated_head = (ack_packet['addr'] + 1 - self.base) % self.allocated_depth  + self.base
            self.updated_head.wr(new_updated_head) 
            if new_updated_head == self.updated_tail.rd():
                self.updated_all_valid.wr(False)
                

#            print('reset_phead detected!!', 'head:', self.drain_phead)
#            print('filled_head:', self.filled_head.rd(), \
#                  'filled_tail:', self.filled_tail.rd(),\
#                  'filled_all_valid:', self.filled_all_valid.rd(),\
#                  'updated_head:', self.updated_head.rd(),\
#                  'updated_tail:', self.updated_tail.rd(),\
#                  'drain_pointer::', self.drain_phead) 
        
    def check_fill_request(self):
        if self.fill_addr_ichn.valid():
            virtual_info       = self.fill_addr_ichn.peek()
            virtual_fill_addr  = virtual_info['addr']
                
    
            if virtual_fill_addr == 'reset_phead':
                self.fill_phead = self.base
                self.fill_addr_ichn.pop()
                self.fill_round_done.wr(True)
#                if 'PE' in self.debug:
#                    print('------:', self.debug, 'Reset Fill State')                 
            else:
                physical_fill_addr = (self.fill_phead - self.base + virtual_fill_addr) % self.allocated_depth + self.base
                gate_fill_request  = self.gate_request({'type':'fill', 'physical_addr': physical_fill_addr})
                if not gate_fill_request:
#                    if 'ifmap' in self.debug:
#                    print('-->>>', self.debug, '*** fill *** processed ---- ', physical_fill_addr)
#                    print('filled_head:', self.filled_head.rd(), \
#                          'filled_tail:', self.filled_tail.rd(),\
#                          'filled_all_valid:', self.filled_all_valid.rd(),\
#                          'updated_head:', self.updated_head.rd(),\
#                          'updated_tail:', self.updated_tail.rd(),\
#                          'drain_pointer::', self.drain_phead) 
                    
                    request_info = {'addr': physical_fill_addr}
                    request_info['reset_phy_head'] = False if 'reset_phy_head' not in virtual_info else virtual_info['reset_phy_head']
                    return request_info
                    
#                if 'Psum' in self.debug:
#                print('-->>>', self.debug, '*** fill *** gated ---- ', physical_fill_addr)
#                print('filled_head:', self.filled_head.rd(), \
#                      'filled_tail:', self.filled_tail.rd(),\
#                      'filled_all_valid:', self.filled_all_valid.rd(),\
#                      'updated_head:', self.updated_head.rd(),\
#                      'updated_tail:', self.updated_tail.rd(),\
#                      'updated_all_valid:', self.updated_all_valid.rd(),\
#                      'drain_pointer::', self.drain_phead)        
        return {'addr': None}
        
    
    def check_update_request(self):
        if self.update_AG is not None:
            if self.update_addr_ichn.valid():
                virtual_info         = self.update_addr_ichn.peek()
                virtual_update_addr  = virtual_info['addr']
                if virtual_update_addr == 'reset_phead':
                    self.update_phead = self.base
                    self.update_addr_ichn.pop()
#                    if 'PE' in self.debug:
#                        print('------:', self.debug, 'Reset Update State') 
                else:
                    physical_update_addr = (self.update_phead - self.base + virtual_update_addr) % self.allocated_depth + self.base
                    gate_update_request  = self.gate_request({'type':'update', 'physical_addr': physical_update_addr})
                    if not gate_update_request:
                        request_info = {'addr': physical_update_addr}
                        request_info['reset_phy_head'] = False if 'reset_phy_head' not in virtual_info else virtual_info['reset_phy_head']
                        return request_info
#                    if 'PsumGLB' in self.debug:
#                        print('-->>>', self.debug, '*** update *** gated ---- ', physical_update_addr)
#                        print('filled_head:', self.filled_head.rd(), \
#                              'filled_tail:', self.filled_tail.rd(),\
#                              'filled_all_valid:', self.filled_all_valid.rd(),\
#                              'updated_head:', self.updated_head.rd(),\
#                              'updated_tail:', self.updated_tail.rd(),\
#                              'updated_all_valid:', self.updated_all_valid.rd(),\
#                              'drain_pointer::', self.drain_phead) 
        return {'addr': None}       
        
    
    def check_drain_request(self):     
        if self.drain_addr_ichn.valid():
            virtual_info        = self.drain_addr_ichn.peek()
            virtual_drain_addr  = virtual_info['addr']
            if virtual_drain_addr == 'reset_phead':
                self.drain_phead = self.base
                self.drain_addr_ichn.pop()
                self.drain_round_done.wr(True)
#                if 'PE' in self.debug:
#                    print('------:', self.debug, 'Reset Drain State')    
                                 
            else:
                physical_drain_addr = (self.drain_phead - self.base + virtual_drain_addr) % self.allocated_depth + self.base
                info = {'type':'drain',\
                         'physical_addr': physical_drain_addr,\
                         'prereq': virtual_info['prereq']}
                info['shrink'] = None if 'shrink' not in virtual_info else virtual_info['shrink']
                gate_drain_request  = self.gate_request(info)
#                if 'IFmapGLB' in self.debug:
#                    print(self.debug, info, 'gate:', gate_drain_request)
    
                if not gate_drain_request['gate']:
                    request_info = {'addr':  physical_drain_addr,\
                                    'prereq': virtual_info['prereq'],\
                                    'forwarded': gate_drain_request['forwarded']}
                    request_info['shrink'] = None if 'shrink' not in virtual_info else virtual_info['shrink']
                    request_info['reset_phy_head'] = False if 'reset_phy_head' not in virtual_info else virtual_info['reset_phy_head']
#                    if 'IFmapGLB' in self.debug:
#                    print('drain request: ', self.debug, info, 'gate_request:', gate_drain_request, 'request_info:', request_info)
                    return request_info
#                if 'IFmapGLB' in self.debug:
#                print('-->>>', self.debug, '*** drain *** gated ---- ', physical_drain_addr, virtual_info['prereq'])
#                print('filled_head:', self.filled_head.rd(), \
#                          'filled_tail:', self.filled_tail.rd(),\
#                          'filled_all_valid:', self.filled_all_valid.rd(),\
#                          'updated_head:', self.updated_head.rd(),\
#                          'updated_tail:', self.updated_tail.rd(),\
#                          'updated_all_valid:', self.updated_all_valid.rd(),\
#                          'drain_pointer::', self.drain_phead) 
            return {'addr': None }    
        
        
        
    def in_region(self, addr, region_type):
       
        region_name = region_type + '_region'
        head = self.book_keeping[region_name]['head'].rd()
        tail = self.book_keeping[region_name]['tail'].rd()
        
        if tail == head:
            if self.book_keeping[region_name]['all_valid'].rd():
                return True
            else:
                return False
        
        elif tail > head:
            if addr < tail and addr >= head:
                return True
            else:
                return False
        else:
            if addr >= tail and addr < head:
                return False
            else:
                return True              
                
    def gate_request(self, request_info):
        
        '''given the request type and physcial addr
           decides if the request needs to be gated accroding to the book keeping record'''
        
        request_type = request_info['type']
        request_addr = request_info['physical_addr']
    
        if request_type == 'fill' :
            if not self.in_region(request_addr, 'fill'):
                return False
            else:
                return True
            
        elif request_type == 'drain':
            prereq = request_info['prereq']
            
            if prereq == 'fill':
                if not self.in_region(request_addr, 'fill'):
                    if self.approved_write_addr_in_cycle['fill'] == request_addr\
                       and request_info['shrink'] is None:
                        return {'gate': False, 'forwarded': True}
                    return {'gate': True, 'forwarded': False}
                else:
                    return {'gate': False, 'forwarded': False}
            elif prereq == 'update':
                    if not self.in_region(request_addr, 'fill')\
                       or not self.in_region(request_addr, 'update'):
                           if self.approved_write_addr_in_cycle['update'] == request_addr \
                              and request_info['shrink'] is None:
                               return {'gate': False, 'forwarded': True}
                           return {'gate': True, 'forwarded': False}
                    else:
                       return {'gate': False, 'forwarded': False}
            else:
                print('drain prereq is not expected')
                sys.exit(0)
                        
        else:
            if not self.in_region(request_addr, 'fill'):
#                print('update addr:', request_addr, 'not in region',\
#                      'filled_head:', self.filled_head.rd(), \
#                      'filled_tail:', self.filled_tail.rd(),\
#                      'updated_head:', self.updated_head.rd(),\
#                      'updated_tail:', self.updated_tail.rd(),\
#                      'drain_pointer:', self.drain_phead)
                return True
            else:
                return False        
        
        
        
        
        
        
        
        
