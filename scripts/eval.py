# -*- coding: utf-8 -*-


import sys,os, subprocess, importlib

if __name__ == '__main__':

    if len(sys.argv) < 7:
        print('Usage: python eval.py <design_name> <architecture_name> <layer_name> <mapping_name> <weights_data_name> <ifmap_data_name>')
        sys.exit(0)

    design_name               = sys.argv[1]
    architecture_path_input   = sys.argv[2]
    layer_path_input          = sys.argv[3]
    mapping_path_input        = sys.argv[4]
    bias_data_path_input      = sys.argv[5]
    weights_data_path_input   = sys.argv[6]
    ifmap_data_path_input     = sys.argv[7]
    stats_data_path_input     = sys.argv[8]

    print('Starting Evaluation for Design:', design_name)
    # ========================================================================
    # !!!!! PLEASE MAKE SURE THE PYTHON EXEC PATH/ ENV_VAR IS CORRECT
    # ========================================================================
    # python_exec = os.path.normpath('/homes/nelliewu/anaconda3/bin/python')
    python_exec = 'python'
    print('\n NOTE: python executable used is ', python_exec, '\n')
    print(' Please make sure it is CORRECT\n')

    # ====================================================================
    # execute the needed processes
    # ====================================================================

    # import simulation related modules according to design
    abs_path_test_bench_folder =  os.path.abspath('../designs/' + design_name + '/testbenches/' + design_name + '/')
    abs_path_model_folder = os.path.abspath('../designs/' + design_name + '/model')
    sys.path.append(abs_path_model_folder)
    sys.path.append(abs_path_test_bench_folder)
    tb_module = importlib.import_module(design_name + '_tb')

    # interpret terminal input testbench
    layer_path = os.path.abspath('../workloads/layer_shapes/' + layer_path_input) \
                 if len(layer_path_input.split(os.sep)) == 1 else os.path.abspath(layer_path_input)

    arch_path = os.path.abspath('../designs/' + design_name + '/arch_parameters/' + architecture_path_input) \
                if len(architecture_path_input.split(os.sep)) == 1 else os.path.abspath(architecture_path_input)

    mapping_path = os.path.abspath('../designs/' + design_name + '/mappings/' + mapping_path_input)\
                if len(mapping_path_input.split(os.sep)) == 1 else os.path.abspath(mapping_path_input)

    weights_data_path = os.path.abspath('../workloads/weights_data/' + weights_data_path_input)\
                      if len(weights_data_path_input.split(os.sep)) == 1 else os.path.abspath(weights_data_path_input)

    ifmap_data_path = os.path.abspath('../workloads/ifmap_data/' + ifmap_data_path_input)\
                      if len(ifmap_data_path_input.split(os.sep)) == 1 else os.path.abspath(ifmap_data_path_input)

    bias_data_path = os.path.abspath('../workloads/bias_data/' + bias_data_path_input)\
                     if len(bias_data_path_input.split(os.sep)) == 1 else os.path.abspath(bias_data_path_input)

    stats_path = os.path.abspath('../designs/' + design_name + '/stats/' + design_name + '/' +  stats_data_path_input)\
                 if len(stats_data_path_input.split(os.sep)) == 1 else os.path.abspath(stats_data_path_input)

    # run testbench
    tb_module.main(arch_path, layer_path, mapping_path, bias_data_path, weights_data_path , ifmap_data_path, stats_path)
    print('*** simulation finished ***')
    # navigate to estimation directory to perform energy estimation
    est_home_dir = os.path.normpath('../tools/estimator/' )
    os.chdir(est_home_dir)

    # setup the inputs for estimator
    in_stats_path = stats_path
    out_stats_path = stats_path
    glb_attr_path = os.path.normpath('../../designs/' + design_name + '/testbenches/' + design_name + '/global_attr.yaml')
    verbose_ERT_GEN = '0'
    verbose_CALC = '1'

    # invoke enegy estimator
    subprocess.call([python_exec, 'run.py', design_name, stats_path, stats_path, glb_attr_path, verbose_ERT_GEN, verbose_CALC])
