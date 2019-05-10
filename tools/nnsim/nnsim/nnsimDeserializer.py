from nnsim.module import Module
        
class nnsimDeserializer(Module):
    
    def instantiate(self, setup):
        self.in_chn                 = setup['in_chn']
        self.out_chn                = setup['out_chn'] 
        self.ratio                  = setup['ratio']  # how many data are packaged together
        self.debug                  = setup['debug']
        self.predefined_class       = True
        self.component_with_action  = True
        
        
        self.class_name             = 'nnsimDeserializer'
        
        self.action                 = {'deserialize': None}
        self.attrs                  = {'deserialization_ratio': self.ratio}
        self.access_stats           = {'deserialize': {'count':0}, 'idle':{'count': 0}}
        self.component_with_action = True
        
        
    
    def configure(self, config = {'active_in_chn':0, 'active_out_chn':0}):
        self.ready_to_send  = False  # there is aready full packet for sending
        self.data           = []
        self.idx            = 0
        
        self.active_in_chn_idx  = config['active_in_chn']
        self.active_out_chn_idx = config['active_out_chn']   
        
        # determine whether we are dealing with channel list or individual channels 
        self.active_in_chn = self.in_chn if issubclass(type(self.in_chn), Module) \
                                    else self.in_chn[self.active_in_chn_idx]
                                    
        self.active_out_chn = self.out_chn if issubclass(type(self.out_chn), Module) \
                                    else self.out_chn[self.active_out_chn_idx]
    
    def tick(self):
        
        if self.active_in_chn.valid() and not self.ready_to_send:
            self.data += self.active_in_chn.pop()
#            print(self.debug, ' detected data ', self.data)
            self.idx += 1
            
            if self.idx == self.ratio:
                self.idx = 0
                self.ready_to_send = True
                self.access_stats['deserialize']['count']  += 1

        elif self.active_out_chn.vacancy() and self.ready_to_send:
            self.active_out_chn.push(self.data)
#            if 'PE' in self.debug:
#                print(self.debug, ' pushing out data', self.data)
            self.ready_to_send = False
            self.data = []
       
        else:
            self.access_stats['idle']['count']  += 1
            

