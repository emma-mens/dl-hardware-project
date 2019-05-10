from copy import deepcopy
from yaml import load, dump
from estimator.utility import ee_loader, ee_dumper, write_yaml_file, remove_qoutes_yaml
from estimator.prebuilt_template import prebuilt_template_class

class energy_reference_generator(object):
    """ Generate an energy reference table for each component in the design
    
        output saved to: estimator/reference_tables/<design_name>/
        top_level.yaml aggregates all the energy estimation table
        class_namex.yaml: energy reference table for the specific class
        
        for each class, the energy table is in a list format, 
        for each item in the list, a set of fixed attributes are used, 
                                   energy if various operations are listed
   """
   
    def __init__(self):
        
        ''' initializes all bookkeeping containers '''
        
        self.component_class_description   = {}
        self.architecture_description      = {}
        self.top_level_classes             = set([])
        self.energy_reference_table        = {}
        self.unit_energy_reference_table   = {}
        self.top_level_yaml                = {}
        self.general_attrs                 = None
        
#   
    def generate_class_table(self, class_definition):
        
        ''' recursive function that generates energy 
        
        class_definition contains: 
            - class attributes
            - actions related class type 
                case0 - all actions (standalone toplevel prebuilt class)
                case1 - only a single action (subclass of a top level custom class)
            - actions' composition (if custom class type)
            - subclass definitions (if custom class type)
        '''

        # ---------------------------------------------------------------
        # Check class type
        # ---------------------------------------------------------------
        # check if the class is alreay a prbuilt class
        is_defualt_prebuilt_class = class_definition['component_class_name'] in self.prebuilt_classes
        # check if the class is some parametrized version of the prebuilt class with different class names
        #  (useful if you have multiple top level instances of the same prebuilt class type but diff params)
        is_redefined_prebuilt_class = 'base_class_name' in class_definition
        
        # --------------------------------------------------------------------------------------------
        # Directly call energy estimators if the class is a paramtrized version of a prebuilt class
        # --------------------------------------------------------------------------------------------
        if is_defualt_prebuilt_class or is_redefined_prebuilt_class:
            
            class_name    = class_definition['component_class_name'] \
                            if is_defualt_prebuilt_class \
                            else class_definition['base_class_name']
                            
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
                        
        # ---------------------------------------------------------------------------------------------------
        # Recursivly parse the compount component class type to arrive at the underlying prebuilt classes
        # ---------------------------------------------------------------------------------------------------      
        else:
            # custom component class parsing
            #   custom component class must have subcomponent classes
            #   custom component class must be define one an only one time
            energy_table = {}
           
            # understand the meaning of the customly defined actions of the class
            for action, action_def in class_definition['actions'].items():
                # =====================================================
                # Parametrized Actions
                # =====================================================
                if False:
                    # all the parameterized actions remain unchanged, run time recalculation is needed
                    energy_table[action] = action_def
                # =====================================================
                # Non-parametrized Compound Actions
                # =====================================================
                else:
                    energy_table[action] = {'numerical_energy': 0, 'base_class_actions':{}}
