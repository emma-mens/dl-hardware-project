# -*- coding: utf-8 -*-
from nnsim.nnsimSmartBuffer   import nnsimSmartBuffer
from weights_glb_ags          import WeightsGLBDrainAG, WeightsGLBFillAG
from psum_glb_ags             import PsumGLBDrainAG, PsumGLBUpdateAG, PsumGLBFillAG
from ifmap_glb_ags            import IFMapGLBDrainAG, IFMapGLBFillAG

class WeightsGLB(nnsimSmartBuffer):
    
    def instantiate(self, setup):
        
        setup['LMs']        = [{'AGs':{'drain': WeightsGLBDrainAG, 'fill': WeightsGLBFillAG}}]
        setup['debug']      = 'WeightsGLB'
        
        nnsimSmartBuffer.instantiate(self, setup)              
        
        self.class_name = 'WeightsGLB' 
        
        #======================================================================
        #                  Stats Collection Info
        #======================================================================  
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
        
            
    def configure(self, config):
       config['LM'][0]['AGs'] =  {'logical_depth': config['LM'][0]['bound']-config['LM'][0]['base'] + 1}
       config['LM'][0]['AGs'].update(config['shape_mapping_info'].copy())
       nnsimSmartBuffer.configure(self, config)

    def define_access_stats(self):
        # -----------------------------------------------------------------------------
        # Record Related Access Count
        # -----------------------------------------------------------------------------
        self.access_stats['idle']         = {'count': self.sbuffer.buffer.access_stats['idle']}
        for key, value in self.sbuffer.buffer.access_stats['SRAM_access'].items():
            self.access_stats['buffer_access'].append({'attributes': {'ndrain': key[0], 'nfill': key[1], 'n_repeated_drain':key[2]}, 'count': value})



class IFmapGLB(nnsimSmartBuffer):
    
    def instantiate(self, setup):
        
        setup['LMs']              = [{'AGs':{'drain': IFMapGLBDrainAG, 'fill': IFMapGLBFillAG}}]
        setup['debug']            = 'IFmapGLB'
        
        nnsimSmartBuffer.instantiate(self, setup)              
        
        self.class_name = 'IFmapGLB' 
        
        #======================================================================
        #                  Stats Collection Info
        #======================================================================  
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
            
    def configure(self, config):
        
      config['LM'][0]['AGs'] = {'logical_depth': config['LM'][0]['bound']-config['LM'][0]['base'] + 1}
      config['LM'][0]['AGs'].update(config['shape_mapping_info'].copy())
      
      nnsimSmartBuffer.configure(self, config)

class PsumGLB(nnsimSmartBuffer):
    
    def instantiate(self, setup):
        
        setup['LMs']              = [{'AGs':{'drain': PsumGLBDrainAG, 'fill': PsumGLBFillAG, 'update': PsumGLBUpdateAG}}]
        setup['debug']            = 'PsumGLB'
        
        nnsimSmartBuffer.instantiate(self, setup)              
        
        self.class_name = 'PsumGLB' 
        
        #======================================================================
        #                  Stats Collection Info
        #======================================================================  
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------
        self.component_class_as_subclass           = 'show'  # whether to show the class information as a subclass
        self.component_class_as_topclass           = 'show'  # whether to show the class_information as a top level class
        self.component_specification_stats         = 'show'
        self.access_counts_stats                   = 'show'
            
    def configure(self, config):
        
      config['LM'][0]['AGs'] = {'logical_depth': config['LM'][0]['bound']-config['LM'][0]['base'] + 1}
      config['LM'][0]['AGs'].update(config['shape_mapping_info'].copy())
      
      nnsimSmartBuffer.configure(self, config)
       
        
