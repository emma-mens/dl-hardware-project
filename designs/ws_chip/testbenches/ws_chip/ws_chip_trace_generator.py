# -*- coding: utf-8 -*-
from scipy.io  import loadmat 
from scipy.signal import correlate2d
import math
import numpy as np

INT_32_MAX = 2147483647

class ws_chip_trace_generator():
    
    def _init__(self):
        self.class_name = 'ws_chip_trace_generator'
        
    
    def configure(self, config):
        
        self.mapping            = config['mapping']
        self.shape              = config['shape']
        self.ifmap              = config['ifmap_data']
        self.weights            = config['weights_data']
        self.biases             = config['bias_data']
        self.GLB_width          = 2
       
    # check if the final result is correct
    def conv(self,x,W,b,out_size):
        y = np.zeros([out_size[0], out_size[1], out_size[2], out_size[3]]).astype(np.int32)
        for batch_idx in range(out_size[3]):
            for out_channel in range(out_size[2]):
                for in_channel in range(x.shape[2]):
                    W_c = W[:, :, in_channel, out_channel]
                    x_c = x[:, :, in_channel, batch_idx]
                    y[:, :, out_channel, batch_idx] += correlate2d(x_c, W_c, mode="valid")
                y[:, :, out_channel, batch_idx] += b[out_channel]
        return y
            
    
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

        k = self.mapping['C0']
        m = self.mapping['M0']
        n = self.mapping['N0']

        # -------------------------------------------------------------------------------------
        # extra padding for nondivisible input channels
        if  not C % k == 0:
            print('NOTE: C % k!= 0, extra padding is added to avoid data pollution between output tiles')
            new_C = (C//k + 1) * k
            new_weights = np.zeros((R,S,new_C,M))
            new_weights[:,:,0:C,:] = self.weights
            for row in range(R):
                for col in range(S):
                    for ichn in range(C):
                        new_weights[row][col][ichn][:] = self.weights[row][col][ichn][:]
            self.weights = new_weights
            
            new_iacts = np.zeros((H, W, new_C, N))
            for row in range(H):
                for col in range(W):
                    for ichn in range(C):
                        new_iacts[row][col][ichn][:] = self.iacts[row][col][ichn][:]
            self.iacts = new_iacts
            C = new_C
            print(self.weights)
        

        # container for psum in value
        oshape = (int((H-R)/U)+ 1, int((W-S)/U) + 1, M, N)
        self.psum   = np.zeros(oshape, np.int64)
        for batch_idx in range(N):
            for out_chn in range(oshape[2]):
                for e in range(oshape[0]):
                    for f in range(oshape[1]):
                        self.psum[e][f][out_chn][batch_idx] = self.biases[out_chn]
            
        # --------------------------------------------------------------------------------------
        # tiling
        n_in_chn_tile  = math.ceil(C / k)
        n_out_chn_tile = math.ceil(M / m)
        n_batch_tile   = math.ceil(N / n)
        
        
        
        # ---------------- construct weight, ifmap, and psum in sequence  ------------------------------------
        # there is no reuse in the weight GLB, therefore, every single data that needs to be sent to the PE array comes from offchip
        w_seq   = []
        i_seq   = []
        pin_seq = []
        
        for batch_tile in range(n_batch_tile):
            for out_chn_tile in range(n_out_chn_tile):
                for in_chn_tile in range(n_in_chn_tile):
                    for row in range(R):
                        for col in range(S):
                            for in_chn in range(k):
                                for out_chn in range(m):
                                    curr_out_chn = out_chn_tile * m + out_chn
                                    curr_in_chn  = in_chn_tile * k + in_chn
#                                    print(curr_in_chn, curr_out_chn)
                                    if curr_in_chn < C and curr_out_chn < M:
                                        weight = self.weights[row, col, curr_in_chn, curr_out_chn]
                                        w_seq.append(weight)
                    address_per_tile = R * S * k * m 
                    if not address_per_tile % self.GLB_width == 0:
                        for pad_idx in range(self.GLB_width - address_per_tile % self.GLB_width):
                            w_seq.append(INT_32_MAX)
                                    
        for batch_tile in range(n_batch_tile):   
            for out_chn_tile in range(n_out_chn_tile):
                for in_chn_tile in range(n_in_chn_tile):
                    for w_row in range(R):
                        for w_col in range(S):
                            for p_row in range(E):
                                for p_col in range(F):
                                    for batch in range(n):
                                        for in_chn in range(k):
                                            curr_in_chn = in_chn_tile * k + in_chn
                                            curr_batch  = batch_tile * n + batch
                                            curr_row = p_row * U + w_row
                                            curr_col = p_col * U + w_col
                                            if curr_in_chn < C and curr_batch < N:
                                                ifmap = self.ifmap[curr_row, curr_col, curr_in_chn, curr_batch]
                                                i_seq.append(ifmap)
                            address_per_pass = k * n * E * F 
                            if not address_per_pass % self.GLB_width == 0:
                                for pad_idx in range(self.GLB_width - address_per_pass % self.GLB_width):
                                    i_seq.append(INT_32_MAX)
                    
                
        for batch_tile in range(n_batch_tile):   
            for out_chn_tile in range(n_out_chn_tile):
                for row in range(E):
                    for col in range(F):
                        for batch in range(n):
                            for out_chn in range(m):
                                curr_out_chn = out_chn_tile * m + out_chn
                                curr_batch  = batch_tile * n + batch
                                if curr_out_chn < M and curr_batch < N:
                                    psum = self.psum[row, col, curr_out_chn, curr_batch]
                                    pin_seq.append(psum)
                address_per_out_tile = E * F * m * n
                if not address_per_out_tile % self.GLB_width == 0:
                    for pad_idx in range(self.GLB_width - address_per_out_tile % self.GLB_width):
                        pin_seq.append(INT_32_MAX)


        # ----------------- construct psum out sequence ------------------------------------   
        reference = self.conv(self.ifmap, self.weights, self.biases, oshape).astype(np.int32)
        pout_seq = []   
        for batch_tile in range(n_batch_tile):                  
            for out_chn_tile in range(n_out_chn_tile):
                    for row in range(E):
                        for col in range(F):
                            for batch_idx in range(n):
                                for out_chn in range(m):
                                    curr_out_chn = out_chn_tile * m + out_chn
                                    curr_batch   = batch_tile * n + batch_idx
                                    if curr_out_chn < M and curr_batch < N:
                                        psum_out = reference[row, col, curr_out_chn, batch_idx + batch_tile * n]
                                        pout_seq.append(psum_out)
        return{'weights': w_seq, 'ifmap': i_seq, 'psum_in': pin_seq, 'psum_out': pout_seq}
            
    
    def generate_trace(self):
        for key, value in self.mapping.items():
            if not key == 'update_addr_generator_config':
                self.mapping[key] = int(value)
            
        for key, value in self.shape.items():
            self.shape[key] = int(value)     
        
        # retrieve the parsed data
        seq_dict = self.process()
        
        
        return seq_dict

                            
