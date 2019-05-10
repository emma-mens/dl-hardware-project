from nnsim.module import Module
from nnsim.module import ModuleList as ModuleL
from nnsim.nnsimChannel import NoLatencyChannel as NLCh
from nnsim.nnsimChannel import Channel as Ch
from nnsim.nnsimLogicalManager import nnsimLogicalManager as LM
from nnsim.nnsimRAM import SRAM
import sys

RD = True
WR = False

class nnsimSmartBuffer(Module):
    def instantiate(self, setup):
        self.class_name         = 'nnsimSmartBuffer'
        self.debug              = setup['debug']
        # ----------------------------------------------------------------
        # input channels
        # ----------------------------------------------------------------
        self.fill_data_ichns    = setup['fill_data_ichns']
        self.update_data_ichns  = setup['update_data_ichns']\
                                    if 'update_data_ichns' in setup\
                                    else None
        self.drain_enable_ichns = setup['drain_enable_ichns']\
                                  if 'drain_enable_ichns' in setup\
                                  else None
        # ----------------------------------------------------------------
        # output channels
        # ----------------------------------------------------------------
        self.drain_data_ochns   = setup['drain_data_ochns']
        # ----------------------------------------------------------------
        # subcomponents
        # ---------------------------------------------------------------- 
        self.logical_managers   = ModuleL()
        self.memory             = SRAM(setup['SRAM'])
        self.memory_width       = setup['SRAM']['width']
        # ----------------------------------------------------------------
        # internal channels
        # ----------------------------------------------------------------
        self.ack_internal_chns             = ModuleL()
        self.lm_fill_addr_internal_chns    = ModuleL()
        self.lm_drain_addr_internal_chns   = ModuleL()
        self.lm_update_addr_internal_chns  = ModuleL()
        # ----------------------------------------------------------------
        # setup logical managers
        # ---------------------------------------------------------------- 
        self.num_logical_managers   = setup['num_logical_managers']
        for logical_unit_idx in range(self.num_logical_managers):
            lm_setup = {'debug': self.debug + ' (LM:'+ str(logical_unit_idx) + ')'}
            lm_setup['memory_width'] = self.memory_width
            lm_setup.update(setup['LMs'][logical_unit_idx].copy())
            # ------ >> ack channel
            self.ack_internal_chns.append(Ch())
            lm_setup['ack_ichn'] = self.ack_internal_chns[logical_unit_idx]
            # ------ >> fill address channel
            self.lm_fill_addr_internal_chns.append(Ch())
            lm_setup['fill_addr_ochn']   = self.lm_fill_addr_internal_chns[logical_unit_idx]
            # ------ >> drain address channel
            self.lm_drain_addr_internal_chns.append(Ch())
            lm_setup['drain_addr_ochn']   = self.lm_drain_addr_internal_chns[logical_unit_idx]
            # ------ >> update address channel
            if 'update' in setup['LMs'][logical_unit_idx]['AGs']:
                self.lm_update_addr_internal_chns.append(Ch())
                lm_setup['update_addr_ochn']   = self.lm_update_addr_internal_chns[logical_unit_idx]
            else:
                self.lm_update_addr_internal_chns.append(None)
            # ------ >> instantiate logical manager
            self.logical_managers.append(LM(lm_setup))
            # ------ >> assign unique class name for each logical manager
            self.logical_managers[logical_unit_idx].class_name = \
                  'LM'+ str(logical_unit_idx) + '_' + self.logical_managers[logical_unit_idx].class_name 
            
        # ----------------------------------------------------------------
        # internal records containers
        # ----------------------------------------------------------------
        # >> record for processed reads
        # used for retrieving read data information 
        self.last_read                = ModuleL() 
        for sram_port_idx in range(self.memory.nports):
            self.last_read.append(NLCh(depth = 1))
        
        # used for detecting drains that can be forwarded
        self.approved_write_data_in_cycle = []
        for lm_idx in range(self.num_logical_managers):
            self.approved_write_data_in_cycle.append({'fill': None, 'update': None})
            
        # -----------------------------------------------------------------
        # Static and Runtime information
        # -----------------------------------------------------------------
        # definitin of compound actions
        self.setup_access_info()
        
        attrs_dict = setup['SRAM'].copy()
        attrs_dict.pop('port_type')
        self.attrs.update(attrs_dict)
        
        self.component_with_action = True
        
    def configure(self, config):
        for logical_unit_idx in range(self.num_logical_managers):
            self.logical_managers[logical_unit_idx].configure(config['LM'][logical_unit_idx])
        # ----------------------------------------------------------------
        # internal records configuration
        # -------------- -------------------------------------------------- 
        # >> record for logical manager and sram ports correspondance
        self.lm_sram_map = config['lm_sram_map']
        
    def tick(self):
        self.ack_packet = []
        for i in range(self.num_logical_managers):
            self.ack_packet.append([])
        # ------------------------------------------------------------------
        # Check for unprocessed reads
        # ------------------------------------------------------------------
        for sram_port_idx in range(self.memory.nports):
            if self.last_read[sram_port_idx].valid():
                read_request_info = self.last_read[sram_port_idx].peek()
