# -*- coding: utf-8 -*-
from estimator.energy_reference_generator import energy_reference_generator
from estimator.energy_calculator import energy_calculator
import sys

#def main(design_name, input_path, global_attr_file, output_folder, verbose = False):
def main(info_dict):

    ERT_GEN_info = { 'design_name': info_dict['design_name'],\
                     'input_path': info_dict['input_path'],\
                     'output_path': info_dict['output_path'],\
                     'global_attr_file': info_dict['global_attr_file'],\
                     'verbose': info_dict['verbose_ERT_GEN']}
    ERT_GEN = energy_reference_generator()
    ERT_GEN.fire(ERT_GEN_info)


    CALC_info    = { 'design_name': info_dict['design_name'],\
                     'input_path': info_dict['input_path'],\
                     'output_path': info_dict['output_path'],\
                     'verbose': info_dict['verbose_CALC']}
    CALC = energy_calculator()
    CALC.fire(CALC_info)
    
    
if __name__ == '__main__':
    design_name = sys.argv[1]
    in_stats_path = sys.argv[2]
    out_stats_path = sys.argv[3]
    glb_attr_path = sys.argv[4]
    verbose_ERT_GEN = int(sys.argv[5])
    verbose_CALC = int(sys.argv[6])
    
    info_dict = {'design_name': design_name,\
                 'input_path': in_stats_path,\
                 'output_path': out_stats_path,\
                 'global_attr_file': glb_attr_path,\
                 'verbose_ERT_GEN': verbose_ERT_GEN,\
                 'verbose_CALC': verbose_CALC}    
    main(info_dict)

    
    