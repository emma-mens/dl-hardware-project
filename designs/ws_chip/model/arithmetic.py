# -*- coding: utf-8 -*-

from nnsim.nnsimArithmetic import nnsimMac, nnsimNZeroComp

class mac(nnsimMac):
    def instantiate(self, setup):
        
        nnsimMac.instantiate(self, setup)
       #======================================================================
        #                  Stats Collection Info
        #====================================================================== 
        self.class_name              = 'mac' 
        self.predefined_class        = True
        self.base_class_name         = 'MAC'
        
        self.attrs['out_data_width'] = 8
        self.attrs['data_width']     = 16
        
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_as_subclass        = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass        = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats      = 'show'
        self.access_counts_stats                = 'show'
        
    def configure(self, config):
        nnsimMac.configure(self, config)
    
    def tick(self):
        nnsimMac.tick(self)
        
        
        
class zeroComp(nnsimNZeroComp):
    
    def instantiate(self, setup):
    
        nnsimNZeroComp.instantiate(self, setup)
        # -----------------------------------------------
        # Flags for Stats Collection
        # ------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
        
    def configure(self, config):
        nnsimNZeroComp.configure(self, config)
    
    def tick(self):
        nnsimNZeroComp.tick(self)
        
