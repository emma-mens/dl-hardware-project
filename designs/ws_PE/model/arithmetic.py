# -*- coding: utf-8 -*-

from nnsim.nnsimArithmetic import nnsimMac, nnsimNZeroComp
# ================================================================
# PLEASE DO NOT CHANGE THIS FILE
# ================================================================
class mac(nnsimMac):
    
    # --------------------------------------------------------------------
    # Instantiate the module (DO NOT CHANGE)
    # --------------------------------------------------------------------  
    def instantiate(self, setup):
        # a child class of nnsim package class nnsimMacPerformance, the parent class does a mac in a cycle
        nnsimMac.instantiate(self, setup)
        #======================================================================
        #                  Stats Collection Info
        #====================================================================== 
        self.class_name              = 'mac' 
        self.predefined_class        = True
        self.base_class_name         = 'MAC'
        
        self.attrs['data_width']     = 8
        
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data 
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
    
    # --------------------------------------------------------------------
    # Configure the modulev (DO NOT CHANGE)
    # --------------------------------------------------------------------         
    def configure(self, config):
        nnsimMac.configure(self, config)
    
    # --------------------------------------------------------------------
    # What does this module do on positive eedge of the clock? (DO NOT CHANGE)
    # --------------------------------------------------------------------
    def tick(self):
        # Same as the parent class (details in lab4/tools/nnsim/nnsim/nnsimArithmetic.py)
        # On high level:
	#    1. if there are operands in the input channels, pop out each operand out of its input channel
	#    2. Does the mac operation if both multiplicants are nonzero, otherwise, skip the multiplication
	#    3. push the results out to its ouput channel
        nnsimMac.tick(self)

        
        

