# -*- coding: utf-8 -*-
from yaml import load, dump
from copy import deepcopy
from estimator.utility import ee_loader, ee_dumper, write_yaml_file
from estimator.prebuilt_template import prebuilt_template_class

class energy_calculator(object):
    def __init__(self):
        self.architecture_description = {}
        self.access_description       = {}
        self.energy_estimation_table  = {}
        self.access_counts            = {}

    def flatten_access_description(self, prefix, access_info):
    # each element in the list is a dictionary that has:
    # 1. access_name
    # 2. access_count
    # 3. access_attributes (if any)      

       for key, value in access_info.items():
            if type(value) is list:
                for attr_set_idx in range(len(value)):
                    attr_set = value[attr_set_idx]
                    if 'count' not in attr_set.keys():
                        sub_prefix = prefix + '.' + key 
                        self.flatten_access_description(sub_prefix, attr_set)
                    else:
                        # key is the access name, value is the access count + access  attributes (if applicable)
                        if prefix not in self.access_description:
                            self.access_description[prefix] = []
                        new_access_info = attr_set.copy()
                        new_access_info.update({'access_name': key})
                        self.access_description[prefix].append(new_access_info)
           
            elif type(value) is dict:
                if 'count' not in value:
                    sub_prefix = prefix + '.' + key
                    self.flatten_access_description(sub_prefix, value)
                else:
                    if prefix not in self.access_description:
                        self.access_description[prefix] = []
                    new_access_info = value.copy()
                    new_access_info.update({'access_name': key})
                    self.access_description[prefix].append(new_access_info)
                    
                        
    def parse_access_description(self, raw_access_description):
        ''' parse the access counts input 
              - flatten the list type objects  
              - parsed value stored in self.access_counts
        '''
