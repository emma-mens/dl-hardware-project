from nnsim.nnsimAddressGenerator import nnsimAddressGenerator as AG
import math

class PsumGLBFillAG(AG):
    def instantiate(self, setup):

        AG.instantiate(self, setup)
        
        self.class_name                        = 'Psum_GLB_fill_addr_generator'
        
        # -------------------------------------------------------------------
        # Hardware Properties
        # -------------------------------------------------------------------
        self.width                             = setup['width']   
        self.debug                             = setup['debug'] + '-> psum'             
                              
    def configure(self, config):
        self.depth                             = config['logical_depth']
        # 2D shape of the datatype
        self.S                                 = config['shape']['S']  # number of filter cols 
        self.W                                 = config['shape']['W']  # number of ifmap cols
        self.F                                 = config['shape']['F']  # number of ofmap cols
        
        self.R                                 = config['shape']['R']  # number of filter rows
        self.H                                 = config['shape']['H']  # number of ifmap  rows
        self.E                                 = config['shape']['E']  # number of ofmap  rows 
        
        self.N                                 = config['shape']['N']  # total number of ifmaps
        self.M                                 = config['shape']['M']  # total number of filters
        self.C                                 = config['shape']['C']  # total number of input channels
        
        self.U                                 = config['shape']['U']  # stride size
        
        # mapping parameters needed 
        self.k                                 = config['mapping']['C0'] # number of tile input channels
        self.m                                 = config['mapping']['M0'] # number of tile output channels
        self.n                                 = config['mapping']['N0'] # number of tile ifmaps
        self.n_last                            = self.N % self.n if not self.N % self.n == 0 else self.n
        self.e                                 = math.ceil((self.H - self.R + 1) /self.U) 
        self.f                                 = math.ceil((self.W - self.S + 1) /self.U) 
        
        # generate counters according to the mapping
        self.n_in_chn_tile                     = math.ceil(self.C / self.k)
        self.n_out_chn_tile                    = math.ceil(self.M / self.m)
        self.n_batch_tile                      = math.ceil(self.N / self.n)
        self.n_tile                            = self.n_out_chn_tile * self.n_batch_tile
        
        self.addr_per_tile                     = self.m * self.e * self.f * self.n
        self.entries_per_tile                  = math.ceil(self.addr_per_tile/self.width)
        # number of tiles the layer will incur, determines when should the address generation completely stop
        self.nreset                            = self.n_tile
        self.curr_tile                         = 0
 
        self.new_tile_config()
        AG.configure(self)
        
    def new_tile_config(self):
        
        self.set                  = False
        self.count                = False 
        
        
        
    def get_next_action(self):
        
        if not self.set:
            action     = ('Set', {'action_config': {'addr': 0}})
            self.set   = True
            
        elif self.set and not self.count:
            nsteps     = self.entries_per_tile - 1
            action     = ('Count', {'round_meta': {'nsteps': nsteps, 'reset_phy_head': True}})
            self.count = True
        
        if self.set and self.count:
            print('~~~', self.debug,' ', self.type,' finished out_tile', self.curr_tile)
            self.curr_tile += 1
            self.new_tile_config()  # the fill of a tile is complete 
        
        return action



class PsumGLBDrainAG(AG):
    def instantiate(self, setup):

        AG.instantiate(self, setup)
        
        self.class_name                        = 'Psum_GLB_drain_addr_generator'
        
        # -------------------------------------------------------------------
        # Hardware Properties
        # -------------------------------------------------------------------
        self.width                             = setup['width']  
        self.debug                             = setup['debug'] + '-> psum'             
                              
    def configure(self, config):
        self.depth                             = config['logical_depth']
        # 2D shape of the datatype
        self.S                                 = config['shape']['S']  # number of filter cols 
        self.W                                 = config['shape']['W']  # number of ifmap cols
        self.F                                 = config['shape']['F']  # number of ofmap cols
        
        self.R                                 = config['shape']['R']  # number of filter rows
        self.H                                 = config['shape']['H']  # number of ifmap  rows
        self.E                                 = config['shape']['E']  # number of ofmap  rows 
        
        self.N                                 = config['shape']['N']  # total number of ifmaps
        self.M                                 = config['shape']['M']  # total number of filters
        self.C                                 = config['shape']['C']  # total number of input channels
        
        self.U                                 = config['shape']['U']  # stride size
        
        # mapping parameters needed 
        self.k                                 = config['mapping']['C0'] # number of tile input channels
        self.k_last                            = self.C % self.k if not self.C % self.k == 0 else self.k
        self.m                                 = config['mapping']['M0'] # number of tile output channels
        self.m_last                            = self.M % self.m if not self.M % self.m == 0 else self.m
        self.n                                 = config['mapping']['N0'] # number of tile ifmaps
        self.n_last                            = self.N % self.n if not self.N % self.n == 0 else self.n
        self.e                                 = math.ceil((self.H - self.R + 1) /self.U) 
        self.f                                 = math.ceil((self.W - self.S + 1) /self.U) 
        
        # generate counters according to the mapping
        self.n_in_chn_tile                     = math.ceil(self.C / self.k)
        self.n_out_chn_tile                    = math.ceil(self.M / self.m)
        self.n_batch_tile                      = math.ceil(self.N / self.n)
        self.n_tile                            = self.n_out_chn_tile * self.n_batch_tile
        
        self.entries_per_pass                  = math.ceil(self.m * self.e * self.f * self.n / self.width)
            
        # number of tiles the layer will incur, determines when should the address generation completely stop
        self.nreset                            = self.n_tile
        self.curr_tile                         = 0
        self.new_tile_config()
        AG.configure(self)
        
    def new_tile_config(self):
        
        self.set                  = False
        self.count                = False 

        self.reset_phy_head       = True if self.R == 1 and self.S == 1 and self.n_in_chn_tile == 1 else False
        self.out_chn_tile_done    = False
        self.curr_in_chn_tile     = 0
        self.curr_weights_col     = 0
        self.curr_weights_row     = 0
        self.prereq               = 'fill'
        self.ndrop                = 0 if not (self.R == 1 and self.S == 1 and self.n_in_chn_tile == 1) \
                                      else self.entries_per_pass
        