#                    print(action_def)
                    for subclass_name, subclass_action in action_def['subcomponent_class_actions'].items():
                        # ----------------------------------------------------
                        # Constrcut a basic sbuclass_definition dictionary 
                        # ----------------------------------------------------
                        subclass_definition = deepcopy(class_definition\
                                                       ['sub_component_classes']\
                                                       [subclass_name])
                        subclass_definition['actions'] = subclass_action
                        subclass_definition['component_class_name'] = subclass_name
                        subaction_name = subclass_action['action_name']
                      
                        # transfer the specified parameter values (if any)
                        #   from parent class to sub class
                        for p, binding in subclass_definition['attributes'].items():
                            if binding in class_definition['attributes'].keys():
                                subclass_definition['attributes'][p] =\
                                class_definition['attributes'][binding]
                                
                        # ----------------------------------------------------------------
                        # Determine if additional information needs to added the dictionary
                        # ----------------------------------------------------------------    
                        # if the sub component class is custom type,\
                        #     find its subcomponent classes from the database
                        if not subclass_name in self.prebuilt_classes and 'base_class_name' not in subclass_definition:
                            
                            # retrivie the information related to the subclass from the user input component class information
                            subclass_record = self.component_class_description[subclass_name]
                            
                            if not 'base_class_name' in subclass_record:
                                # if the subclass is a normal compound class
                                #     - add its sub_component_class key to its definition by retriving from the provided component class info
    #                                print(subclass_name, ':', subclass_record)
                                subclass_definition['sub_component_classes'] = deepcopy(subclass_record['sub_component_classes'])
                                
                                #     - add the defintion for the action that will be used to calculate energy consumption of the top level class
                                subclass_definition['actions'] = {subaction_name: deepcopy(subclass_record['actions'][subaction_name])}
                           
                            else:
                                # if the subclass is a direct instantiation of a prebuilt class with specified attributes
                                subclass_definition['base_class_name'] = deepcopy(subclass_record['base_class_name'])
    
                        # ----------------------------------------------------------
                        # Accumulate energy value for this specific action
                        # ----------------------------------------------------------
                        
                        # check if the energy table for a specific class (for the same set of attributes values) is generated
                        # return None if not found 
                        
                        class_name_to_check = subclass_name if 'base_class_name' not in subclass_definition \
                                                            else subclass_definition['base_class_name']
                        generated_table = None
                        if type(subclass_action['repeat']) is int:
                            generated_table = self.exist_generated_table(class_name_to_check, \
                                                                         subclass_definition['attributes'],\
                                                                         subclass_action['action_name'])
                            
                        if generated_table is None:
                            # generate a fresh energy reference table for this specific setting
                            # record the calculated energy values 
                            sub_energy_table = self.generate_class_table(subclass_definition)[subaction_name] 
                        else:
                            sub_energy_table = generated_table
                            
                        # ---------------------------------------------------------------
                        # if no actions with arguments in this subclass is used
                        # ---------------------------------------------------------------
                        if 'numerical_energy' in sub_energy_table and type(subclass_action['repeat']) is int :
                            energy_table[action]['numerical_energy'] += sub_energy_table['numerical_energy']*subclass_action['repeat']
                        # ---------------------------------------------------------------
                        # if actions with arguments in this subclass is used
                        # ---------------------------------------------------------------                                                                         *int(subclass_action['repeat'])
                        if 'base_class_actions' in sub_energy_table:
                            for base_class_name, base_class_info in sub_energy_table['base_class_actions'].items():
                                if  base_class_name not in energy_table[action]['base_class_actions']:
                                    energy_table[action]['base_class_actions'][base_class_name] = []
                                for related_actions in base_class_info:
                                    energy_table[action]['base_class_actions'][base_class_name].append(related_actions)
        # ---------------------------------------------------------- 
        # Record the newly generated energy table 
        # ---------------------------------------------------------- 
