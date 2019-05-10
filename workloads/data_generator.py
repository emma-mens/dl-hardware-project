from yaml import load
from random import randint
import numpy as np

# --------------------------------------------------
# Choose what data you are trying to generate
# --------------------------------------------------
weights_density = 100
ifmap_density =  100
shape_file_name = 'shape1.yaml'
shape_info = load(open('layer_shapes/' + shape_file_name))

H = shape_info['H']
W = shape_info['W']
R = shape_info['R']
S = shape_info['S']
E = shape_info['E']
F = shape_info['F']
C = shape_info['C']
M = shape_info['M']
U = shape_info['U']
N = shape_info['N']


ifmap = np.zeros((H, W, C, N)).astype(np.int32)
weights = np.zeros((R, S, C, M)).astype(np.int32)
bias = []

# >>>>  generate ifmap
for n in range(N):
    for c in range(C):
        for row in range(H):
            for col in range(W):
                rand = randint(1,100)
                if rand <= ifmap_density:
                    ifmap[row][col][c][n] = randint(1,3)
                else:
                    ifmap[row][col][c][n] = 0

# >>>>  generate weights
for m in range(M):
    for c in range(C):
        for row in range(R):
            for col in range(S):
                rand = randint(1,100)
                if rand < weights_density:
                    weights[row][col][c][m] = randint(1,3)
                else:
                    weights[row][col][c][m] = 0

# >>>> generate bias
for m in range(M):
    bias.append(randint(1,3)-10)


prefix = shape_file_name[0:-5]
np.save('ifmap_data/' + prefix + '_density_'+ str(ifmap_density), ifmap)
np.save('weights_data/' + prefix +'_density_'+ str(weights_density), weights)
np.save('bias_data/' + shape_file_name[0:-5]+'_bias', bias)