#                if 'IFmapGLB' in self.debug:
#                    print(self.debug, read_request_info, 'ochn vacancy:', self.drain_data_ochns[read_request_info['lm_idx']].vacancy())
                if self.drain_data_ochns[read_request_info['lm_idx']].vacancy():
                    if read_request_info['enabled']:
                        if not read_request_info['forwarded']:
                            read_data = [d for d in self.memory.response(port = sram_port_idx)] 
#                            if 'PsumGLB' in self.debug:
#                                print('DDDDD ' ,self.debug, 'read from memory:', read_data, 'from ', read_request_info['addr'])
                        else:
                            read_data = read_request_info['forwarded_data']
#                            if 'PsumGLB' in self.debug:
#                                print('DDDDD ' ,self.debug, 'forwared read:', read_data, 'from ', read_request_info['addr'])
                    else:
                        read_data = [0] * self.memory.width
#                        if 'PsumGLB' in self.debug:
#                                print('DDDDD ' ,self.debug, 'gated data:', read_data, 'from ', read_request_info['addr'])
                    self.last_read[sram_port_idx].pop()
#                    if 'PsumGLB' in self.debug:
#                        print(self.debug, 'port ', sram_port_idx, 'pop')
                    self.drain_data_ochns[read_request_info['lm_idx']].push(read_data)

        # ------------------------------------------------------------------
        # Check for ready requests 
        # ------------------------------------------------------------------ 
        for lm_idx in range(self.num_logical_managers):
            self.check_for_update_request(lm_idx)
            self.check_for_fill_request(lm_idx)
            self.check_for_drain_request(lm_idx)
            if self.logical_managers[lm_idx].fill_round_done.rd()\
               and self.logical_managers[lm_idx].drain_round_done.rd():
                   self.logical_managers[lm_idx].reset_book_keeping_pointers()
#                   print('round done')
            
    def check_for_drain_request(self, lm_idx):   
#        if not self.lm_drain_addr_internal_chns[lm_idx].valid():
#            if 'IFmapGLB' in self.debug:
#                print('!!!!!', self.debug,' no drain request')
#        else:
#            if 'IFmapGLB' in self.debug:
#                print('!!!!!', self.debug,'wait to process request',self.lm_drain_addr_internal_chns[lm_idx].peek() )
        if self.lm_drain_addr_internal_chns[lm_idx].valid():
            
            request_info = self.logical_managers[lm_idx].check_request('drain')
#            print(request_info)
#            if 'IFmapGLB' in self.debug:
#                print(self.debug, request_info)

            if request_info['addr'] is not None:
                enable_signal_ready = True
                enabled             = True
                enabled_buffer      = False
                if self.drain_enable_ichns is not None and \
                   self.drain_enable_ichns[lm_idx] is not None:
                    enable_signal_ready = self.drain_enable_ichns[lm_idx].valid()
                    enabled_buffer      = True
                    if enable_signal_ready:
                        enabled         = self.drain_enable_ichns[lm_idx].peek()[0]
