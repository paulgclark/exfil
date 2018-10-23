# This module instantiates one of a number of possible
# sources of IQ data.

import rf_mgt as rfm
import zmq_utils as zmqu
from gnuradio import gr
from gnuradio import uhd
try:
    import osmosdr
except:
    print "Warning! No osmocom support detected. HackRF not available."
from gnuradio import zeromq

class rx_source(gr.hier_block2):

    def __init__(self,
                 rf_params,
                 tcp_test,
                 sdr_sel):
        gr.hier_block2.__init__(
            self,
            "RX Source Block",
            gr.io_signature(0, 0, 0), # no inputs
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1)  # single out
        )

        # parameters
        self.rf_params = rf_params
        self.tcp_test = tcp_test
        self.sdr_sel = sdr_sel

        # instantiate the IQ source
        ## use the ZeroMQ Pull Source for loopback connection to TX
        if self.sdr_sel == rfm.HW_TEST:
            self.src = zeromq.pull_source(
                gr.sizeof_gr_complex,
                1,
                self.tcp_test,
                100,
                False,
                -1)

        elif self.sdr_sel == rfm.HW_UHD:
            self.src = uhd.usrp_source(
                ",".join(("", "")),
                uhd.stream_args(
                        cpu_format="fc32",
                        channels=range(1),
                ),
            )
            self.src.set_antenna('TX/RX', 0)
            self.src.set_center_freq(rf_params.center_freq, 0)
            self.src.set_gain(rf_params.rx_gain, 0)
            self.src.set_samp_rate(rf_params.samp_rate)

        elif self.sdr_sel == rfm.HW_HACKRF:
            self.src = osmosdr.source(args="numchan=" + str(1) + " " + 'hackrf=0')
            self.src.set_sample_rate(self.rf_params.samp_rate)
            self.src.set_center_freq(self.rf_params.center_freq, 0)
            self.src.set_freq_corr(0, 0)
            self.src.set_dc_offset_mode(0, 0)
            self.src.set_iq_balance_mode(0, 0)
            self.src.set_gain_mode(False, 0)
            # mapping single value gain to hackrf's 3 stages as follows:
            #  Gain -> RF    IF     BB
            #   0      0     0      0
            #  20      0     8      8
            #  30      0    16     16
            #  40     14    16     16
            #  60     14    24     24
            #  80     14    32     32
            if   rf_params.rx_gain ==  0: rfg, ifg, bbg =  0,  0,  0
            elif rf_params.rx_gain == 20: rfg, ifg, bbg =  0,  0,  0
            elif rf_params.rx_gain == 30: rfg, ifg, bbg =  0, 16, 16
            elif rf_params.rx_gain == 40: rfg, ifg, bbg =  0, 24, 24
            elif rf_params.rx_gain == 60: rfg, ifg, bbg = 14, 24, 24
            elif rf_params.rx_gain == 80: rfg, ifg, bbg = 14, 32, 32
            else:                         rfg, ifg, bbg =  0, 16, 16
            self.src.set_gain(rfg, 0)
            self.src.set_if_gain(ifg, 0)
            self.src.set_bb_gain(bbg, 0)
            self.src.set_antenna('', 0)
            self.src.set_bandwidth(0, 0)

        self.connect((self.src, 0), (self,0))
