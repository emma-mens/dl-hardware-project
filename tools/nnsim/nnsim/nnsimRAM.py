from nnsim.module import Module, HWError
from nnsim.nnsimReg import Reg
import numpy as np

RD = True
WR = False

class RAMError(HWError):
    pass
        
        
class SRAM(Module):
    def instantiate(self, setup):
        # depth: The number of address stored in the RAM
        # width: The number of words stored per address (NOT bits)
        # word-size is application dependent and implicit but <64b
        self.class_name = "SRAM"
        self.predefined_class = True
        self.component_class_as_subclass = 'show'
        self.debug = setup['debug'] if 'debug' in setup else None
        
        # -------------------------------------------------------------------
        # Internal Hardware Setup
        # -------------------------------------------------------------------
        self.width      = setup['width']
        self.depth      = setup['depth']
        self.nports     = setup['nports']
        self.port_type  = setup['port_type']
        self.data_width = setup['data_width']
        self.nbanks     = setup['nbanks']
        self.dtype      = setup['dtype'] if 'dtype' in setup else np.int32
        self.attrs = {'depth' :     self.depth,\
                      'width':      self.width,\
                      'data_width': self.data_width,\
                      'nports':     self.nports,\
                      'nbanks':     self.nbanks}
        
        self.port_used = [False]*self.nports
        self.data = np.zeros((self.depth, self.width)).astype(self.dtype )

        # Emulate read latency
        self.output_reg = np.zeros((self.nports, self.width)).astype(self.dtype)
        self.rd_nxt = np.zeros((self.nports, self.width)).astype(self.dtype)

        # Emulate write latency
        self.port_wr = [False]*self.nports
        self.wr_nxt = np.zeros((self.nports, self.width)).astype(self.dtype)
        self.wr_addr_nxt = np.zeros(self.nports).astype(self.dtype)

   
    def port_in_use(self, port = 0):
        if self.port_used[port]:
           return True
        return False

    def request(self, access, address, data=None, port=0):
        if self.port_used[port]:
            raise RAMError("Port conflict on port %d" % port)
        self.port_used[port] = True

        if access == RD:
            if not self.port_type[port] == 'rd' and not self.port_type[port]  == 'rw':
                raise RAMError(" Rd using a non-readable port")
            self.rd_nxt[port, :] = self.data[address, :]
            
        elif access == WR:
            if not self.port_type[port]  == 'wr' and not self.port_type[port]  == 'rw':
                raise RAMError(" Wr using a non-writble port")
            self.port_wr[port] = True
            self.wr_addr_nxt[port] = address
            self.wr_nxt[port, :] = data[:]

    def response(self, port=0):
        if not self.port_type[port] == 'rd' and not self.port_type[port] == 'rw':
            raise RAMError(" Request Rd response from a non-readable port")        
        data = self.output_reg[port]
        return data

    def __ntick__(self):
        
        self.output_reg[:] = self.rd_nxt[:]
        for port in range(self.nports):
            self.port_used[port] = False

            if self.port_wr[port]:
                self.port_wr[port] = False
                self.data[self.wr_addr_nxt[port], :] = self.wr_nxt[port, :]
        

    def dump(self, l = None):
        if l is None:
            l = self.data.shape[0]
        for i in range(l):
            print(i, self.data[i])
            