#                if 'IFmapGLB' in self.debug:
#                    print(self.debug, request_info, 'enable signal:', enable_signal_ready)   
                if enable_signal_ready:
                    sram_rd_port = self.lm_sram_map[lm_idx]['drain']
                    if self.last_read[sram_rd_port].vacancy() and not self.memory.port_in_use(sram_rd_port):
#                        if 'PsumGLB' in self.debug:
#                            print(self.debug, 'there is space and available prot for issuing read request')
                        if enabled_buffer:
                            self.drain_enable_ichns[lm_idx].pop()
                            
                        address = request_info['addr']
                        self.lm_drain_addr_internal_chns[lm_idx].pop()
                       
                        if enabled and not request_info['forwarded']:
                            self.memory.request(RD, address, port = sram_rd_port)
                       
                        if enabled and request_info['forwarded']:
#                            print('forwarding data')
                            if request_info['prereq'] == 'fill':
                                forwarded_data = self.approved_write_data_in_cycle[lm_idx]['fill']
                                if forwarded_data is None:
                                    print(self.debug, 'there is no fill data available for forwarding')
                                    sys.exit(0)
                            elif request_info['prereq'] == 'update':
                                forwarded_data = self.approved_write_data_in_cycle[lm_idx]['update']
                                if forwarded_data is None:
                                    print(self.debug, 'there is no update data available for forwarding')
                                    sys.exit(0)
                            else:
                                print(self.debug, 'nowhere to find data being forwarded')
                                sys.exit(0)
                        else:
                            forwarded_data = None
                        
                        self.last_read[sram_rd_port].push({'lm_idx':    lm_idx,\
                                                           'enabled':   enabled,\
                                                           'addr':      address,\
                                                           'forwarded': request_info['forwarded'],\
                                                           'forwarded_data': forwarded_data})
                        
                        ack_packet = {'type': 'drain', 'addr': address, 'shrink': request_info['shrink'],\
                                      'prereq': request_info['prereq'],  'forwarded': request_info['forwarded'],\
                                      'reset_phy_head': request_info['reset_phy_head'] }
#                        if 'IFmapGLB' in self.debug:
#                            print('########## DRAIN #################', self.debug, request_info)
                        self.logical_managers[lm_idx].update_book_keeping(ack_packet)  

                        # -------------------------------------------------
                        # record access
                        # ------------------------------------------------- 
                        if enabled :                         
                            last_addr = self.last_read_addr[lm_idx]
                            if request_info['forwarded']:
                                arg_name = 'lm' + str(lm_idx) + '_nforwarded_drain'
                                self.cycle_access[arg_name] += 1
                            elif last_addr is not None and last_addr == address:
                                arg_name = 'lm' + str(lm_idx) + '_nrepeated_drain'
                                self.cycle_access[arg_name] +=1
                            else:
                                 arg_name = 'lm' + str(lm_idx) + '_ndrain'
                                 self.last_read_addr[lm_idx] = address
                                 self.cycle_access[arg_name] +=1
                        else:
                            arg_name = 'lm' + str(lm_idx) + '_ngated_drain'
                            self.cycle_access[arg_name] +=1
                            
#                    else:
#                        if 'PsumGLB' in self.debug:
#                            print(self.debug, 'rd_port:', sram_rd_port, 'last_read_vacant:', self.last_read[sram_rd_port].vacancy(), \
#                                              'port_in_use:', self.memory.port_in_use(sram_rd_port))
                            

    def check_for_update_request(self, lm_idx):
        if self.logical_managers[lm_idx].update_AG is None:
            return
#        if 'PsumGLB' in self.debug:
#            stop = 1
        if (self.update_data_ichns[lm_idx].valid() and self.lm_update_addr_internal_chns[lm_idx].valid()) or \
           (self.lm_update_addr_internal_chns[lm_idx].valid() and self.lm_update_addr_internal_chns[lm_idx].peek()['addr'] == 'reset_phead' ):
            request_info = self.logical_managers[lm_idx].check_request('update')
