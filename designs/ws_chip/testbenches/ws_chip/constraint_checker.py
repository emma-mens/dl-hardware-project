import sys
import numpy as np
def check_constriant(mapping, shape, arch, ifmap_data, weights_data, bias_data):
        
        # ===============================================================================
        # Check Memory Constraint
        # ===============================================================================
        
        if shape['E'] * shape['F'] * mapping['M0'] * mapping['N0'] > \
           arch['depth']['PsumGLB'] * arch['width']['PsumGLB'] :
            print('\nVIOLATION: PsumGLB Memory Constraint Violated!!! Cannot map to design!\n')
            sys.exit(1)
                
        # ===============================================================================
        # Check Mapping Constraint
        # ===============================================================================
        if  mapping['N0'] > shape['N'] or mapping['C0'] > shape['C'] or mapping['M0'] > shape['M']:
            print('\nVIOLATION: at least of your mapping parameters exceed shape limit')                       
        
        # ===============================================================================
        # Check PE Array Constraint
        # ===============================================================================
        if mapping['C0'] > arch['PE_array'][0]:
            print('\nVIOLATION: PE Array Row Dimension Exceeded!!! Cannot map to design!\n')
            sys.exit(1)

        if mapping['M0'] > arch['PE_array'][1]:
            print('\nVIOLATION: PE Array col Dimension Exceeded!!! Cannot map to design!\n')
            sys.exit(1)
            
        # ===============================================================================
        # Check Data Shape Constraint
        # ===============================================================================
        if not ifmap_data.shape == (shape['H'], shape['W'], shape['C'], shape['N']):
            print('\nVIOLATION: ifmap data dimension is not for the selected layer shape\n')
            sys.exit(1)
        if not weights_data.shape == (shape['R'], shape['S'], shape['C'], shape['M']):
            print('\nVIOLATION: weights data dimension is not for the selected layer shape\n')
            sys.exit(1)
        if not len(bias_data) == shape['M']:
            print('\nVIOLATION: bias data dimension is not for the selected layer shape\n')
            sys.exit(1)            
        # ===============================================================================        
        # apply the extra padding if C % C0 != 0
        # ===============================================================================
        if not shape['C'] % mapping['C0'] == 0:
            print('NOTE: C % C0 != 0, extra padding is added ')
            new_C = (shape['C']//mapping['C0'] + 1) * mapping['C0']
            new_weights = np.zeros((shape['R'],shape['S'],new_C,shape['M'])).astype(np.int32)
            for row in range(shape['R']):
                for col in range(shape['S']):
                    for ichn in range(new_C):
                        for ochn in range(shape['M']):
                            if ichn < shape['C']:
                                new_weights[row][col][ichn][ochn] = weights_data[row][col][ichn][ochn]
            
            new_ifmap = np.zeros((shape['H'], shape['W'], new_C, shape['N'])).astype(np.int32)
            for row in range(shape['H']):
                for col in range(shape['W']):
                    for ichn in range(shape['C']):
                        new_ifmap[row][col][ichn][:] = ifmap_data[row][col][ichn][:]
               
            shape['C'] = new_C
            
            weights_data = np.copy(new_weights)
            ifmap_data = np.copy(new_ifmap)
      
           
        # ===============================================================================        
        # apply the extra padding if M % M0 != 0
        # ===============================================================================
        if not shape['M'] % mapping['M0'] == 0:
            print('NOTE: M % M0!= 0, extra padding is added')
            new_M = (shape['M']//mapping['M0'] + 1) * mapping['M0']
            new_weights = np.zeros((shape['R'],shape['S'],shape['C'],new_M)).astype(np.int32)
            for row in range(shape['R']):
                for col in range(shape['S']):
                    for ochn in range(shape['M']):
                        for ichn in range(shape['C']):
                            new_weights[row][col][ichn][ochn] = weights_data[row][col][ichn][ochn]
            
            new_bias = []
            for i in range(shape['M']):
                new_bias.append(bias_data[i])
            for j in range(new_M - shape['M']):
                new_bias.append(0)
               
            shape['M'] = new_M
            
            bias_data = new_bias
            weights_data = np.copy(new_weights)   
            
        # ===============================================================================        
        # apply the extra padding if N % N0 != 0
        # ===============================================================================
        if not shape['N'] % mapping['N0'] == 0:
            print('NOTE: N % n!= 0, extra padding is added')
            new_N = (shape['N']//mapping['N0'] + 1) * mapping['N0']
            new_ifmap = np.zeros((shape['H'], shape['W'], shape['C'], new_N)).astype(np.int32)
            for row in range(shape['H']):
                for col in range(shape['W']):
                    for ichn in range(shape['C']):
                        for ib in range(shape['N']):
                            new_ifmap[row][col][ichn][ib] = ifmap_data[row][col][ichn][ib]
            
            shape['N'] = new_N
            ifmap_data = np.copy(new_ifmap)               
            
            
        return (mapping, shape, ifmap_data, weights_data, bias_data)