#        access_counts = self.access_description['access_counts']['component_access']
        for name, access_info in raw_access_description.items():
            # if the design name is not used as a prefix
            if len(name) < len(self.design_name)\
                or (not ((self.design_name == name[0:len(self.design_name)] or name[len(self.design_name)] == '.'))):
                    name = self.design_name + '.' + name
            # check if the access counts are sent in hierarchical form
            # if so, flatten
            self.flatten_access_description(name, access_info)

    def query_estimation_engine(self, class_definition):
        
        class_name  = class_definition['base_class_name'] \

                        
        prebuilt_class_path = 'estimator/component_class_prebuilt_lib/' + class_name + '.yaml'
        prebuilt_obj = prebuilt_template_class(prebuilt_class_path)
        prebuilt_obj.configure(class_definition['attributes'])
        
        vendor        = class_definition['attributes']['vendor']
        technology    = class_definition['attributes']['technology']
        voltage       = class_definition['attributes']['voltage']
        
        etimation_model_info = {'vendor': str(vendor), 'technology': str(technology), 'voltage': str(voltage)}
        
        if not 'actions' in class_definition:
            energy_table = prebuilt_obj.generate_energy_reference_table(etimation_model_info)
            
        else:
            energy_table = prebuilt_obj.generate_energy_reference_table\
                    (etimation_model_info, actions = [class_definition['actions']])
        return energy_table
 
    def process_parameterized_action(self, base_class_name, base_class_action, component_energy_table, access_info):
    #  AddressGenerator:
    #    - base_action_name: generate
    #      repeat: ndrain
    #      parameters:
    #      count_max: 12 
        
        base_action_name = base_class_action['base_action_name']
        # construct defined defintion of current action according to template
        actual_action = {}
        actual_action.update(base_class_action.copy())
        
        if type(actual_action['repeat']) is not int:
            # if number of repeat times is inkonwn
            if type(actual_action['repeat']) is not dict:
                # number of repeats is derived from a single operation
                processed_repeat = access_info['arguments'][actual_action['repeat']]
            else:
                # number of repeats needs some computational operation
                processed_repeat = 0
                for op_type, oprands in actual_action['repeat'].items():
                    if op_type == 'sum':
                        # the operation on the arguments is sum
                        for op in oprands:
                            int_val = access_info['arguments'][op] if type(op) is not int else op
                            processed_repeat += int_val
                    else:
                        raise Exception('unexpected processing type of repeat')
                            
                        
            actual_action['repeat'] = processed_repeat
        
        actual_energy = 0
        
        if 'numerical_energy' in base_class_action:
            actual_energy += base_class_action['numerical_energy'] * actual_action['repeat']
            
        
        if 'arguments' in actual_action:
            actual_action['evaled_arguments'] = []
            for arg in actual_action['arguments']:
                if type(arg) is str:
                    arg = access_info['arguments'][arg]
                elif type(arg) is dict:
                    processed_arg = 0
                    for op_type, oprands in arg.items():
                        if op_type == 'sum':
                            for op in oprands:
                                op = access_info['arguments'][op] if type(op) is str else op
                                processed_arg += op
                        else:
                            raise Exception('unexpected processing type of arguments')
                    arg = processed_arg
                                
                actual_action['evaled_arguments'].append(arg)
        
            all_attrs = {}
            general_component_attrs = component_energy_table['attributes'] 
            all_attrs.update(general_component_attrs.copy())
            all_attrs.update(base_class_action['attributes'])
            class_definition = {'base_class_name': base_class_name, 'attributes': all_attrs, 'actions':{'action_name':base_action_name, 'repeat': actual_action['repeat']} }     
            
            if 'evaled_arguments' in actual_action:
                class_definition['actions']['evaled_arguments'] = actual_action['evaled_arguments']
            
            energy_table = self.query_estimation_engine(class_definition)
            actual_energy += energy_table[base_action_name]['numerical_energy'] * actual_action['repeat']
        
        return actual_energy

    
    def generate_estimation(self, output_path):
        
        self.design_energy_reference_table = \
                            load(open(output_path + '/reference_tables/' \
                            + self.design_name + '/' \
                            + 'top_level.yaml'), ee_loader)
        total_energy = 0     
        for component_name, all_accesses in self.access_description.items():
            accumulate = 0
            component_class = self.architecture_description[component_name]
            component_energy_table = self.design_energy_reference_table[component_class]
            for access_info in all_accesses:
                if not len(access_info) == 0:
                    access_accumulate = 0
                    access_energy_table = component_energy_table[access_info['access_name']]
                    if 'base_class_actions' in access_energy_table:
                        for base_class_name, related_base_action_lst in access_energy_table['base_class_actions'].items():
                            for related_base_action in related_base_action_lst:
                                calculated_energy = self.process_parameterized_action(base_class_name, related_base_action,component_energy_table, access_info)
                                access_accumulate += calculated_energy
                    # overall numerical energy, the number that can be generated during generation of ERTs, repeat is already counted
                    if 'numerical_energy' in access_energy_table:
                        access_accumulate += access_energy_table['numerical_energy']
                    access_accumulate = access_accumulate * access_info['count']
                    accumulate = accumulate + access_accumulate
            
            self.energy_estimation_table[component_name] = round(accumulate,2) 

            total_energy += accumulate
        self.energy_estimation_table['total'] = total_energy
            
                    
    def fire(self, info):
        # load and parse access counts
        access_description_path       = info['input_path'] +  '/access_description.yaml' 
        self.design_name              = info['design_name']
        self.raw_access_description   = load(open(access_description_path), ee_loader)
        self.parse_access_description(self.raw_access_description )
        # load processed architecture description (processed during energy table generation)
        architecture_description_path  = info['output_path'] + '/parsed_arch_descriptions/' + self.design_name + '.yaml'
        self.architecture_description = load(open(architecture_description_path), ee_loader)
        
        # claculate energy estimations according to saved energy reference tables
        self.generate_estimation(info['output_path'])

        # save results
        file_path = info['output_path'] + '/final_estimations/' + self.design_name + '.yaml'
        write_yaml_file(file_path, self.energy_estimation_table)             
            
        if info['verbose']:    
            print('\nTOP LEVEL ENERGY ESTIMATION TABLE \n')
            table_yaml = dump(self.energy_estimation_table, Dumper = ee_dumper,\
                                                    default_flow_style = False)
            print(table_yaml)            
            
            
