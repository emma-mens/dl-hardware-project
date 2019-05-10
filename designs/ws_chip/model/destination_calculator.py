
from nnsim.module import Module
import math

class IFmapNoCDestCalc(Module):
    def instantiate(self, setup):
        
        self.class_name           = 'IFmapNoCDestCalc'
        
        
        self.debug                = setup['debug']  
        self.out_chn              = setup['out_chn']  
        self.out_channel_width    = setup['out_channel_width']
                              
    def configure(self, config):
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
        self.e                    = math.ceil((self.H - self.R + 1)/self.U) 
        self.f                    = math.ceil((self.W - self.S + 1)/self.U) 

        
        # generate counters according to the mapping
        self.n_in_chn_tile        = math.ceil(self.C / self.k)
        self.n_out_chn_tile       = math.ceil(self.M / self.m) 
        self.n_batch_tile         = math.ceil(self.N / self.n)
#        
        self.n_total_chn_tile     = self.n_in_chn_tile * self.n_out_chn_tile
        self.n_tile               = self.n_in_chn_tile * self.n_out_chn_tile * self.n_batch_tile
        
        self.curr_tile            = 0
        self.layer_done           = False
        
        self.new_tile_config()
        self.get_next_destination()
        
    def new_tile_config(self):
        self.curr_data_row     = 0
        self.curr_data_col     = 0
        self.curr_data_in_chn  = 0
        self.curr_data_batch   = 0
        self.curr_weights_col  = 0
        self.curr_weights_row  = 0

    
    def get_next_destination(self):
        if self.curr_tile == self.n_tile:
            self.layer_done = True
#            print('IFmapDestCalc layer done')
            return
        
        self.destination = []    # stores a set of destinations for each data to be sent
        # need to send the same ifmap values to all of the different filter PE sets
        pe_row = self.curr_data_in_chn
        for pe_col in range(self.m):
            self.destination.append([pe_row, pe_col])
#        print(self.debug, self.destination)
        
        self.curr_data_in_chn += 1
        if self.curr_data_in_chn == self.k:
            self.curr_data_in_chn = 0
            self.curr_data_batch += 1
            if self.curr_data_batch == self.n:
                self.curr_data_batch = 0            
                self.curr_data_col += 1
                if self.curr_data_col == self.f:
                    self.curr_data_col = 0
                    self.curr_data_row += 1
                    if self.curr_data_row == self.e:
                        self.curr_data_row = 0
                        self.curr_weights_col += 1
                        if self.curr_weights_col == self.S:
                            self.curr_weights_col = 0
                            self.curr_weights_row += 1
                            if self.curr_weights_row == self.R:
                                self.curr_weights_row = 0
                                self.curr_tile += 1
                                self.new_tile_config()
                            
    def tick(self):
        if self.layer_done:
            return
        if self.out_chn.vacancy():
            self.out_chn.push(self.destination)
            self.get_next_destination()
            
# --------------------------------------------------------------------------
# Destinations for the weights data that comes from the WeightsGLB
# --------------------------------------------------------------------------
class WeightsNoCDestCalc(Module):
    def instantiate(self, setup):
        
        self.class_name           = 'IFmapNoCDestCalc'
        
        
        self.debug                = setup['debug']  
        self.out_chn              = setup['out_chn']  
        self.out_channel_width    = setup['out_channel_width']
                              
    def configure(self, config):
        # 2D shape of the datatype
        self.S                    = config['shape']['S']  # number of filter cols 
        self.W                    = config['shape']['W']  # number of ifmap cols
        self.F                    = config['shape']['F']  # number of ofmap cols
        
        self.R                    = config['shape']['R']  # number of filter rows
        self.H                    = config['shape']['H']  # number of ifmap  rows
        self.E                    = config['shape']['E']  # number of ofmap  rows 
        
        self.N                    = config['shape']['N']  # total number of ifmaps
        self.M                    = config['shape']['M']  # total number of filters
        self.C                    = config['shape']['C']  # tota; number of input channels
        self.U                    = config['shape']['U']
        
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
        
        self.n_total_chn_tile     = self.n_in_chn_tile * self.n_out_chn_tile
        self.n_tile               = self.n_in_chn_tile * self.n_out_chn_tile * self.n_batch_tile 
        
        self.curr_tile            = 0
        self.layer_done           = False
        self.new_tile_config()
        self.get_next_destination()
        
    def new_tile_config(self):
        self.curr_data_row        = 0
        self.curr_data_col        = 0
        self.curr_data_in_chn     = 0
        self.curr_data_out_chn    = 0
        self.curr_out_chn_set     = 0
        self.curr_in_chn_set      = 0
        self.curr_data_batch      = 0
        
            
    
    def get_next_destination(self):
        # if the layer is done, return None as the destination
        if self.curr_tile  == self.n_tile:
            self.layer_done = True
