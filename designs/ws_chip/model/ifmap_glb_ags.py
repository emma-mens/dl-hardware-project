from nnsim.nnsimAddressGenerator import nnsimAddressGenerator as AG
import math
# ---------------------------------------------------------------------------
# Address Generator for ifmap data stored in GLB
# ---------------------------------------------------------------------------
class IFMapGLBFillAG(AG):
    def instantiate(self, setup):
        AG.instantiate(self, setup)
        
        self.class_name = 'IFMap_glb_fill_addr_generator'
        
        # -------------------------------------------------------------------
        # Hardware Properties
        # -------------------------------------------------------------------
        self.width                = setup['width']
        self.debug                = setup['debug'] + '-> ifmap'          
                              
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
        self.n_last               = self.N % self.n if not self.N % self.n == 0 else self.n
        self.e                    = math.ceil((self.H - self.R + 1) /self.U) 
        self.f                    = math.ceil((self.W - self.S + 1) /self.U)  
        
        # generate counters according to the mapping
        self.n_in_chn_tile        = math.ceil(self.C / self.k)
        self.n_out_chn_tile       = math.ceil(self.M / self.m)
        self.n_batch_tile         = math.ceil(self.N / self.n)
        self.n_tile               = self.n_in_chn_tile * self.n_out_chn_tile * self.n_batch_tile
        
        self.addr_per_pass        = self.k * self.E * self.F * self.n
        self.entries_per_pass     = math.ceil(self.addr_per_pass / self.width)
        
        # number of tiles the layer will incur, determines when should the address generation completely stop
        self.nreset               = self.n_tile  
        self.curr_tile            = 0
        
        self.new_tile_config()
        AG.configure(self)
        
    def new_tile_config(self):
        # new tile means m R*S weights has been processed, and new set of R*S weights will be sent to the PE array
        self.set                  = False
        self.count                = False 
        self.curr_pass            = 0
        
    def get_next_action(self):
        
        if not self.set:
            action = ('Set', {'action_config': {'addr': 0}})
            self.set = True
            
        elif self.set and not self.count:
            nsteps = self.entries_per_pass - 1
            action = ('Count', {'round_meta': {'nsteps': nsteps, 'reset_phy_head': True}})
            self.count = True 
            
        if self.set and self.count:
            self.set = False
            self.count = False
            self.curr_pass += 1
            if self.curr_pass == self.R * self.S:
                print('!**** ', self.debug,' ', self.type,' finished tile', self.curr_tile)
                self.curr_tile += 1
                self.new_tile_config()  # the fill of a tile is complete 
        return action
                
class IFMapGLBDrainAG(AG):
    
    def instantiate(self, setup):
        
        AG.instantiate(self, setup)
        self.class_name = 'IFMap_GLB_drain_addr_generator'
        # -------------------------------------------------------------------
        # Hardware Properties
        # -------------------------------------------------------------------
        self.width                = setup['width']   
        self.debug                = setup['debug'] + '-> ifmap'               
                              
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
        self.n_tile               = self.n_in_chn_tile * self.n_out_chn_tile * self.n_batch_tile
        self.addr_per_pass        = self.k * self.n * self.E * self.F
        self.entries_per_pass     = math.ceil(self.addr_per_pass / self.width)
        self.rounds_per_pass      = math.ceil(self.entries_per_pass / self.depth) 
        
        self.curr_tile            = 0
        self.curr_round           = 0
        self.nreset               = self.n_tile
        self.new_tile_config()
        AG.configure(self)
        
    def new_tile_config(self):
        self.reset_phy_head   = False if self.rounds_per_pass > 1 else True
        self.set              = False
        self.count            = False 
        self.curr_pass        = 0
        
   
    def get_next_action(self):
        
        if not self.set:
            action = ('Set', {'action_config': {'addr': 0},\
                              'round_meta': {'ndrop': 0, 'prereq': 'fill'}})
            self.set = True                    
            
        elif not self.count:
            nsteps = self.depth - 1 if self.curr_round != self.rounds_per_pass - 1 else\
                                   self.entries_per_pass - self.curr_round * self.depth - 1 
            action = ('Count', {'action_config': {},\
                                'round_meta': {'nsteps': nsteps, 'ndrop': nsteps + 1, 'prereq': 'fill', 'reset_phy_head': self.reset_phy_head}})
            self.count = True 
        if self.set and self.count:
            self.set = False
            self.count = False
            self.curr_round += 1
            if self.curr_round == self.rounds_per_pass - 1:
                self.reset_phy_head = True
            if self.curr_round == self.rounds_per_pass:
                self.curr_round = 0
                self.curr_pass += 1
                self.reset_phy_head = False if self.rounds_per_pass > 1 else True
                if self.curr_pass == self.R * self.S:
                    self.new_tile_config()
                    print('!**** ', self.debug,' ', self.type,' finished tile', self.curr_tile)
                    self.curr_tile += 1           
        return action           