#            if 'PsumGLB' in self.debug:
#                print(self.debug, request_info)
            if request_info['addr'] is not None:
                sram_wr_port = self.lm_sram_map[lm_idx]['update']
                if not self.memory.port_in_use(sram_wr_port):
                    address = request_info['addr']
                    data    = self.update_data_ichns[lm_idx].pop()
#                    if 'PsumGLB' in self.debug:
#                        print(self.debug, request_info, 'data for update:', data)
                    self.approved_write_data_in_cycle[lm_idx]['update'] = data
                    self.lm_update_addr_internal_chns[lm_idx].pop()
                    self.memory.request(WR, address, data, port = sram_wr_port)
                    ack_packet = {'type': 'update', 'addr': address, 'reset_phy_head': request_info['reset_phy_head']}
                    self.logical_managers[lm_idx].update_book_keeping(ack_packet)   
                    # ---------------------------------------
                    # record access
                    # ---------------------------------------    
                    if not data == self.last_write_data[lm_idx]:
                        arg_name = 'lm' + str(lm_idx) + '_nupdate'
                    else:
                        arg_name = 'lm' + str(lm_idx) + '_nrepeated_data_update'
                        
                    self.cycle_access[arg_name] += 1 
#                    self.curr_write_addr[lm_idx] = address
                    self.last_write_data[lm_idx] = data
                    
                    if self.traces_stats == 'show':
                        self.recorder.record(self.debug + '_update.txt', data[0])
                else:
                    # if the write port is not avaiable, overwrite the logical manager's information
                   self.logical_managers[lm_idx].approved_write_addr_in_cycle['update'] = None
#        else:
#            if 'PsumGLB' in self.debug:
#                print('update_data:', self.update_data_ichns[lm_idx].valid())

             
    def check_for_fill_request(self, lm_idx):
        if (self.fill_data_ichns[lm_idx].valid() and self.lm_fill_addr_internal_chns[lm_idx].valid()) or \
           (self.lm_fill_addr_internal_chns[lm_idx].valid() and self.lm_fill_addr_internal_chns[lm_idx].peek()['addr'] == 'reset_phead' ):
            request_info = self.logical_managers[lm_idx].check_request('fill')
            if request_info['addr'] is not None:
                sram_wr_port = self.lm_sram_map[lm_idx]['fill']
                if not self.memory.port_in_use(sram_wr_port):
                    address = request_info['addr']
                    data    = self.fill_data_ichns[lm_idx].pop()
                    self.approved_write_data_in_cycle[lm_idx]['fill'] = data
                    self.lm_fill_addr_internal_chns[lm_idx].pop()
#                    print(self.debug, data)
                    self.memory.request(WR, address, data, port = sram_wr_port)
                    ack_packet = {'type': 'fill', 'addr': address, 'reset_phy_head':request_info['reset_phy_head']}
                    self.logical_managers[lm_idx].update_book_keeping(ack_packet)
#                    if 'IFmapGLB' in self.debug:
#                            print(self.debug, request_info)
                    
                    # ---------------------------------------
                    # record access
                    # --------------------------------------- 
                    if not data == self.last_write_data[lm_idx]:
                        arg_name = 'lm' + str(lm_idx) + '_nfill'
                    else:
                        arg_name = 'lm' + str(lm_idx) + '_nrepeated_data_fill'
                    self.cycle_access[arg_name] += 1
                    
