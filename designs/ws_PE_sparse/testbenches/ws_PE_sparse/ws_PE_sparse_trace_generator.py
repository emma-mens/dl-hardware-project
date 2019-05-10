# -*- coding: utf-8 -*-

import numpy as np
import math

class ws_PE_sparse_trace_generator():
    
    def _init__(self):
        self.class_name = 'PE_trace_generator'
        
    
    def configure(self, config):
        
        self.ifmap              = config['ifmap_data']
        self.weights            = config['weights_data']
        self.bias               = config['bias_data']
        self.mapping            = config['mapping']
        self.shape              = config['shape']
       
    
    def process(self):
        # parse the input information
        H = self.shape['H']
        W = self.shape['W']
        R = self.shape['R']
        S = self.shape['S']
        E = self.shape['E']
        F = self.shape['F']
        C = self.shape['C']
        M = self.shape['M']
        U = self.shape['U']
        N = self.shape['N']

        N0 = self.mapping['N0']
        
        # container for psum in value
        oshape = (int((H-R)/U)+ 1, int((W-S)/U) + 1, M, N)
        self.psum   = np.zeros(oshape, np.int32)
        for batch_idx in range(N):
            for out_chn in range(oshape[2]):
                for e in range(oshape[0]):
                    for f in range(oshape[1]):
                        self.psum[e][f][out_chn][batch_idx] = self.bias[out_chn]
            
        
        # initializing input stream
        w_seq = []
        ifmap_seq = []
        psum_in_seq = []
        psum_out_seq = []
        
        batch_tile = math.ceil(N/N0)
        
        
        # generating input streams for all data types
        for curr_batch_tile in range(batch_tile):
            for out_chn in range(M):
                for in_chn in range(C):
                    for weights_row in range(R):
                        for weights_col in range(S):
                            weight = self.weights[weights_row, weights_col, in_chn , out_chn]
                            w_seq.append(weight)
                            for ofmap_row in range(E):
                                for ofmap_col in range(F):
                                    for curr_n in range(N0 ):
                                        ifmap = self.ifmap[weights_row + ofmap_row][weights_col+ ofmap_col][in_chn][curr_n + curr_batch_tile * N0 ]
                                        psum_in = self.psum[ofmap_row][ofmap_col][out_chn][curr_n + curr_batch_tile * N0]
                                        ifmap_seq.append(ifmap)
                                        psum_in_seq.append(psum_in)
                                        
                                        psum_out = ifmap * weight + psum_in
                                        self.psum[ofmap_row][ofmap_col][out_chn][curr_n + curr_batch_tile * N0 ] = psum_out
                                        psum_out_seq.append(psum_out)
                
        # return the generated streams
        return{'weights': w_seq, 'ifmap': ifmap_seq, 'psum_in': psum_in_seq, 'psum_out': psum_out_seq}
            
    
    
    def generate_trace(self):
        # make sure all of the mapping/shape params are integers
        for key, value in self.mapping.items():
            self.mapping[key] = int(value)
            
        for key, value in self.shape.items():
            self.shape[key] = int(value)     
        
        # retrieve the parsed data
        seq_dict = self.process()
        
        
        return seq_dict
