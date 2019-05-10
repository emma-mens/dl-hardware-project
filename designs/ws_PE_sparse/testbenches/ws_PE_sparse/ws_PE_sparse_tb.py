# ----------------------------------------------------------------------
# Import Libraries
# ----------------------------------------------------------------------
import sys
import numpy as np

# import simulator constructs for hardware insatntiation
from nnsim.module import ModuleList
from nnsim.nnsimChannel import Channel
from nnsim.simulator import Finish
from nnsim.nnsimTestBench import nnsimTestBench
from constraint_checker import check_constriant
# import design descriptions for hardware insatntiation
sys.path.append('../../model')
from pe_sparse import PE_sparse
from nnsim.nnsimRecorder import nnsimRecorder

# import trace generator for input data and output reference
#from config import *
from ws_PE_sparse_trace_generator import ws_PE_sparse_trace_generator

class ws_PE_sparse_tb(nnsimTestBench):
    ''' Testbench specifically for weight stationary PE_ARARRY + GLB + NoC testing '''
    def instantiate(self, setup):
        nnsimTestBench.instantiate(self, setup)

        self.trace_generator            = ws_PE_sparse_trace_generator()
        self.traces_stats               = 'show'
        self.recorder                   = nnsimRecorder() if self.traces_stats == 'show' else None
        self.generated_trace            = True
        
        # bookkeeping variables
        self.result                     = []
        # ---------------------------------------------------------------------
        # IO channels for onchip and offchip communications
        # ---------------------------------------------------------------------
        # -> input channels for sending the input trace data to the GLBs
        # smartbuffer needs channels specified as list format
        self.weights_in_chn             = Channel()
        self.ifmap_chn                  = Channel()
        self.psum_in_chn                = Channel()
        # -> output channel for reciving calculated psum from the chip
        self.psum_out_chn               = Channel()
        
        pe_setup = {'weights_data_in_chn': self.weights_in_chn,\
                    'ifmap_data_in_chn': self.ifmap_chn,\
                    'psum_data_in_chn': self.psum_in_chn,\
                    'psum_data_out_chn': self.psum_out_chn}
        pe_setup.update(self.arch['PE'])
        self.dut  = PE_sparse(pe_setup) 
        
    def configure(self):
        # ====================================================================================================
        # 1. check if the setup meets the constraints,  if not met, program will exit
        # 2. apply paddings to input channels if total input channels not divisible by input channel mapping
        # ====================================================================================================
        check_constriant(self.mapping, self.shape, self.arch, self.ifmap_data, self.weights_data, self.bias_data)
        # ====================================================================================================        
        print('>> Generating input/output traces ')
        
        # configure trace generator
        trace_gen_config = { 'mapping':       self.mapping,\
                             'shape':         self.shape,\
                             'ifmap_data':    self.ifmap_data,\
                             'weights_data':  self.weights_data,\
                             'bias_data':     self.bias_data}
        
        
        self.trace_generator.configure(trace_gen_config)
        traces = self.trace_generator.generate_trace()
        
        # configure input traces
        self.weights_itrace          = traces['weights']
        self.ifmap_itrace            = traces['ifmap']
        self.psum_itrace             = traces['psum_in']
        self.psum_otrace             = traces['psum_out']        
        
        print('>> Configuring the testbech and unit under test ')
        # bookkeeping indexes used to step through the generated traces cycle by cycle 
        self.weights_itrace_idx      = 0
        self.ifmap_itrace_idx        = 0
        self.psum_itrace_idx         = 0
        
        #===========================================================================
        # PE configuration
        #===========================================================================   
        # configure the PE for specific workload and define the output channel
        lm_sram_map   = {'WeightsSp': [{'drain': 0, 'fill': 1}]}
        
        # weight scratchpad (depth = 1) config info
        buffer_config = {'LM': [{'base': 0, 'bound': self.arch['PE']['wsp_depth']-1}],\
                         'lm_sram_map':lm_sram_map['WeightsSp'].copy() }
                                
        shape_mapping_info = {'shape': self.shape.copy(), 'mapping': self.mapping.copy()}
        config =  { 'WeightsSp':            buffer_config,\
                    'shape_mapping_info':   shape_mapping_info,\
                    'clk_gated':            False}  
        self.dut.configure(config)
        
        print('----------------------------------------------------------------------------------')
        print(' Simulation starting ...')
        print('----------------------------------------------------------------------------------')
        
    def tick(self):
        # ----------------------------------------------------------------------------------------
        # Send Traces into the Designs input channels, cycle by cycle
        # ----------------------------------------------------------------------------------------
        
        # ------------------------- weights input trace ----------------------------------------------
        if self.weights_in_chn.vacancy():
            if self.weights_itrace_idx  < len(self.weights_itrace):
                if not np.isnan(self.weights_itrace[self.weights_itrace_idx]):
                    weight_data_to_send = [ self.weights_itrace[self.weights_itrace_idx]]
                    self.weights_in_chn.push(weight_data_to_send)
                    self.weights_itrace_idx += 1
            else:
                self.weights_done = True
        # ------------------------- ifmap input trace ------------------------------------------------    
        if self.ifmap_chn.vacancy():
            if self.ifmap_itrace_idx < len(self.ifmap_itrace):
                if not np.isnan(self.ifmap_itrace[self.ifmap_itrace_idx]):
                    ifmap_data_to_send = [ self.ifmap_itrace[self.ifmap_itrace_idx]]
                    self.ifmap_chn.push(ifmap_data_to_send)
                    self.ifmap_itrace_idx += 1
            else:
                self.ifmap_done = True  
                
        if self.psum_in_chn.vacancy():
            if self.psum_itrace_idx < len(self.psum_itrace):
                if not np.isnan(self.psum_itrace[self.psum_itrace_idx]):
                    psum_data_to_send = [ self.psum_itrace[self.psum_itrace_idx]]
                    self.psum_in_chn.push(psum_data_to_send)
                    self.psum_itrace_idx += 1
            else:
                self.psum_done = True  
                
        # -------------------------------------------------------------------------------------------
        # Collect output from the design's output channel
        # -------------------------------------------------------------------------------------------
        if self.psum_out_chn.valid():
            psum_out = self.psum_out_chn.pop()
            for idx in range(len(psum_out)):
                p = psum_out[idx]
                self.result.append(p)
