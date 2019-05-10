# -*- coding: utf-8 -*-
from nnsim.module import Module, ModuleList
from nnsim.nnsimChannel import Channel
from glb import WeightsGLB, IFmapGLB, PsumGLB
from pe import PE
from destination_calculator import IFmapNoCDestCalc, WeightsNoCDestCalc, PsumInNoCDestCalc
from noc import WeightsNoC, IFMapNoC, PsumRdNoC, PsumWrNoC
from serdes import IfmapSerializer, WeightsSerializer, PsumSerializer


class chip(Module):
    def instantiate(self, setup):
        
        self.pe_array_row       = setup['pe_array'][0]
        self.pe_array_col       = setup['pe_array'][1]
        
        # ---------------------------------------------------------------------
        # io data b/w offchip
        # ---------------------------------------------------------------------
        self.weights_in_chns    = setup['io_chns']['weights']
        self.ifmap_in_chns      = setup['io_chns']['ifmap'] 
        self.psum_in_chns       = setup['io_chns']['psum_in']
        self.psum_out_chn       = setup['io_chns']['psum_out']
        
        # ---------------------------------------------------------------------
        # onchip channels
        # ---------------------------------------------------------------------
        # >> buffer output channels
        self.weights_out_chns   = ModuleList(Channel())
        self.ifmap_out_chns     = ModuleList(Channel())
        self.ifmap_out_chns     = ModuleList(Channel())
        self.psum_out_chns      = ModuleList(Channel())
        
        # >> update data to buffer
        self.psum_update_chns   = ModuleList(Channel())
        
        # ===================================================================
        # GLBs
        # ===================================================================
        # ------------------------ WEIGHTS -------------------------------
        weights_glb_setup = {'fill_data_ichns':        self.weights_in_chns,\
                             'drain_data_ochns':       self.weights_out_chns, \
                             'num_logical_managers':   1,\
                             'SRAM':                   {\
                                                        'depth':      setup['depth']['WeightsGLB'],\
                                                        'width':      setup['width']['WeightsGLB'],\
                                                        'data_width': setup['data_width']['WeightsGLB'],\
                                                        'nbanks':     setup['nbanks']['WeightsGLB'],\
                                                        'nports':     setup['nports']['WeightsGLB'],\
                                                        'port_type':  setup['port_type']['WeightsGLB'],\
                                                        },\
                             'debug': ' WeightsGLB'}
        self.weights_glb  = WeightsGLB(weights_glb_setup)
        
        # ------------------------ IFMAP -------------------------------
        ifmap_glb_setup = {'fill_data_ichns':        self.ifmap_in_chns,\
                           'drain_data_ochns':       self.ifmap_out_chns, \
                           'num_logical_managers':   1,\
                           'SRAM':                   {\
                                                      'depth':      setup['depth']['IFmapGLB'],\
                                                      'width':      setup['width']['IFmapGLB'],\
                                                      'data_width': setup['data_width']['IFmapGLB'],\
                                                      'nbanks':     setup['nbanks']['IFmapGLB'],\
                                                      'nports':     setup['nports']['IFmapGLB'],\
                                                      'port_type':  setup['port_type']['IFmapGLB'],\
                                                        },\
                            'debug': ' IFmapGLB'} 
        self.ifmap_glb =  IFmapGLB(ifmap_glb_setup)
        
        # ------------------------ PSUM -------------------------------
        psum_glb_setup = {'fill_data_ichns':        self.psum_in_chns,\
                          'update_data_ichns':      self.psum_update_chns,\
                          'drain_data_ochns':       self.psum_out_chns, \
                          'num_logical_managers':   1,\
                          'SRAM':                   {\
                                                      'depth':      setup['depth']['PsumGLB'],\
                                                      'width':      setup['width']['PsumGLB'],\
                                                      'data_width': setup['data_width']['PsumGLB'],\
                                                      'nbanks':     setup['nbanks']['PsumGLB'],\
                                                      'nports':     setup['nports']['PsumGLB'],\
                                                      'port_type':  setup['port_type']['PsumGLB'],\
                                                        },\
                            'debug': ' PsumGLB'} 
        self.psum_glb =  PsumGLB(psum_glb_setup)

        
        # ===================================================================
        # PE Array Channels
        # ===================================================================
        self.ifmap_pe_data_chns   = ModuleList()
        self.weights_pe_data_chns = ModuleList()
        self.psum_data_chns       = ModuleList()
        
        self.pe_data_chns = {'ifmap':        self.ifmap_pe_data_chns,\
                             'weights':      self.weights_pe_data_chns,\
                             'psum':         self.psum_data_chns}
        
        for pe_row in range(self.pe_array_row):
            for chn_type, chn_row in self.pe_data_chns.items():
                chn_row.append(ModuleList())
            for pe_col in range(self.pe_array_col):
                for chn_type, chn_col in self.pe_data_chns.items():
                    chn_col[pe_row].append(Channel())

        self.psum_data_chns.append(ModuleList())
        for pe_col in range(self.pe_array_col):
            self.psum_data_chns[-1].append(Channel())
        
        # ===================================================================
        # Destination Calculators for NoC
        # ===================================================================
        self.ifmap_NoC_destination_chn = ModuleList(Channel())
        ifmap_NoC_destination_calculator_setup = \
                          {'out_chn': self.ifmap_NoC_destination_chn[0],\
                           'out_channel_width': 1,\
                           'debug': 'IFmapNoCDestCalc'}
        self.ifmap_NoC_destination_calculator = IFmapNoCDestCalc(ifmap_NoC_destination_calculator_setup)
        
        
        self.weights_NoC_destination_chn = ModuleList(Channel())       
        weights_NoC_desitnation_calculator_setup = \
                           {'out_chn': self.weights_NoC_destination_chn[0],\
                            'out_channel_width': 1,\
                            'debug': 'WeightsNoCDestCalc'}
        self.weights_NoC_destionation_calculator = WeightsNoCDestCalc(weights_NoC_desitnation_calculator_setup)
        

        self.psum_in_NoC_destination_chn = ModuleList(Channel())         
        psum_in_NoC_desitnation_calculator_setup = \
                           {'out_chn': self.psum_in_NoC_destination_chn[0],\
                            'out_channel_width': 1,\
                            'debug': 'PsumInNoCDestCalc'}
        self.psum_in_NoC_destionation_calculator = PsumInNoCDestCalc(psum_in_NoC_desitnation_calculator_setup)   
        
        
        # ===================================================================
        # NoCs
        # ===================================================================
        # weights serializer 4:1
        self.weights_serializered_data_chn = Channel()
        weights_serializer_setup           = {'in_chn':  self.weights_out_chns[0],\
                                              'out_chn': self.weights_serializered_data_chn,\
                                              'ratio':   setup['weights_seri_ratio'],\
                                              'debug':   'weights_serialzer'}
        self.weights_serializer            = WeightsSerializer(weights_serializer_setup)
        
        # Weights NoC: weightGLB -> PEs
        weights_noc_setup = {'rd_chns': self.pe_data_chns['weights'],\
                             'wr_chns': self.weights_serializered_data_chn,\
                             'dest_chns': self.weights_NoC_destination_chn,\
                             'debug': 'WeightsNoC'}
        self.weightsNoC   = WeightsNoC(weights_noc_setup)
        
        # -------------- IFmap NoC: IfmapGLB -> PEs -----------------------
        # ifmap serializer 4:1
        self.ifmap_serialized_data_chn    = Channel()
        ifmap_serializer_setup            = {'in_chn':  self.ifmap_out_chns[0],\
                                             'out_chn': self.ifmap_serialized_data_chn,\
                                             'ratio':   setup['ifmap_seri_ratio'],\
                                             'debug':  'ifmap_serializer'}
        self.ifmap_serilizer = IfmapSerializer(ifmap_serializer_setup)
        
        # ifmap NoC
        ifmap_noc_wr_chns = ModuleList()
        ifmap_noc_wr_chns.append(self.ifmap_serialized_data_chn)
        ifmap_noc_setup = {'rd_chns':   self.pe_data_chns['ifmap'],\
                           'wr_chns':   ifmap_noc_wr_chns,\
                           'dest_chns': self.ifmap_NoC_destination_chn,\
                           'debug':     'IFmapNoC'}
        self.ifmapNoC   = IFMapNoC(ifmap_noc_setup)
        # ---------------------------------------------------------------------
        
        # -------------- PsumRd NoC: Psum GLB -> PEs ----------------------
        
        # psum serializer 4:1
        self.psum_serialized_data_chn    = Channel()
        psum_serializer_setup            = {'in_chn':  self.psum_out_chns[0],\
                                            'out_chn': self.psum_serialized_data_chn,\
                                            'ratio':   setup['psum_seri_ratio'],\
                                            'debug':   'psum_serialzer'}
        self.psum_serializer             = PsumSerializer(psum_serializer_setup)
        
        # psum read noc
        pe_noc_wr_chn = ModuleList(self.psum_serialized_data_chn)
        
        psum_rd_noc_setup = {'rd_chns':   self.psum_data_chns,\
                             'wr_chns':   pe_noc_wr_chn,\
                             'dest_chns': self.psum_in_NoC_destination_chn,\
                             'debug':     'PsumRdNoC'}
        self.psumRdNoC    =  PsumRdNoC(psum_rd_noc_setup)
        # ---------------------------------------------------------------------
        
        # -------------- PsumWrNoC:  PEs -> ifmapPsum GLB ---------------------
        self.psum_out_noc_rd_chns = ModuleList()
        self.psum_out_noc_rd_chns.append(self.psum_update_chns[0]) # write back to GLB
        self.psum_out_noc_rd_chns.append(self.psum_out_chn)     # write offchip
        psum_wr_noc_setup = {'rd_chns':       self.psum_out_noc_rd_chns,\
                             'wr_chns':       self.psum_data_chns,\
                             'debug':        'PsumWrNoC'}
        self.psumWrNoC    =  PsumWrNoC(psum_wr_noc_setup)        
            
        # ===================================================================
        # PE Array
        # ===================================================================
        # general setup of a PE
        PE_setup          = setup['PE']
        
        self.PE = ModuleList()

        
        for pe_row in range(self.pe_array_row):
            self.PE.append(ModuleList())
            for pe_col in range(self.pe_array_col):
                # PE specific setup
                PE_setup['row'] = pe_row
                PE_setup['col'] = pe_col
                PE_setup['weights_data_in_chn']    = self.weights_pe_data_chns[pe_row][pe_col]
                PE_setup['ifmap_data_in_chn']      = self.ifmap_pe_data_chns[pe_row][pe_col]
                PE_setup['psum_data_in_chn']       = self.psum_data_chns[pe_row][pe_col]
                PE_setup['psum_data_out_chn']      = self.psum_data_chns[pe_row + 1][pe_col]
                self.PE[pe_row].append(PE(PE_setup))
                

    def configure(self, config):
        
        # extract the shape and mapping information
        self.mapping  = config['mapping']
        self.shape    = config['shape']
        
        # --------------------------------------------------------------------
        # Configure Global Buffers
        # --------------------------------------------------------------------  
        self.weights_glb.configure(config['WeightsGLB'])
        self.ifmap_glb.configure(config['IFmapGLB'])
        self.psum_glb.configure(config['PsumGLB'])
        
        # --------------------------------------------------------------------
        # Configure Destination Calculators
        # --------------------------------------------------------------------
        shape_mapping_info = {'mapping': self.mapping, 'shape': self.shape}
        self.ifmap_NoC_destination_calculator.configure(shape_mapping_info)       
        self.weights_NoC_destionation_calculator.configure(shape_mapping_info)  
        self.psum_in_NoC_destionation_calculator.configure(shape_mapping_info)
        
        # --------------------------------------------------------------------
        # Configure NoCs
        # --------------------------------------------------------------------
        self.weightsNoC.configure()
        self.ifmapNoC.configure()
        self.psumRdNoC.configure()
        # >> self defined NoC module
        self.psumWrNoC.configure({'mapping': self.mapping, 'shape': self.shape})
        
        # --------------------------------------------------------------------
        # Configure Serializers/Deserilizers
        # --------------------------------------------------------------------        
        self.ifmap_serilizer.configure()
        self.psum_serializer.configure()
        self.weights_serializer.configure()
        
        # --------------------------------------------------------------------
        # Configure PE Arrays
        # --------------------------------------------------------------------          
        PE_config  = config['PE']
        for pe_row in range(self.pe_array_row):
            for pe_col in range(self.pe_array_col):
                # determine if the PE needs to be used for this layer
                PE_config['clk_gated'] = True if pe_col >= self.mapping['M0'] or \
                                                 pe_row >= self.mapping['C0']\
                                              else False
                                                  
                self.PE[pe_row][pe_col].configure(PE_config)

            