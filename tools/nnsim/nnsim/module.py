from yaml import load, dump
from nnsim.nnsimStatsCollector import nnsimStatsCollector 

# Module object

class_dictionary = {}

class HWError(Exception):
    pass

class Module(object):
    def __init__(self, *args, **kwargs):
        self.name = str(id(self))
        self.predefined_class = False
        self.class_name = ''
        self.clk_gated = False
        self.path = ''
        self.sub_modules = []
        self.instantiation_done = False
        
        # -------------------------------------------------------------------
        # Default Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_specification_stats         = 'hide'
        self.component_with_action                 =  False
        self.component_class_as_subclass           = 'hide'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'hide'  # whether to show the class_information as a top level class
        self.access_counts_stats                   = 'hide'
        self.traces_stats                          = 'hide'
        self.traces_generated                      = False
        self.customized_access                     = False
                
        # -------------------------------------------------------------------
        # Bookkeeping data structures for stats and test vector collection
        # -------------------------------------------------------------------
        self.component_class_generated             = False
        self.architecture_specification_generated  = False
        self.access_counts_generated               = False
        
        self.attrs                                 = {}
        self.actions                               = {}
        self.comp_spec                             = {}
        
        self.access_stats                          = {}
        
        # -------------------------------------------------------------------
        # Instantiate Customized Instances
        # -------------------------------------------------------------------
        # an arbitrary number of positional arguments and keyword arguments can be provided
        self.instantiate(*args, **kwargs)
        self.register_modules()
        self.instantiation_done= True
                
    def setup(self):
        pass

    def __setup__(self, path=''):
        self.setup()
        self.path = "%s/%s" % (path, self.name)
        for sub_module in self.sub_modules:
            sub_module.__setup__(self.path)

    def instantiate(self):
        raise HWError("Cannot instantiate abstract module")

    def getsize(self):
        return (1,)


    # if the stat type is aggregate, we just add the values in the raw stats dictionary 
    # we do not show the submodule's data as a separate entity
    # if the parent module has the specific key for a type of stat, then each submodule's own value for the specific key is added
    def finalize_access_stats(self):
        self.final_access_stats = {}
        self.final_access_stats = self.raw_access_stats
        self.sub_modules = []
        self.register_modules()
#        print('------- Register for', self.name)
        for sub_module in self.sub_modules:
            sub_module.finalize_access_stats()
            for key in sub_module.final_access_stats:
                self.final_access_stats[sub_module.name] = sub_module.final_access_stats
#        print('------- Registion finished', self.name)            
                    


# we only dump data for the modules that are labeled "show"
    def dump_access_stats(self, filename):
        if self.stat_type == 'show':
            output = dump({self.name: self.final_access_stats}, default_flow_style=False)
#            print({self.name: self.final_access_stats})
            filename.write(output)
        for sub_module in self.sub_modules:
            sub_module.dump_access_stats(filename)

    def register_modules(self):
        for key, attr in vars(self).items():
            attr = vars(self)[key]
            if issubclass(type(attr), Module):
                attr.name = key
                self.sub_modules.append(attr)
            elif issubclass(type(attr), ModuleList):
                self.sub_modules += attr.register(key)

    def register_module_name(self):
        for key, attr in vars(self).items():
            attr = vars(self)[key]
            if issubclass(type(attr), Module):
                attr.name = key
            elif issubclass(type(attr), ModuleList):
                attr.register(key)

                

    def tick(self):
        pass

    def reset(self):
        pass

    def __tick__(self):
        if hasattr(self, 'clk_gated'):
            if self.clk_gated:
                return
        self.tick()
        for sub_module in self.sub_modules:
            sub_module.__tick__()

    def __ntick__(self):
        for sub_module in self.sub_modules:
            sub_module.__ntick__()

    def __reset__(self):
        self.reset()
        for sub_module in self.sub_modules:
            sub_module.__reset__()

class ModuleList(object):
    def __init__(self, lst = []):
        
        if lst == []:
            self.list = []
        else:
            # easier way to instantiate a priorly known modlelist setup
            self.list =[]
            self.append(lst)
        

    def append(self, m):
        if issubclass(type(m), Module) or issubclass(type(m), ModuleList) or m is None:
            self.list.append(m)
        else:
            raise HWError("Can only append Module or ModuleList")

    def get_len(self):
        return len(self.list)
    
    def getsize(self):
        dim = (self.get_len(),)
        if issubclass(type(self.list[0]), ModuleList):
            dim += self.list[0].getsize()
        else:
            return dim
        return dim

    def __getitem__(self, key):
        return self.list[key]


    def register(self, list_name): #flatten the nested module list
        curr_dim_idx = 0
        module_list = []
        for m in self.list:
            # represent (nested) modulelist as arrays with multiple dimensions
            if issubclass(type(m), Module) or issubclass(type(m), ModuleList):
               m.name = list_name + '[' + str(curr_dim_idx) + ']'
               curr_dim_idx += 1
               
            if issubclass(type(m), Module):
                module_list.append(m)
                                
            elif issubclass(type(m), ModuleList):
                
                module_list += m.register(m.name)
                
        return module_list

    # utitility functions for the NoC to use to match dimension
    def flatten(self, flattened):
       for idx in range(self.get_len()):
           if issubclass(type(self.list[idx]), Module):
              flattened.append(self.list[idx])
           else:
               flattened = self.list[idx].flatten(flattened )

       return flattened

    def reshape(self, shape):

        flattened = ModuleList()
        flattened = self.flatten(flattened)
        
        # if the shape needed is a linear moduleList
        if shape[0] == 1:
            return flattened
        
        new_data = ModuleList()
        for i in range(len(shape)):
            new_data.append(ModuleList())
#        print('the length of the flattened modulelist is: ', flattened.getlen())
        i = 0                    # the idx for the flattened modulelist  
        for dim in range(len(shape)):
            j = 0                # the idx for the specific dim
            l = shape[dim]       # the number of data needed for the specific dim
    #        print('dim: ', dim, 'l: ', l)        
            while(j < l ):
    #            print('j: ', j)
                if i >= flattened.getlen():
                    raise HWError('the shape is not legal')
                    
                new_data[dim].append(flattened[i])
                j+= 1
                i+= 1
        
        return new_data