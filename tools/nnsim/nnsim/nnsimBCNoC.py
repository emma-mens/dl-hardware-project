from nnsim.module import Module 
import numpy as np

class nnsimBCNoC(Module):  
    def instantiate(self, setup):
        
        self.class_name = 'nnsimNoC'
        
        self.debug      = None if 'debug' not in setup \
                               else setup['debug']
        
        self.rd_chns    = setup['rd_chns']
        self.wr_chns    = setup['wr_chns']
   
        self.srd_chns   = self.rd_chns.getsize()
        self.swr_chns   = self.wr_chns.getsize()
        
        # total number of read/write channels
        self.nrd_chns   = np.prod(self.srd_chns)  
        self.nwr_chns   = np.prod(self.swr_chns) 
        
        # all total physcial read/write channels laid out in a linear fashion
        self.rd_flatten   = self.rd_chns.reshape((1,)) 
        self.wr_flatten   = self.wr_chns.reshape((1,)) 
        
    def configure(self):
        # make sure there is no double push for the same read channels
        #     possible when two data needs to be written to the same read channel        
        self.vacancy_record = [True] * self.nrd_chns 
        self.ncol = 14
    
    # ------------------------------------------------------------------------
    # Convert the index from high dimension to linear 
    # ------------------------------------------------------------------------
    def dest_to_linear(self, dest):
        linear = 0
        # if this is a 1D index, return the value
        if len(dest) == 1:
            return dest[0]
        else:
            linear = dest[0] * self.ncol + dest[1]
            return linear        

    def tick(self):
        if self.clk_gated:
            return        
        self.vacancy_record = [True] * self.nrd_chns
        for entry_idx in range(len(self.vacancy_record)):
            if not self.rd_flatten[entry_idx].vacancy():
                self.vacancy_record[entry_idx] = False
        # data is from write chns 
        # data is sent to read chns    
        for wi in range(self.nwr_chns): 
            if self.wr_flatten[wi].valid():
                # --------------------------------------------------------------------------
                # check if all the destinations the data is multicasted to have space
                # --------------------------------------------------------------------------
                vacancy = True

                for idx in range(self.nrd_chns):
                    vacancy = vacancy and self.rd_flatten[idx].vacancy()\
                              and self.vacancy_record[idx] 

                # if there is space for every channel
                if vacancy:
                    data = self.wr_flatten[wi].pop()
                    for idx in range(self.nrd_chns):
                        # send data
                        self.rd_flatten[idx].push(data)
                        self.vacancy_record[idx] = False  
#                else:
#                    print('No vacancy', self.vacancy_record)


