from nnsim.module import Module, HWError
import numpy as np
RD = True
WR = False
class RegError(HWError):
    pass

class Reg(Module):
    def instantiate(self, reset_val):
        
        self.class_name                              = 'REG'
        self.component_class_specification_stats     = 'hide'
        self.access_counts_stats                     = 'hide'
        self.component_specification_stats           = 'hide'
        self.predefined_class                        = True
        self.reset_val                               = reset_val
        self.data_s                                  = reset_val
        self.data_m                                  = None

    def rd(self, enable = True):
        if enable:
            return self.data_s
        else:
            return np.nan

    def wr(self, x, enable = True):
        if enable:
            if self.data_m is not None:
                raise RegError("Double write on register")
            self.data_m = x
        # print("writing: ", x, 'data_m: ',self.data_m)

    def reset(self):
        self.data_s = self.reset_val
        self.data_m = None

    #at a negative clk edge, propogate value through slave latch   
    def __ntick__(self):
        if self.data_m is not None:
            self.data_s = self.data_m
            self.data_m = None
            # print('----ntick-----')
            # print(self.data_s, self.data_m)

            
class REGFILE(Module):
    def instantiate(self, depth, width=1, nports=1, dtype=np.int16):
        # depth: The number of address stored in the RAM
        # width: The number of words stored per address (NOT bits)
        # word-size is application dependent and implicit but <64b
        self.class_name = "REGFILE"
        self.predefined_class = True
        self.access_stats ={'rd': 0,\
                            'wr': 0}


        self.width = width
        self.nports = nports
        self.params = {'depth' : depth,\
                       'width': width,\
                       'nports': nports,\
                       'dtype': int(str(dtype)[-4:-2])}
        
        self.port_used = [False]*nports
        self.data = np.zeros((depth, width)).astype(dtype)

        # Emulate read latency
        self.output_reg = np.zeros((nports, width)).astype(dtype)
        self.rd_nxt = np.zeros((nports, width)).astype(dtype)

        # Emulate write latency
        self.port_wr = [False]*nports
        self.wr_nxt = np.zeros((nports, width)).astype(dtype)
        self.wr_addr_nxt = np.zeros(nports).astype(np.uint32)


    def request(self, access, address, data=None, port=0):
        if self.port_used[port]:
            raise RAMError("Port conflict on port %d" % port)
        self.port_used[port] = True

        if access == RD:
            self.rd_nxt[port, :] = self.data[address, :]
            self.raw_access_stats['rd'] += 1
            #print("access is a read")
            #print("read next cycle is: ",self.rd_nxt[port, :] )
        elif access == WR:
            self.port_wr[port] = True
            self.wr_addr_nxt[port] = address
            if self.width == 1:
                self.wr_nxt[port, 0] = data
            else:
                self.wr_nxt[port, :] = data[:]
            self.raw_access_stats['wr'] += 1

    def response(self, port=0):
        data = self.output_reg[port]
        return data[0] if self.width == 1 else data

    def __ntick__(self):
        self.output_reg[:] = self.rd_nxt[:]
        #print("negative clk edge, output_reg: ",self.output_reg[:] )
        for port in range(self.nports):
            self.port_used[port] = False

            if self.port_wr[port]:
                self.port_wr[port] = False
#                print("======== ", self.wr_nxt[port,:])
                self.data[self.wr_addr_nxt[port], :] = self.wr_nxt[port, :]

    def dump(self):
        for i in range(self.data.shape[0]):
            print(i, self.data[i])