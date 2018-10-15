# This modules provides transmit-side tuning via complex
# multiplication.
# Input:
#   - Oversampled, modulated IQ data centered at DC
# Output:
#   - Tuned and transmit-ready IQ data

import zmq_utils as zmq
import rf_mgt as rfm
from gnuradio import gr
from gnuradio import analog
from gnuradio import blocks


class TxTuner(gr.hier_block2):

    def __init__(self,
                 rf_params):
        gr.hier_block2.__init__(
            self,
            "TX Tuner Block",
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1),  # single in
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1)  # single out
        )

        # parameters
        self.rf_params = rf_params

        # variables
        self.samp_rate = rf_params.samp_rate
        self.center_freq = rf_params.center_freq
        self.freq = rf_params.freq

        # this is the sinusoid we'll use to multiply for tuning
        self.analog_sig_source_x_0 = analog.sig_source_c(
            self.samp_rate,
            analog.GR_COS_WAVE,
            self.freq - self.center_freq,
            1,  # amplitude of waveform
            0)

        # this is the complex multiply that does the shifting
        self.blocks_multiply_xx_0 = blocks.multiply_vcc(1)
        self.connect((self, 0), (self.blocks_multiply_xx_0))
        self.connect((self.analog_sig_source_x_0, 0),
                     (self.blocks_multiply_xx_0, 1))

        # send out of hier block
        self.connect((self.blocks_multiply_xx_0, 0), (self, 0))



