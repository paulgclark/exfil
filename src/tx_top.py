# This module contains the top level transmitter block
#
# Input:
#   - transmit payloads sent into the flowgraph as message PDUs
# Output:
#   - IQ data sent to an SDR (or ZMQ sink if in test mode)

import zmq_utils as zmqu
import rf_mgt as rfm
import tx_source
import tx_ook_mod
import tx_tuner
import tx_out

from gnuradio import gr
from gnuradio import zeromq
from gnuradio import blocks


class TxTop(gr.top_block):

    def __init__(self,
                 rf_params,
                 bb_params,
                 tcp_addr,
                 tcp_test):
        gr.top_block.__init__(self, "tx_top")

        # parameters
        self.rf_params = rf_params
        self.bb_params = bb_params
        self.tcp_addr = tcp_addr
        self.tcp_addr_test = tcp_test

        # variables
        self.samp_rate = rf_params.samp_rate
        self.center_freq = rf_params.center_freq
        self.working_samp_rate = 10/bb_params.symbol_time

        # baseband source
        self.bb_src = tx_source.TxSource(rf_params=self.rf_params,
                                         tcp_addr=self.tcp_addr)

        # modulation
        if rf_params.mod_scheme == rfm.MOD_OOK:
            self.mod = tx_ook_mod.TxOokMod(rf_params=self.rf_params,
                                           bb_params=self.bb_params)
            self.connect((self.bb_src, 0), (self.mod, 0))
        #elif rf_params.mod_scheme == rfm.MOD_FSK
        #    self.mod_sync = rx_fsk_demod.rx_fsk_demod(rf_params)
        #    self.connect((self.tuner, 0), (self.mod_only, 0))

        # tuner
        self.tuner = tx_tuner.TxTuner(rf_params=self.rf_params)
        self.connect((self.mod, 0), (self.tuner, 0))

        # transmit output
        self.tx_out = tx_out.TxOut(rf_params=self.rf_params,
                                   tcp_test=self.tcp_addr_test)
        self.connect((self.tuner, 0), (self.tx_out))

        # keeps the iq data flowing regardless of zmq situation
        #self.null_sink = blocks.null_sink(
        #    sizeof_stream_item=gr.sizeof_gr_complex)
        #self.connect((self.mod, 0), (self.null_sink, 0))

        # debug sink; connect this to a flowgraph running the debug
        # viewer
        if False:
            self.zeromq_debug_sink = zeromq.push_sink(
                gr.sizeof_gr_complex,
                #gr.sizeof_char,
                1,
                zmqu.TCP_DEBUG,
                100,
                False,
                32768*8
            )
            self.connect((self.tuner, 0), (self.zeromq_debug_sink, 0))
