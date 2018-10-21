# This module contains the top level receiver block
#
# Input:
#   - none, this block instances its IQ source
# Output:
#   - messages sent via ZMQ

import zmq_utils as zmqu
import rf_mgt as rfm
import rx_source
import rx_tuner
import rx_ook_demod
import rx_clk_sync
import bb_sync
from gnuradio import gr
from gnuradio import zeromq
from gnuradio import blocks
from gnuradio import eng_option


class RxTop(gr.top_block):

    def __init__(self,
                 rf_params,
                 bb_params,
                 tcp_addr,
                 tcp_test):
        gr.top_block.__init__(self, "rx_top")

        # parameters
        self.rf_params = rf_params
        self.bb_params = bb_params
        self.tcp_addr = tcp_addr
        self.tcp_addr_test = tcp_test

        # variables
        self.samp_rate = rf_params.samp_rate
        self.center_freq = rf_params.center_freq
        self.working_samp_rate = 10/bb_params.symbol_time

        # rf source
        self.src = rx_source.rx_source(rf_params=self.rf_params,
                                       tcp_test=self.tcp_addr_test)

        # tuner
        self.tuner = rx_tuner.RxTuner(rf_params=self.rf_params,
                                      working_samp_rate=self.working_samp_rate)
        self.connect((self.src, 0), (self.tuner, 0))

        # demod
        if rf_params.mod_scheme == rfm.MOD_OOK:
            self.mod_only = rx_ook_demod.rx_ook_demod(
                rf_params=self.rf_params,
                bb_params=self.bb_params)
            self.connect((self.tuner, 0), (self.mod_only, 0))
            self.mod_sync = rx_clk_sync.rx_clk_sync(
                bb_params=self.bb_params,
                working_samp_rate=self.working_samp_rate)
            self.connect((self.mod_only, 0), (self.mod_sync, 0))
        #elif rf_params.mod_scheme == rfm.MOD_FSK
        #    self.mod_sync = rx_fsk_demod.rx_fsk_demod(rf_params)
        #    self.connect((self.tuner, 0), (self.mod_only, 0))

        # preamble sync, packet construction and output via ZMQ
        self.packet_build = bb_sync.BuildPacketToZmq(
            bb_params=self.bb_params,
            tcp_addr=self.tcp_addr)
        self.connect((self.mod_sync, 0), (self.packet_build, 0))

        # keeps the iq data flowing regardless of zmq situation
        #self.null_sink = blocks.null_sink(
        #    sizeof_stream_item=gr.sizeof_char)
        #self.connect((self.mod_sync, 0), (self.null_sink, 0))

        # debug sink; connect this to a flowgraph running the debug
        # viewer
        '''
        if True:
            self.zeromq_debug_sink = zeromq.push_sink(
                #gr.sizeof_gr_complex,
                gr.sizeof_char,
                1,
                zmqu.TCP_DEBUG,
                100,
                False,
                32768*8
            )
            self.connect((self.mod_sync, 0), (self.zeromq_debug_sink, 0))
        '''
