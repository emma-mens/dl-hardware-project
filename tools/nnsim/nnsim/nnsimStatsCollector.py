from datetime import datetime
import os
from yaml import load, dump
from nnsim.nnsimUtil import sim_dumper, create_folder
from copy import deepcopy



# each module has a stats collector associated with it
#    the stats collector is responsible for collecting all the stats related to this module

class nnsimStatsCollector():
    
    def __init__(self, module, stats_dir_path):
        
    
        self.class_spec = {}
    
        self.class_hierarchy = {}
        self.arch_spec = {}
        self.access_counts = {}
        
        # the architecture design object you are collecting data on
        self.module = module
        self.component_class_generated            = False
        self.architecture_specification_generated = False
    
        self.root_dir = stats_dir_path + '/'
        create_folder(self.root_dir)
        
    # =========================================================================
    #  Collects the the involved component class information
    # ========================================================================= 
    def collect_class_specification_stats(self):

        if not self.component_class_generated:
        
            file_path = os.path.normpath(self.root_dir + 'component_class_description.yaml')
            
            if os.path.isfile(file_path ):
                os.remove(file_path )
            out_file = open(file_path ,'a')
            out_file.write('\n# ==================================================\n')
            out_file.write('#\t component class description \n')    
            out_file.write('# ==================================================\n') 
            self.save_class_spec(self.module)               
            self.dump_class_spec(out_file)
            out_file.close()
            self.component_class_generated = True
            
            
    def save_class_spec(self, module):
        
        if not module.component_class_generated:
                # -----------------------------------------------------------
                # Record component class information (if not recorded already)
                # -----------------------------------------------------------             
                if module.class_name not in self.class_spec.keys():
                    # record only if the user wants to show it
                    if module.component_class_as_topclass == 'show':
                        class_spec = {}  
                        class_spec['attributes'] = module.attrs
                        if not module.predefined_class:
                            # a compound class should invovle user defined actions
                            class_spec['actions'] = module.actions
                        else:
                            if getattr(module, 'base_class_name', None) is not None:
                                class_spec['base_class_name'] = module.base_class_name
                        
                        # a compound class should have subclasses
                        if not len(module.sub_modules) == 0:
                            class_spec['sub_component_classes'] = {}
                            
                            for sub_module in module.sub_modules:
                                if sub_module.component_class_as_subclass == 'show':
                                    class_spec['sub_component_classes'][sub_module.class_name] = {'attributes': sub_module.attrs}
                                    if getattr(sub_module, 'base_class_name', None) is not None:
                                        class_spec['sub_component_classes'][sub_module.class_name]['base_class_name'] = sub_module.base_class_name
                            
                            # if none of the subcomponent classes need to be recorded, get rid of the field
                            if len(class_spec['sub_component_classes'].keys()) == 0:
                                class_spec.pop('sub_component_classes')
                                
                        self.class_spec[module.class_name] = deepcopy(class_spec) 
                    
                    # ---------------------------------------------------------
                    # Record component class specification for the submodules
                    # ---------------------------------------------------------
                    for sub_module in module.sub_modules:
                        self.save_class_spec(sub_module)
                        
                    # mark the component class information as generated                
                    module.component_class_generated = True
    
    def dump_class_spec(self, file):
        output = dump(self.class_spec, default_flow_style=False, Dumper = sim_dumper)
        file.write(output)
            
    # =========================================================================
    #  Describes the the involved architecture component descriptions
    # =========================================================================            
    def collect_architecture_specification_stats(self): 
        if not self.architecture_specification_generated:

            file_path = os.path.normpath(self.root_dir + 'architecture_description.yaml')
            
            if os.path.isfile(file_path ):
                os.remove(file_path )
            out_file = open(file_path ,'a')
            out_file.write('\n# ==================================================\n')
            out_file.write('#\t architecture description \n')    
            out_file.write('# ==================================================\n')             
           
            self.save_arch_spec(self.module) 
            self.summarize_arch_spec(self.module)              
            self.dump_arch_spec(out_file)
            out_file.close()  
            self.architecture_specification_generated = True
            
   
    #  COLLECT COMPONENTS SPEC STATS
    #            this information only needs to be collected once 
    #            for each architecture design

    def save_arch_spec(self, module):
        if module.architecture_specification_generated or not module.component_specification_stats == 'show':
            for sub_module in module.sub_modules:
                self.save_arch_spec(sub_module)
        else:

            if module.component_specification_stats == 'show' and module.component_with_action:
                module.comp_spec  = {'class': module.class_name}
            module.architecture_specification_generated = True
            
            for sub_module in module.sub_modules:
                sub_module.register_module_name()
                self.save_arch_spec(sub_module)
                sub_module.architecture_specification_generated = True
                if sub_module.component_specification_stats == 'show' and\
                   not len(sub_module.comp_spec) == 0:
                       module.comp_spec[sub_module.name] = deepcopy(sub_module.comp_spec) 
                            
    def summarize_arch_spec(self, module): 
        if module.component_specification_stats == 'show' and not len(module.comp_spec) == 0:
            self.arch_spec[module.name] = module.comp_spec
       
        else:
            for sub_module in module.sub_modules:
                sub_module.register_module_name()
                self.summarize_arch_spec(sub_module)        
        
    def dump_arch_spec(self, file):
        output = dump(self.arch_spec, default_flow_style=False, Dumper = sim_dumper) 
        file.write(output)            
            
            
    # ============================================================ 
    #
    #  ACCESS STATS NEEDS TO BE COLLECTED EVERY SINGLE RUN
    #
    # ============================================================  
    def collect_access_stats(self, file_name= 'access_description'):
        file_path = os.path.normpath(self.root_dir + file_name + '.yaml')
        
        if os.path.isfile(file_path ):
            os.remove(file_path )
        out_file = open(file_path ,'a')
        out_file.write('\n# ==================================================\n')
        out_file.write('#\t access counts \n')    
        out_file.write('# ==================================================\n')             
        self.finalize_access_stats(self.module)
        self.summarize_access_counts(self.module)
        self.dump_access_stats(out_file)
        

    def finalize_access_stats(self, module):

        if module.access_counts_generated or not module.access_counts_stats == 'show':  
            for sub_module in module.sub_modules:
                self.finalize_access_stats(sub_module)
        else:
            if module.customized_access:
                module.summerize_access_stats()
                
            for sub_module in module.sub_modules:
                
                sub_module.register_module_name()
                self.finalize_access_stats(sub_module)
                sub_module.access_counts_generated = True
                
                for key in sub_module.access_stats:
                    if sub_module.access_counts_stats != 'aggregate':
                        if sub_module.access_counts_stats == 'show':
                            module.access_stats[sub_module.name] = deepcopy(sub_module.access_stats) 
    
    def summarize_access_counts(self, module):
       
        if module.access_counts_stats == 'show':
            self.access_counts[module.name] = module.access_stats
       
        else:
            for sub_module in module.sub_modules:
                sub_module.register_module_name()
                self.summarize_access_counts(sub_module)
                
    
    def dump_access_stats(self, file):
        output = dump(self.access_counts, default_flow_style=False, Dumper = sim_dumper) 
        file.write(output) 

    # ============================================================ 
    #
    #  IO Traces Collection
    #
    # ============================================================                              
    def collect_io_traces(self):
        file_path = self.root_dir  
        if os.path.isfile(file_path ):
            os.remove(file_path )
        self.finalize_io_traces(self.module)
        
    def finalize_io_traces(self, module):
        if module.traces_generated or not module.traces_stats == 'show':  
            pass

        else:
            module.recorder.dump_records(self.root_dir)    
            self.traces_generated  = True
            
        for sub_module in module.sub_modules:
                self.finalize_io_traces(sub_module)


        

        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        