#            print('WeightsDestCalc Layer done')
            return
        self.destination = []   # stores a set of destinations for each data to be sent
        
        pe_row = self.curr_data_in_chn
        pe_col = self.curr_data_out_chn
        
        self.destination.append([pe_row, pe_col])
        self.curr_data_out_chn += 1
        if self.curr_data_out_chn == self.m:
            self.curr_data_out_chn = 0
            self.curr_data_in_chn += 1
            if self.curr_data_in_chn == self.k:
                self.curr_data_in_chn = 0
                self.curr_data_col += 1
                if self.curr_data_col == self.S:
                    self.curr_data_col = 0
                    self.curr_data_row += 1
                    if self.curr_data_row == self.R:
                        self.curr_data_row = 0
                        self.curr_tile += 1
                        self.new_tile_config()
    def tick(self):
        if self.layer_done:
            return
        if self.out_chn.vacancy():
            self.out_chn.push(self.destination)
#            print(self.debug, ' ', self.destination)
            self.get_next_destination()        


# --------------------------------------------------------------------------
# Destinations for the psum in data that comes from the WeightsGLB
# --------------------------------------------------------------------------
class PsumInNoCDestCalc(Module):
    def instantiate(self, setup):
        
        self.class_name           = 'PsumInNoCDestCalc'
        
        self.debug                = setup['debug']  
        self.out_chn              = setup['out_chn']  
        self.out_channel_width    = setup['out_channel_width']
                              
    def configure(self, config):
        # 2D shape of the datatype
        self.S                    = config['shape']['S']  # number of filter cols 
        self.W                    = config['shape']['W']  # number of ifmap cols
        self.F                    = config['shape']['F']  # number of ofmap cols
        
        self.R                    = config['shape']['R']  # number of filter rows
        self.H                    = config['shape']['H']  # number of ifmap  rows
        self.E                    = config['shape']['E']  # number of ofmap  rows 
        
        self.N                    = config['shape']['N']  # total number of ifmaps
        self.M                    = config['shape']['M']  # total number of filters
        self.C                    = config['shape']['C']  # tota; number of input channels
        self.U                    = config['shape']['U']
        
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
        
        self.n_total_chn_tile     = self.n_in_chn_tile * self.n_out_chn_tile
        self.n_tile               = self.n_in_chn_tile * self.n_out_chn_tile * self.n_batch_tile 

        self.curr_tile            = 0
        # for each input channel tile, the data comes from reusing the GLB data
        # for each output channel tile, a new tile of data is reloaded from DRAM
        # but the difference is invisible from the NoCs
        self.layer_done           = False
        self.new_tile_config()
        self.get_next_destination()
        
    def new_tile_config(self):
        self.curr_data_row        = 0
        self.curr_data_col        = 0
        self.curr_data_in_chn     = 0
        self.curr_data_out_chn    = 0
        self.curr_out_chn_set     = 0
        self.curr_out_chn_vset    = 0
        self.curr_in_chn_set      = 0
        self.curr_ifmap_batch     = 0
        self.curr_weights_col     = 0
        self.curr_weights_row     = 0
        
            
    def get_next_destination(self):
        
        if self.curr_tile == self.n_tile:
            self.layer_done = True
#            print('PsumIn Dest Calc layer done')
            return
        
        self.destination = []   # stores a set of destinations for each data to be sent
        pe_col           = self.curr_data_out_chn
        pe_row           = 0
        
        self.destination.append([pe_row, pe_col])
        
        self.curr_data_out_chn += 1
        if self.curr_data_out_chn == self.m:
            self.curr_data_out_chn = 0
            self.curr_ifmap_batch += 1
            if self.curr_ifmap_batch == self.n:
                self.curr_ifmap_batch = 0
                self.curr_data_col += 1
                if self.curr_data_col == self.f:
                    self.curr_data_col = 0
                    self.curr_data_row += 1
                    if self.curr_data_row == self.e:
                        self.curr_data_row = 0
                        self.curr_weights_col += 1
                        if self.curr_weights_col == self.S:
                            self.curr_weights_col = 0
                            self.curr_weights_row += 1
                            if self.curr_weights_row == self.R:
                                self.curr_weights_row = 0
                                self.curr_tile += 1
                                self.new_tile_config()

                               
    def tick(self):
        if self.layer_done:
            return
        if self.out_chn.vacancy():
            self.out_chn.push(self.destination)
#            print(self.debug, ' ', self.destination)
#            print('data_out_chn:', self.curr_data_out_chn, 'data_col:', self.curr_data_col, \
#                  'data_row:', self.curr_data_row, 'weight_col:', self.curr_weights_col, 'weight_row:', self.curr_weights_row)
            self.get_next_destination()   
            
            