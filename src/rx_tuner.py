# This module contains hier blocks for general-purpose tuning base on the
# gnuradio API. It is intended for use with companion blocks that perform
# demodulation, deframing and other functions.

# ADD THIS TO GLOBAL RF FILE (move up one level)
#SDR_SEL_TEST = 0
#SDR_SEL_UHD = 1
#SDR_SEL_HACKRF = 2
#SDR_SEL_LIME = 3
#SDR_SEL_LIME_MINI = 4

from gnuradio import gr
from gnuradio import filter
from gnuradio.filter import firdes

class RxTuner(gr.hier_block2):

    def __init__(self,
                 rf_params,
                 working_samp_rate
                 ):
        gr.hier_block2.__init__(
            self,
            "RX Tuner Block",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),  # single in
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1)   # single out
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.samp_rate = rf_params.samp_rate
        self.working_samp_rate = working_samp_rate
        self.center_freq = rf_params.center_freq
        self.freq = rf_params.freq
        self.channel_width = rf_params.channel_width
        self.freq_offset_corr = rf_params.freq_offset_corr
        if rf_params.transition_width == 0:
            self.transition_width = rf_params.channel_width/5
        else:
            self.transition_width = rf_params.transition_width

        ##################################################
        # Variables
        ##################################################
        self.decimation = int(self.samp_rate/self.working_samp_rate)
        self.filter_taps = firdes.low_pass(1,
                                           self.samp_rate,
                                           self.channel_width/2,
                                           self.transition_width)

        ##################################################
        # Blocks
        ##################################################
        self.xlating_fir = filter.freq_xlating_fir_filter_ccc(
            self.decimation,
            self.filter_taps,
            self.freq-self.center_freq-self.freq_offset_corr,
            self.samp_rate
        )

        ##################################################
        # Connections
        ##################################################
        self.connect((self.xlating_fir, 0), (self, 0))
        self.connect((self, 0), (self.xlating_fir, 0))


    ######################################################
    # don't need all of the helper functions, this flowgraph
    # will be stopped and recreated with new parameters;
    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
