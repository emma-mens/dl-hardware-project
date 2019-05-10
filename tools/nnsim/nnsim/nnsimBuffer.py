# -*- coding: utf-8 -*-

from nnsim.module import Module, ModuleList
from nnsim.nnsimChannel import  NoLatencyChannel
from copy import deepcopy


# ================================================================================
#                        nnsimBuffer
#    1. Provides setup for parametrizable smart buffer
#    2. Provides setup for address generators and destination calculators (if any)
#    3. Provides logic for parametrizable number of banks
# ================================================================================

# each virtual port has:
#    a channel for addr seq
#    a channel for input data
#    an addr generator
#    Optionally a destination generator
#    optionally a channel for output data  

class nnsimBuffer(Module):
    def instantiate (self, setup):
        
        self.class_name         = "nnsimBuffer"
        self.debug              = setup['debug']
        self.enabled_buffer     = setup['enabled_buffer'] if 'enabled_buffer' in setup.keys() else False
        self.reg_insert_opt     = setup['reg_insert_opt'] if 'reg_insert_opt' in setup.keys() else True
        self.nbanks             = setup['nbanks']
        
        # physical channels from outside world to write data into the buffer
        self.physical_chns = []
        
        # address generators for each memory bank
        self.addr_generator_type = []

        #======================================================================
        #                  Virtual Data Transfer Channels 
        #====================================================================== 
        #   - instantiated from outside
        #   - responsible for receiving data from outside
        #   - responsible for pushing data to outside
        
        self.fill_data_chns    = setup['fill_chns']\
                                 if 'fill_chns' in setup.keys() else None
                                   
        self.update_data_chns = setup['update_chns']\
                                if 'update_chns' in setup.keys() else None
                                   
        self.update_src_chns  = setup['update_src_chns']\
                                if 'update_src_chns' in setup.keys() else None
                                   
        self.drain_rsp_chns   = setup['drain_chns']\
                                if 'drain_chns' in setup.keys() else None
       
        # channels determine whether to perform the read or not, used for zero gating
        self.drain_enable_chns  = setup['drain_enable_chns']\
                                if 'drain_enable_chns' in setup.keys() else None
        
        # number of virtual ports for each memory bank 
        self.nvports = setup['nvports']   
        
        # constrcut dictionary to store all the data channels for ease of access
        self.vdata_chns = {}
        self.vdata_chns['fill'] = self.fill_data_chns if self.fill_data_chns is not None else None
        self.vdata_chns['update'] = self.update_data_chns if self.update_data_chns is not None else None
              
        #======================================================================
        #                  Address Generators 
        #====================================================================== 
        self.addr_generator_types = setup['addr_generators']        
    
        #======================================================================
        #                 Hardware Memory Properties 
        #======================================================================        
        self.depth     = setup['depth']      # depth of each memory bank
        self.width     = setup['width']       # # of data in each memory bank
        self.nports    = setup['nports']     # number of physical ports for each memory bank
        self.pvmapping = setup['pvmapping']
        
        #======================================================================
        #                Internal Channels and Data Structures
        #======================================================================   
        # addr generators
        self.addr_generators = []
        self.faddr_generator = ModuleList()
        self.uaddr_generator = ModuleList()  
        self.daddr_generator = ModuleList() 
        
        # addr chns 
        self.fill_addr_chn   = ModuleList()
        self.update_addr_chn = ModuleList()
        self.drain_addr_chn  = ModuleList()

        self.fill_local_addr_chn   = ModuleList()
        self.update_local_addr_chn = ModuleList()
        self.drain_local_addr_chn  = ModuleList()


        #------------------------------------------------------------------
        # Address Generators 
        #------------------------------------------------------------------              
        self.addr_generators = {'fill':   self.faddr_generator, \
                                'update': self.uaddr_generator, \
                                'drain':  self.daddr_generator}  
        
        #------------------------------------------------------------------
        # Address Channels for Addr Generators to Push to Sbuffer
        #------------------------------------------------------------------
        self.vaddr_chns       = {'fill':   self.fill_addr_chn,\
                                 'update': self.update_addr_chn,\
                                 'drain':  self.drain_addr_chn}
         
        self.local_vaddr_chns =  {'fill':    self.fill_local_addr_chn,\
                                  'update':  self.update_local_addr_chn,\
                                  'drain':   self.drain_local_addr_chn}
                
            #------------------------------------------------------------------
            # Setup Virtual Ports 
            #------------------------------------------------------------------                
           
            # each virtual port has:
            #    a channel for addr seq
            #    a channel for input data
            #    an addr generator
            #    optionally a destination generator
            #    optionally a channel for output data   
            
        for vport, num in self.nvports.items():
            for i in range(num):
                # ---------------------------------------------------------
                # Address Generator 
                # ---------------------------------------------------------                     
                # 1. setup single address generator for the virtual port
                if setup['multi_addr_generators'][vport] == 1:
                    self.vaddr_chns[vport].append(NoLatencyChannel())
                    self.local_vaddr_chns[vport].append(None)
                    addr_gen_setup = {'addr_chn': self.vaddr_chns[vport][i],\
                                      'width': self.width, \
                                      'type':  vport,\
                                      'id':    i,
                                      'depth': self.depth,\
                                      'debug': self.debug }  
                    addr_gen_obj = self.addr_generator_types[vport][i](addr_gen_setup)
                    self.addr_generators[vport].append(addr_gen_obj)
                
                # 2. update address comes from multiple instances of udpate address generators
                else:
                    self.addr_generators[vport].append(ModuleList())
                    # this channel pushes the chosen address from all the local address generators to the smartbuffer
                    self.vaddr_chns[vport].append(NoLatencyChannel()) 
                    self.local_vaddr_chns[vport].append(ModuleList())
                    for idx in range(setup['multi_addr_generators'][vport]):
                        self.local_vaddr_chns[vport][i].append(NoLatencyChannel())
                        addr_gen_setup = {'addr_chn': self.local_vaddr_chns[vport][i][idx],\
                                          'width':    self.width, \
                                          'type':     vport,\
                                          'id':       i,
                                          'depth': self.depth,\
                                          'debug':    self.debug + '[' + str(idx) + ']'}  
                        # assuming these generators are of the same type, just the offset (config) will be different
                        self.addr_generators[vport][i].append(self.addr_generator_types[vport][i](addr_gen_setup))


        #------------------------------------------------------------------
        # Setup Smartbuffer (deals with dependency and confict)
        #------------------------------------------------------------------ 
        
        # destination channels are for the destination calculator to push in destinations
        # destination_chns = self.destination_chns if self.mode == 'glb' else None
        
        # update_src_chns are channels for sending in external update address sequence
        update_src_chn   = self.update_src_chns if self.update_src_chns is not None else None
        
        # drain enable channels are channels that are used to send enable signeal to the buffer for read operations
        drain_enable_chn = self.drain_enable_chns if self.drain_enable_chns is not None else None
        
        # a smartbuffer is a unit of memory bank
        smartbuffer_setup = { 'depth':              self.depth,\
                              'width':              self.width, \
                              'nports':              self.nports, \
                              'pvmapping':           self.pvmapping,\
                              'nvports':             self.nvports,\
                              'vdata_chns':          self.vdata_chns, \
                              'vaddr_chns':          self.vaddr_chns,\
                              'drain_rsp_chns':      self.drain_rsp_chns,\
                              'drain_enable_chns':   drain_enable_chn,\
                              'update_src_chns':     update_src_chn,\
                              'enabled_buffer':      self.enabled_buffer,\
                              'reg_insert_opt':      self.reg_insert_opt,\
                              'debug':               self.debug } 
        self.smartbuffer_type = setup['smartbuffer_type']
        self.sbuffer = self.smartbuffer_type(smartbuffer_setup)
            

        #======================================================================
        #                  Stats Collection Info
        #======================================================================  
        self.attrs     =  { 'dpeth':       setup['depth'],\
                            'width':       setup['width'],\
                            'data_width':  setup['data_width'],\
                            'nbanks':      setup['nbanks'],\
                            'nports':      setup['nports']}
            
    def configure(self, config):
        
        self.clk_gated = False
        self.wr_done   = False
        self.data_set  = 0    # data_set is used to keep track of the remianing data in the channel
                              # if input bandwidth i> memory width => data_set >1

        #--------------------------------------------------
        # Static Clock Gating of a Memory Bank
        #--------------------------------------------------
        self.sbuffer.configure(config)
        
        #------------------------------------------------------------------
        # Configure Address Generators and Destination Generators (IF ANY)
        #------------------------------------------------------------------            
        for port_type, n in self.nvports.items():            
            # if there is this virtual channel in instantiation
            if not n == 0:
                for i in range(n):
                    if issubclass(type( self.addr_generators[port_type][i]), Module):
                        config[port_type]['clk_gated'] = False
                        self.addr_generators[port_type][i].configure(config[port_type])
#                        print(self.debug, 'configing: ', port_type, ' ', i)
                        
                    else:
                        print(port_type)
                        for idx in range(self.addr_generators[port_type][i].get_len()):
                           local_config = deepcopy(config[port_type])
                           local_config.pop('addr_gen_config')
                           if str(idx) in config[port_type]['addr_gen_config'][i]:
                               local_config['addr_gen_config'] = config[port_type]['addr_gen_config'][i][str(idx)]
                               local_config['clk_gated'] = True
                           else:
                               local_config['clk_gated'] = True
                           self.addr_generators[port_type][i][idx].configure(local_config) 
                    

                    

                        
                        