#                    self.curr_write_addr[lm_idx] = address
                    self.last_write_data[lm_idx] = data
                    
                    # -------------------------------------------
                    # record filled data
                    # -------------------------------------------
                    if self.traces_stats == 'show':
                        self.recorder.record(self.debug + '_fill.txt', data[0])
                else:
                    # if the write port is not avaiable, overwrite the logical manager's information
                    self.logical_managers[lm_idx].approved_write_addr_in_cycle['fill'] = None
                    
    def setup_access_info(self):
        
            # =====================================================================
            # construct action description of the compound action: buffer access
            # ===================================================================== 
            self.customized_access      = True
            self.arg_lst                = []      # top level action attributes 
            total_nread                 = []      # all drain related counts: aggregated for memory
            total_nwrite                = []      # all fill related counts: aggregated for memory
            total_nrepeated_read        = []      # all repeated drain related counts: aggregated for memory
            total_nrepeated_data_write  = []      # all repeated data write counts
            subcomp_class_actions       = {}      # all related subcomponent class actions 
            
            # ---------------------------------------------------------------------
            # Collect related information from each logical manager
            # ---------------------------------------------------------------------       
            for lm_idx in range(self.num_logical_managers):
                
                lm_ndrain                = 'lm' + str(lm_idx) + '_ndrain'
                lm_nfill                 = 'lm' + str(lm_idx) + '_nfill'
                lm_nupdate               = 'lm' + str(lm_idx) + '_nupdate'
                lm_nrepeated_data_fill   = 'lm' + str(lm_idx) + '_nrepeated_data_fill'
                lm_nrepeated_data_update = 'lm' + str(lm_idx) + '_nrepeated_data_update'
                lm_nrepeated_drain       = 'lm' + str(lm_idx) + '_nrepeated_drain'
                lm_nforwarded_drain      = 'lm' + str(lm_idx) + '_nforwarded_drain'
                lm_ngated_drain          = 'lm' + str(lm_idx) + '_ngated_drain'
                
                self.arg_lst.append(lm_ndrain)
                self.arg_lst.append(lm_nfill)
                self.arg_lst.append(lm_nupdate)
                self.arg_lst.append(lm_nrepeated_data_fill)
                self.arg_lst.append(lm_nrepeated_data_update)
                self.arg_lst.append(lm_nrepeated_drain)
                self.arg_lst.append(lm_nforwarded_drain)
                self.arg_lst.append(lm_ngated_drain)
                
                # sum up the access that will point into RAM
                # gated and forwarded drain does not invovle actual RAM accesses
                total_nread.append(lm_ndrain)
                total_nwrite.append(lm_nfill)
                total_nwrite.append(lm_nupdate)
                total_nrepeated_read.append(lm_nrepeated_drain)
                total_nrepeated_data_write.append(lm_nrepeated_data_fill)
                total_nrepeated_data_write.append(lm_nrepeated_data_update)
               
                # ---------------------------------------------------------------------------
                # Collect related information for the address generators, embedded in LMs
                # ---------------------------------------------------------------------------                  
                subcomp_class_actions.update({self.logical_managers[lm_idx].class_name:\
                                               {'action_name': 'generate',\
                                                'arguments': [lm_ndrain, lm_ngated_drain, lm_nfill, lm_nupdate, lm_nrepeated_data_update, lm_nrepeated_data_fill ],\
                                                'repeat': {'sum':[lm_ndrain, lm_ngated_drain, lm_nfill, lm_nupdate, lm_nrepeated_data_update, lm_nrepeated_data_fill]}}\
                                              })
    
                # ---------------------------------------------------------------------
                # Collect related information for the channel subcomponent (move to top level/serializer/deserializer)
                # ---------------------------------------------------------------------   
                self.fill_data_ichns[lm_idx].base_class_name  = 'channel'
                self.fill_data_ichns[lm_idx].component_class_as_subclass = 'show'
                
                self.drain_data_ochns[lm_idx].base_class_name = 'channel'
                self.drain_data_ochns[lm_idx].component_class_as_subclass = 'show'
                
                self.fill_data_ichns[lm_idx].class_name  = 'lm_' + str(lm_idx) + '_fill_chn' 
                self.drain_data_ochns[lm_idx].class_name = 'lm_' + str(lm_idx) + '_drain_chn' 
                

                
                
                subcomp_class_actions.update({self.fill_data_ichns[lm_idx].class_name: {'action_name': 'access',\
                                                                                        'repeat': lm_nfill}})
                subcomp_class_actions.update({self.drain_data_ochns[lm_idx].class_name: {'action_name': 'access',\
                                                                                         'repeat': {'sum':[lm_ndrain, lm_nrepeated_drain]}}})   
                
                if self.update_data_ichns is not None and self.update_data_ichns[lm_idx] is not None:
                    
                    self.update_data_ichns[lm_idx].base_class_name = 'channel'
                    self.update_data_ichns[lm_idx].component_class_as_subclass = 'show'
                    
                    self.update_data_ichns[lm_idx].class_name = 'lm_' + str(lm_idx) + '_update_chn' 
                    
                    subcomp_class_actions.update({self.update_data_ichns[lm_idx].class_name: {'action_name': 'access',\
                                                                                              'repeat': lm_nupdate}})   
    
    
        
            # ---------------------------------------------------------------------
            # Collect related information for the memory subcomponent
            # ---------------------------------------------------------------------   
            subcomp_class_actions.update({self.memory.class_name: {'action_name': 'RAM_access',\
                                                                   'arguments':  [{'sum': total_nread}, \
                                                                                  {'sum': total_nwrite}, \
                                                                                  {'sum': total_nrepeated_read},\
                                                                                  {'sum': total_nrepeated_data_write}],\
                                                                   'repeat': 1}})
            # ---------------------------------------------------------------------
            # Define all of the actions using collected info
            # ---------------------------------------------------------------------
    
            smartbuffer_access_action_def = {'arguments': self.arg_lst,\
                                             'subcomponent_class_actions': subcomp_class_actions}
            
            idle_access_action_def        = {'subcomponent_class_actions': \
                                             {self.memory.class_name: {'action_name': 'idle','repeat': 1}}}    
    
            self.actions                  = {'idle': idle_access_action_def,\
                                             'buffer_access': smartbuffer_access_action_def}
                    
            # =====================================================================
            # construct containers for recording access counts
            # =====================================================================        
            self.last_read_addr   = [None] * self.num_logical_managers
            self.last_write_addr  = [None] * self.num_logical_managers
            self.last_write_data  = [None] * self.num_logical_managers
            self.curr_write_addr  = [None] * self.num_logical_managers
            self.access_stats     = {'buffer_access':[], 'idle':{'count': 0}}
            self.cycle_access     = {}
            self.raw_access_stats = {'buffer_access':{}}
            self.reset_cycle_access()
       
    def reset_cycle_access(self):
        for arg in self.arg_lst:
            self.cycle_access.update({arg:0})
            
            
    def __ntick__(self):
        
        Module.__ntick__(self)
        
        idle = True
        for arg , value in self.cycle_access.items():
            if value > 0:
                idle = False
                break
        if idle:
            self.access_stats['idle']['count'] += 1
        else:
            cycle_access_lst = []
            for arg in self.arg_lst:
                cycle_access_lst.append(self.cycle_access[arg])
            cycle_access_tuple = tuple(cycle_access_lst)
            if cycle_access_tuple[6] == 1:
                self.access_stats['idle']['count'] += 1
            if cycle_access_tuple in self.raw_access_stats['buffer_access']:
                self.raw_access_stats['buffer_access'][cycle_access_tuple] += 1
            else:
                self.raw_access_stats['buffer_access'][cycle_access_tuple] = 1
        self.reset_cycle_access()
        
        for lm_idx in range(self.num_logical_managers):
            self.last_write_addr[lm_idx]                                         = self.curr_write_addr[lm_idx]
            
            self.logical_managers[lm_idx].approved_write_addr_in_cycle['fill']   = None 
            self.logical_managers[lm_idx].approved_write_addr_in_cycle['update'] = None 
            
            self.approved_write_data_in_cycle[lm_idx]['fill']                    = None
            self.approved_write_data_in_cycle[lm_idx]['update']                  = None
    
    def summerize_access_stats(self):
        for access_info_tuple, count in self.raw_access_stats['buffer_access'].items():
            arg_dict = {}
            arg_idx  = 0
            for arg_name in self.arg_lst:
                arg_dict[arg_name] = access_info_tuple[arg_idx]
                arg_idx += 1
            access_info_dict = {'arguments': arg_dict, 'count': count}
            self.access_stats['buffer_access'].append(access_info_dict.copy())
                
            
            
        
                
            
        
            
            
            
            