#                print('-->', len(self.result), 'calculated:', p, 'reference:', self.psum_otrace[len(self.result)-1], 'total:',len(self.psum_otrace) )
    
        # -------------------------------------------------------------------------------------------
        # Compare the design's output with the generated output traces to validate functionality
        # -------------------------------------------------------------------------------------------        
        if len(self.result) == len(self.psum_otrace):
            if self.result == self.psum_otrace:
                raise Finish('Success')
            else:
              print('Failed')
              print('---------ofmap-----------------')
              print(self.result)
              print('----------ofmap_trace------------')
              print(self.psum_otrace)
              print('---------difference------------')
              difference = self.result
              for i in range(len(difference)):
                  difference[i] = self.result[i] - self.psum_otrace[i]
              print(difference)
              raise Finish()    
    
#if __name__ == "__main__":
def main(architecture_name, layer_name, mapping_name, bias_data_name, weights_data_name, ifmap_data_name, stats_name):
    from nnsim.simulator import run_tb
    # =======================================================================
    print('\t SETTING UP WS DESIGN TESTBENCH...')
    print('##############################################')
    print(' architecture:',   architecture_name, \
          '\n layer:',        layer_name, \
          '\n mapping: ',     mapping_name,\
          '\n bias_data:',    bias_data_name,\
          '\n ifmap_data:',   ifmap_data_name,\
          '\n weights_data:', weights_data_name,\
          '\n stats_name:',   stats_name)
    print('##############################################')
    #============================================================== 
    # Instantiate & Configure Testbench
    #============================================================== 
    setup = {'architecture_name': architecture_name, \
             'layer_name':        layer_name,\
             'bias_data_name':    bias_data_name,\
             'ifmap_data_name':   ifmap_data_name,\
             'weights_data_name': weights_data_name,\
             'mapping_name':      mapping_name}
    tb = ws_PE_sparse_tb(setup)
    tb.configure()
    # ============================================================== 
    # run simulation
    #============================================================== 
    # directory for saving the stats (access counts, traces, etc.)
    import os

    os.makedirs(stats_name, exist_ok = True)        
    # start simulation
    run_tb(tb, \
           verbose      = False, \
           dump_stats   = True, \
           stats_dir    = stats_name, \
           nticks       = None)
        
if __name__ == "__main__":    
    architecture_name = sys.argv[1] 
    layer_name        = sys.argv[2] 
    mapping_name      = sys.argv[3] 
    bias_data_name    = sys.argv[4]
    weights_data_name = sys.argv[5] 
    ifmap_data_name   = sys.argv[6]
    stats_name        = sys.argv[7]
    main(architecture_name, layer_name, mapping_name, bias_data_name, weights_data_name, ifmap_data_name, stats_name)     
    
    
    