#        print(self.debug, self.type, 'configuring for new tile')
        
    def get_next_action(self):
        
        if not self.set:
            action = ('Set', {'action_config': {'addr': 0},\
                              'round_meta':    {'ndrop': 0, \
                                                'prereq': self.prereq}})
            self.set = True
        elif not self.count:
            nsteps = self.entries_per_pass - 1
            self.count = True
            action = ('Count', {'action_config': {},
                      'round_meta': {'nsteps': nsteps, \
                                     'ndrop':  self.ndrop,\
                                     'prereq': self.prereq,\
                                     'reset_phy_head': self.reset_phy_head}})
        
        if self.set and self.count:
            self.set        = False
            self.count      = False               
            self.prereq     = 'update' # the data has to be updated first and then sent for the next round of computation
            
            self.curr_weights_col += 1
            
            if self.curr_weights_col == self.S:
                self.curr_weights_col = 0
                self.curr_weights_row += 1
                
                if self.curr_weights_row == self.R:
                    self.curr_weights_row = 0
                    self.curr_in_chn_tile += 1
                    
            if self.curr_weights_col == self.S - 1 and\
               self.curr_weights_row == self.R - 1 and\
               self.curr_in_chn_tile == self.n_in_chn_tile-1:
                    self.ndrop = self.entries_per_pass
                    self.reset_phy_head = True
                    
            if self.curr_in_chn_tile == self.n_in_chn_tile:
                print('~~~', self.debug,' ', self.type,' finished out_chn_tile:', self.curr_tile)
                self.curr_tile += 1
                self.new_tile_config() # the drain of an out channel tile is complete
            
#        print(self.debug, action)        
        return action



class PsumGLBUpdateAG(AG):
    def instantiate(self, setup):
        AG.instantiate(self, setup)
        self.class_name           = 'Psum_GLB_update_addr_generator'
        # -------------------------------------------------------------------
        # Hardware Properties
        # -------------------------------------------------------------------
        self.width                = setup['width'] 
        self.debug                = setup['debug'] + '-> psum'             
                              
    def configure(self, config):
        self.depth                = config['logical_depth']
        # 2D shape of the datatype
        self.S                    = config['shape']['S']  # number of filter cols 
        self.W                    = config['shape']['W']  # number of ifmap cols
        self.F                    = config['shape']['F']  # number of ofmap cols
        
        self.R                    = config['shape']['R']  # number of filter rows
        self.H                    = config['shape']['H']  # number of ifmap  rows
        self.E                    = config['shape']['E']  # number of ofmap  rows 
        
        self.N                    = config['shape']['N']  # total number of ifmaps
        self.M                    = config['shape']['M']  # total number of filters
        self.C                    = config['shape']['C']  # total number of input channels
        
        self.U                    = config['shape']['U']  # stride size
        
        # mapping parameters needed 
        self.k                    = config['mapping']['C0'] # number of tile input channels
        self.m                    = config['mapping']['M0'] # number of tile output channels
        self.n                    = config['mapping']['N0'] # number of tile ifmaps
        self.e                    = math.ceil((self.H - self.R + 1) /self.U) 
        self.f                    = math.ceil((self.W - self.S + 1) /self.U) 
        
        # generate counters according to the mapping
        self.n_in_chn_tile        = math.ceil(self.C / self.k)
        self.n_out_chn_tile       = math.ceil(self.M / self.m)
        self.n_batch_tile         = math.ceil(self.N / self.n)
        self.n_tile               = self.n_out_chn_tile * self.n_batch_tile
        
        self.entries_per_pass     = math.ceil(self.m * self.e * self.f * self.n / self.width)
            
        # number of tiles the layer will incur, determines when should the address generation completely stop
        self.nreset                  = self.n_tile
        self.curr_tile               = 0
        self.new_tile_config()
        AG.configure(self)
    
    def new_tile_config(self):
        
        self.set                      = False
        self.count                    = False 
        self.out_chn_tile_done        = False
        self.curr_weights_col         = 0
        self.curr_weights_row         = 0
        self.curr_in_chn_tile         = 0
        
#        print(self.debug, self.type, 'configuring for new tile')
        
    def get_next_action(self):
        
        # update channel should have the same address pattern as the drain channel
        if self.out_chn_tile_done:
            print('~~~', self.debug,' ', self.type,' finished out tile', self.curr_tile)
            self.curr_tile += 1
            self.new_tile_config() # the drain of a tile is complete
            return ('reset_phead',{})   
            
        if not self.set:
            action = ('Set', {'action_config': {'addr': 0, 'ndrop': 0}})
            self.set = True
        elif not self.count:
            nsteps = self.entries_per_pass - 1
            self.count = True
            action = ('Count', {'round_meta': {'nsteps': nsteps}})
        
        if self.set and self.count:
            self.set        = False
            self.count      = False   

            self.curr_weights_col += 1
            if self.curr_weights_col == self.S:
                self.curr_weights_col = 0
                self.curr_weights_row += 1
                if self.curr_weights_row == self.R:
                    self.curr_weights_row = 0
                    self.curr_in_chn_tile += 1
            if self.curr_in_chn_tile == self.n_in_chn_tile - 1 \
               and self.curr_weights_row == self.R - 1 \
               and self.curr_weights_col == self.S - 1:
                self.out_chn_tile_done = True

        return action            
        