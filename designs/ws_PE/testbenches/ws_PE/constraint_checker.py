import sys
def check_constriant(mapping, shape, arch, ifmap_data, weights_data, bias_data):
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
    # Check Mapping Constraint
    # ===============================================================================
    if  mapping['N0'] > shape['N']:
        print('\nVIOLATION: at least of your mapping parameters exceed shape limit')
        sys.exit(1)