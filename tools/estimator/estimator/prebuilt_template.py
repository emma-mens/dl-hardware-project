# -*- coding: utf-8 -*-
import importlib,os
from yaml import load, dump
from estimator.utility import ee_loader, ee_dumper


class error(BaseException):
   def __init__(self, msg):
        print(msg)


class prebuilt_template_class():
    
    def __init__(self, yaml_template_path):
        
        self.yaml_template  = load(open(yaml_template_path), ee_loader)
        self.class_name     = self.yaml_template['component_class_name']
        self.actions        = self.yaml_template['actions']
        self.attributes     = self.yaml_template['attributes']
        self.action_arguments = None if 'action_arguments' not in self.yaml_template\
                                      else self.yaml_template['action_arguments']
        
        self.energy_reference_table = None
        self.ee_engine              = None
        
    def configure(self, params):
       for key in self.attributes.keys():
#           if key not in params:
#               print('WARN: ', key, ': value not found in the provided copmonent class definition for class', self.class_name)
#               print( self.attributes[key] ,' is used as default')
           
#           else:
           if key in params:
               self.attributes[key] = params[key]
       
    
    def generate_energy_reference_table(self, estimation_model_info, actions = 'all'):
        
        self.vendor     = estimation_model_info['vendor']
        self.technology = estimation_model_info['technology']
        self.voltage    = estimation_model_info['voltage']
        self.estimator_base_dir = self.vendor + '.' + self.technology + '.' + self.voltage
        
        self.energy_reference_table = self.fire_engine(actions)
        
        return self.energy_reference_table
   
    def fire_engine(self, actions):
        
        ''' send command via the global interface to the external engines
        
        two modes:
            default: get a table with all the actions and corresponding energy
            mode1: get an energy value for a specific action requested
            
        '''
        
        
        if actions == 'all':
            
            action_list = []
            for i in range(len(self.actions)):
                action_list.append({'action_name': self.actions[i]})
            ee_interface  = {'attributes': self.attributes, 'actions': action_list}
        else:
            ee_interface = {'attributes': self.attributes, 'actions': actions}
        
#        print('fired external energy estimation engine for ', self.class_name)
#        print('energy_estimation_interface:\n', ee_interface_yaml)

        
        energy_reference_table = {}
        for action_idx in range(len(ee_interface['actions'])):
            curr_action = ee_interface['actions'][action_idx]
            action_name = curr_action['action_name']
            
#            process = subprocess.Popen(\
#                                ['./custom_estimation/' \
#                                 + ESTIMATION_ENGINE_BASE_DIR_NAME + '/' \
#                                 + self.class_name + '.py'],\
#                                 stdin = subprocess.PIPE, \
#                                 stdout = subprocess.PIPE, \
#                                 stderr = subprocess.PIPE, \
#                                 bufsize = -1)
            estimation_engine_path =  'plug_in.' \
                                      + self.estimator_base_dir + '.' \
                                      + self.class_name
            
            engine = importlib.import_module(estimation_engine_path)
            
            
#            energy_str = subprocess.check_output(['python', 
#                                               './custom_estimation/' \
#                                                + ESTIMATION_ENGINE_BASE_DIR_NAME + '/' \
#                                                + self.class_name + '.py'],\
#                                                input = str.encode(ee_interface_yaml))\
#                                               .decode()
            # ---------------------------------------------------------------------------------
            # Nonparametreized actions or Parameterized actions with evaled attributes
            # ---------------------------------------------------------------------------------
            if 'arguments' not in curr_action or 'evaled_arguments' in curr_action:
                
                engine_input = {'attributes': ee_interface['attributes'], 'action_name': action_name}
                
                if 'evaled_arguments' in curr_action and self.action_arguments is not None:
                    evaled_arguments = {}
                    for idx in range(len(self.action_arguments[action_name])):
                        arg_name = self.action_arguments[action_name][idx]
                        arg_value = curr_action['evaled_arguments'][idx]
                        evaled_arguments[arg_name] = arg_value
                    engine_input['arguments'] = evaled_arguments.copy()
                numerical_energy = engine.calculate(engine_input)
                
                # if you know how many times it repeats, a numerical value can be directly produced
                if ('repeat' in curr_action and type(curr_action['repeat']) is int) or 'repeat' not  in curr_action:
                    energy_reference_table[action_name] = {'numerical_energy': numerical_energy} 
               
                # otherwise, no exact numerical information is outputted
                else:
                    energy_reference_table[action_name] = {'base_class_actions':\
                                                           {self.class_name:[\
                                                           {'base_action_name': action_name,\
                                                            'attributes': self.attributes,\
                                                            'numerical_energy': numerical_energy,\
                                                            'repeat': curr_action['repeat']}]}}
            # ---------------------------------------------------------------------------------
            # Parameterized actions with abstract attributes
            # ---------------------------------------------------------------------------------           
            else:
                energy_reference_table[action_name] = {'base_class_actions':\
                                                       {self.class_name: [{'base_action_name': action_name,\
                                                        'attributes': self.attributes,\
                                                        'arguments': ee_interface['actions'][action_idx]['arguments'],\
                                                        'repeat': curr_action['repeat']}]}}
        
        return energy_reference_table 
            
        
           
        
         