#        self.record_unit_energy_reference_table(class_definition, energy_table)
        self.record_energy_reference_table(class_definition, energy_table)
        return energy_table
    
    # ---------------------------------------------------------------------------
    # Utility: check if the same energy table has been generated
    # ---------------------------------------------------------------------------    
    def exist_generated_table(self, class_name, class_params, class_action):
        
        ''' test to see if the energy reference table has been generated
        
               - class_name : component class name
               - class_params: the set of params used to characterize the class
               - class_action: the action that we need energy value for
        '''
        if not class_name in self.energy_reference_table.keys():
            return None
        else:
            record_entry = self.energy_reference_table[class_name]
            for idx in range(len(record_entry)):
                recorded_params = record_entry[idx]['attributes']
                if recorded_params == class_params:
                    if class_action in record_entry[idx].keys():
                        return record_entry[idx][class_action]
        return None
    # ------------------------------------------------------------------------
    # record the newly generated energy tables
    # ------------------------------------------------------------------------
    def record_energy_reference_table(self, class_definition, energy_table):
        
        class_name = class_definition['component_class_name']
        attributes = deepcopy(class_definition['attributes'])
        # -----------------------------------------------------------------
        # Save the base class's information
        # -----------------------------------------------------------------
        if 'base_class_name' in class_definition:
            base_class_name = class_definition['base_class_name']
            if base_class_name in self.energy_reference_table.keys():
                record_entry = self.energy_reference_table[base_class_name]
                for idx in range(len(record_entry)):
                    # if attributes are also the same => add a new action
                    if attributes == record_entry[idx]['attributes']:
                        for action_name in energy_table.keys():
                            if not action_name in record_entry[idx].keys():
                               record_entry[idx][action_name] = deepcopy(energy_table[action_name])
                               
                    # if the exsiting record is for another set of attributes => add a new node
                    else:
                        energy_table['attributes'] = deepcopy(attributes)
                        record_entry.append(energy_table)
                
            # if there is no relevent entry for the class    
            else:
                self.energy_reference_table[base_class_name] = []
                energy_table['attributes'] = deepcopy(attributes)
                self.energy_reference_table[base_class_name].append(energy_table)  
            
        # -----------------------------------------------------------------
        # Save the actual class's information
        # -----------------------------------------------------------------            
        # if there is relevent entry for the class
        if class_name in self.energy_reference_table.keys():
            
            record_entry = self.energy_reference_table[class_name]
            for idx in range(len(record_entry)):
                # if attributes are also the same => add a new action
                if attributes == record_entry[idx]['attributes']:
                    for action_name in energy_table.keys():
                        if not action_name in record_entry[idx].keys():
                           record_entry[idx][action_name] = deepcopy(energy_table[action_name])
                           
                # if the exsiting record is for another set of attributes => add a new node
                else:
                    energy_table['attributes'] = deepcopy(attributes)
                    record_entry.append(energy_table)
                
        # if there is no relevent entry for the class    
        else:
            self.energy_reference_table[class_name] = []
            energy_table['attributes'] = deepcopy(attributes)
            self.energy_reference_table[class_name].append(energy_table) 
            
    # -------------------------------------------------------------------------        
    # integrate the commonly used attrs (if any) into the class definition 
    # -------------------------------------------------------------------------
    def format_class_definition(self, class_definition):

        '''  flatten the attributes field of each class definition 
             override global parameter values using the user defined values (if exist)
             distribute shared actions (if exist)
             recursively flatten the subsequent subclass defitions (if exist)
        '''
        if 'attributes' in class_definition.keys():
            cattrs = class_definition['attributes']
            
            # apply overiding and copying of the default parameter values
            # 1. the global field that is specified in each component class
            if 'global' in cattrs.keys():
                for param, default_val in cattrs['global'].items():
                    if not param in cattrs.keys():
                        class_definition['attributes'][param] = deepcopy(default_val)
                # remove the default options after copying is done
                cattrs.pop('global')       
                 
            # 2. the general attributes that are applicable to all of the components           
            if self.general_attrs is not None:
                for attr_name, general_value in self.general_attrs.items():
                    if not attr_name in cattrs.keys():
                        class_definition['attributes'][attr_name] = deepcopy(general_value)               

        if 'sub_component_classes' in class_definition.keys():
            for name, subclass in class_definition['sub_component_classes'].items():
                subclass = deepcopy(self.format_class_definition(subclass))
                subclass['component_class_name'] = name
                class_definition['sub_component_classes'][name] = subclass
                
        if 'actions' in class_definition.keys():
            if 'shared' in class_definition['actions'].keys():
                shared_actions = class_definition['actions']['shared']
                for action, action_def in class_definition['actions'].items():
                    if action != 'shared':
                        if 'shared' not in action_def[-1].keys():
                            action_def += [ action for action in shared_actions]
                        else:
                            if not action_def[-1]['shared']== 'none':
                                action_def += [action for action in action_def[-1]['shared']]
                            class_definition['actions'][action] = class_definition['actions'][action][:-1]
                class_definition['actions'].pop('shared')
                

        return class_definition  
     
    # -------------------------------------------------------------------------
    # processes the hierarchical representation and save the processed results
    # -------------------------------------------------------------------------
    def save_architecture_description(self, output_path):
        
        ''' properly expands the list components (if exists),
            redefine the component names in terms of hierarchy and 
            save the processed description'''
        
        for base_component_name, component_description in self.raw_architecture_description.items():
            if 'count' in component_description.keys():
                # this is a list of component condensed into one description => expand
                count = component_description['count']
                component_description.pop('count')
                for c in range(count):
                    prefix = self.design_name + '.' + base_component_name + '[' + str(c) + ']'
                    self.flatten_architecture_description(prefix, component_description)
            else:
                prefix = self.design_name + '.'  + base_component_name
                if 'class' in component_description:
                    full_name = prefix
                    self.architecture_description[full_name] = component_description['class']
                    self.top_level_classes.add(component_description['class'])
                else:  
                    self.flatten_architecture_description(prefix, component_description)
        
        file_path = output_path + '/parsed_arch_descriptions/' + self.design_name + '.yaml'
        write_yaml_file(file_path, self.architecture_description)                  
   
    def flatten_architecture_description(self, prefix, component_description):
        
        # where there are at least two levels of hierarchy
        for subcomponent_name, subcomponent_description in component_description.items():
            if 'class' in subcomponent_description:
                full_name = prefix + '.' + subcomponent_name
                self.architecture_description[full_name] = subcomponent_description['class']
                self.top_level_classes.add(subcomponent_description['class'])
            else:
                prefix = prefix + '.' + subcomponent_name
                self.flatten_architecture_description(prefix, subcomponent_description)   
    # ===============================================================================================  

              
    def generate_table(self, output_path):
        
        ''' generate energy reference tables for component classes that are top level in the architecture'''
        
        # step1: generate energy reference tables for te top level component classes
        for component_name, classname in self.architecture_description.items(): 
            
            if classname in self.component_class_description:
                class_definition = self.component_class_description[classname]
                if classname not in self.energy_reference_table:
                    self.generate_class_table(class_definition)
                
        # step 2: record the generated energy reference table for top level classes
        for classname in self.top_level_classes:
            if classname in self.energy_reference_table:
                # write separate energy reference tables
                #    just for the users to have a better view of the energy reference tables
                file_path = output_path + '/reference_tables/' + self.design_name + '/'+ classname + '.yaml'  
                # top level class must have a unique set of parameter values
                write_yaml_file(file_path, self.energy_reference_table[classname][0])
                
                include_file_path = "!include " + classname + ".yaml"
                
                self.top_level_yaml[classname] = include_file_path


        
    def fire(self, info):
        
        ''' main function to start the energy reference generator
        
        parses the input files
        produces the energy reference tables for all the top level classes as well as the embeded prebuilt classes
        '''

        # ------------------------------------------------------------------------------
        # Load in the design specfication and extract bookkeeping variables
        # ------------------------------------------------------------------------------
        self.component_class_description     = load(open(info['input_path']+ '/component_class_description.yaml'), ee_loader)
        self.raw_architecture_description    = load(open(info['input_path'] + '/architecture_description.yaml'), ee_loader)
        self.design_name                     = info['design_name']
        self.prebuilt_classes                = load(open('estimator/component_class_prebuilt_lib/lib.yaml'))
       
        # ------------------------------------------------------------------------------
        # Parse the architecture description provided as input
        # ------------------------------------------------------------------------------        
        self.save_architecture_description(info['output_path'])
        
        # ------------------------------------------------------------------------------
        # Format class definition
        # ------------------------------------------------------------------------------
        global_attrs_path = info['global_attr_file']
        self.general_attrs = load(open(global_attrs_path), ee_loader)
        for classname, class_definition in self.component_class_description.items():
            
            class_definition = self.format_class_definition(class_definition)
            class_definition['component_class_name'] = classname        
        
        # ------------------------------------------------------------------------------
        # Generate Energy Reference Tables for the compound classes
        # ------------------------------------------------------------------------------
        self.generate_table(info['output_path'])
        
        if info['verbose']:    
            print('\nTOP LEVEL ENERGY REFERENCE TABLE \n')
            table_yaml = dump(self.energy_reference_table, Dumper = ee_dumper,\
                                                    default_flow_style = False)
            print(table_yaml)
        # ------------------------------------------------------------------------------
        # Summarize all the sparate energy yaml files in one file using include keyword
        # ------------------------------------------------------------------------------        
        file_path = info['output_path'] + '/reference_tables/' + self.design_name + '/' + 'top_level.yaml'
        write_yaml_file(file_path, self.top_level_yaml)  
        remove_qoutes_yaml(file_path)
        

        
     