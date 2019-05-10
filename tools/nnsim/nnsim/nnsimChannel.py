from nnsim.module import Module, HWError
from nnsim.nnsimReg import Reg

class ChannelError(HWError):
    pass

class Channel(Module):
    def instantiate(self, depth = 2, width = 16):
        self.class_name         = "nnsimChannel"
        self.predefined_class   = True
        self.raw_access_stats   = {'push': 0,\
                                   'pop': 0}
        
        self.component_class_specification_stats     = 'hide'
        self.access_counts_stats                     = 'hide'
        self.component_specification_stats           = 'hide'
                                 
        self.data               = [None]*depth
        self.depth              = depth
        
        
        #initial value of read and write ptrs are zeros
        self.rd_ptr             = Reg(0)
        self.wr_ptr             = Reg(0)

        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------        
        self.attrs = {'depth' : depth, 'width': width}
        self.component_with_action  =  True
    

    def peek(self, idx = 0):
        if not self.valid(idx):
            raise ChannelError("Reading from empty channel")
        return self.data[(self.rd_ptr.rd() + idx) % self.depth]

    def push(self, x):
        if not self.vacancy():
            raise ChannelError("Enqueueing into full channel")
        self.data[self.wr_ptr.rd() % self.depth] = x  #it's possible to wr to smaller index and read from larger idx
        self.wr_ptr.wr((self.wr_ptr.rd() + 1) % (2*self.depth)) #update the wr_ptr such that it stays within range
        self.raw_access_stats['push'] += 1
 
    def free(self, count=1):
        if not self.valid(count-1):
            raise ChannelError("Dequeueing from empty channel")
        self.rd_ptr.wr((self.rd_ptr.rd() + count) % (2*self.depth))

    def pop(self):
        self.free(1)
        self.raw_access_stats['pop'] += 1
        return self.peek(0)
    
    #not writing ahead of reading/ self definition of "ahead of"
    def valid(self, idx=0):
        return ((self.wr_ptr.rd() - self.rd_ptr.rd()) % (2*self.depth)) > idx

    
    def vacancy(self, idx=0):  
        return ((self.rd_ptr.rd() + self.depth - self.wr_ptr.rd()) %
                (2*self.depth)) > idx

    def clear(self):
        # Use with care since it conflicts with enq and deq
        self.rd_ptr.wr(self.wr_ptr.rd())

class NoLatencyChannel(Module):
    def instantiate(self, depth = 2, width = 16):
        self.class_name = "nnsimNoLatencyChannel"
        self.predefined_class = True
        
        self.rd_ptr = 0
        self.wr_ptr = 0        
        
        self.data = [None]*depth
        self.depth = depth

        # -------------------------------------------------------------------
        # Flags for Showing Different Kinds of Stats Data
        # -------------------------------------------------------------------          
        self.attrs = {'depth' : depth, 'width': width}
        self.component_with_action  =  True
        
    def peek(self, idx=0):
        if not self.valid(idx):
            raise ChannelError("Reading from empty channel")
            
        return self.data[(self.rd_ptr + idx) % self.depth]


    def push(self, x):
        if not self.vacancy():
            raise ChannelError("Enqueuing into full channel")
    
        self.data[ self.wr_ptr % self.depth] = x
        # if self.name == 'drain_rsp_chn[0]':
        #     print('channel push: ', x)
        self.wr_ptr = (self.wr_ptr + 1)%(2 * self.depth)  
        
    def free(self, count = 1):
        if not self.valid(count-1):
            raise ChannelError("Dequeueing from empty channel")
        self.rd_ptr = (self.rd_ptr + count)%(2*self.depth)
        
    def pop(self):
        data = self.peek(0)
        self.free(1)
        # if self.name == 'drain_rsp_chn[0]':
        #     print('channel pop: ', data)
        return data 
    
    def valid(self, idx=0):
        return ((self.wr_ptr - self.rd_ptr)% (2*self.depth)) > idx

    def vacancy(self, idx=0):
        return ((self.rd_ptr + self.depth - self.wr_ptr )% 
                (2*self.depth)) > idx



def EmptyChannel(Channel):
    def valid(self, idx=0):
        return False

def FullChannel(Channel):
    def vacancy(self):
        return False

