from nnsim.nnsimSerializer import nnsimSerializer
from nnsim.nnsimDeserializer import nnsimDeserializer


class IfmapSerializer(nnsimSerializer):
    
    def instantiate(self, setup):
        nnsimSerializer.instantiate(self, setup)
        self.class_name = 'IfmapSerializer'
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------        
        self.base_class_name                       = 'Serializer'
        
    def configure(self, config = {'active_in_chn':0, 'active_out_chn':0}):
        nnsimSerializer.configure(self, config)
    
    def tick(self):
        nnsimSerializer.tick(self)
        
        
class PsumSerializer(nnsimSerializer):
    
    def instantiate(self, setup):
        nnsimSerializer.instantiate(self, setup)
        self.class_name = 'PsumSerializer'
        
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------        
        self.base_class_name                       = 'Serializer'
        
    
    def configure(self, config = {'active_in_chn':0, 'active_out_chn':0}):
        nnsimSerializer.configure(self, config)
    
    def tick(self):
        nnsimSerializer.tick(self)
       
        
class WeightsSerializer(nnsimSerializer):
    
    def instantiate(self, setup):
        nnsimSerializer.instantiate(self, setup)
        self.class_name = 'WeightsSerializer'
        
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------        
        self.base_class_name                       = 'Serializer'
    
    def configure(self, config = {'active_in_chn':0, 'active_out_chn':0}):
        nnsimSerializer.configure(self, config)
    
    def tick(self):
        nnsimSerializer.tick(self)
        
        
class PsumDeserializer(nnsimDeserializer):
    
    def instantiate(self, setup):
        nnsimDeserializer.instantiate(self, setup)
        self.class_name = 'PsumDeserializer'
        
        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------        
        self.base_class_name                       = 'Deserializer'
        
    
    def configure(self, config = {'active_in_chn':0, 'active_out_chn':0}):
        nnsimDeserializer.configure(self, config)
    
    def tick(self):
        nnsimDeserializer.tick(self)