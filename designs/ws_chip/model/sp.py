from nnsim.nnsimSmartBuffer import nnsimSmartBuffer
#from nnsim.nnsimRecorder    import nnsimRecorder
from weights_sp_ags         import WeightsSpFillAG, WeightsSpDrainAG
from copy                   import deepcopy

class WeightsSP(nnsimSmartBuffer):

    def instantiate(self, setup):
        setup['LMs']     = [{'AGs':{'drain': WeightsSpDrainAG, 'fill': WeightsSpFillAG}}]
        nnsimSmartBuffer.instantiate(self, setup)              
        self.class_name  = 'WeightsSP' 

        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
    
    def configure(self, config):
        config['LM'][0]['AGs'] = deepcopy(config['shape_mapping_info'])
        nnsimSmartBuffer.configure(self, config)
        
     
        
