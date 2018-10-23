# This module contains a hier block for demodulating an On-Off-Keying (OOK)
# signal. It is assumed that the input IQ signal is tuned and filtered.
# The output of this block typically feeds a synchronizer and deframer.
#
# This block optionally supports an AGC via a running computation of
# the signal energy which feeds a divide block. This structure attempts
# to convert the amplitude to roughly 1-1.5, allowing the threshold
# to be generally effective at 0.5.
#
# Input:
#   - tuned, filtered and decimated IQ data
# Output:
#   - demodulated, oversampled baseband data

from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio import digital
import rf_mgt as rfm

class RxOokDemod(gr.hier_block2):

    def __init__(self,
                 rf_params,
                 bb_params):
        gr.hier_block2.__init__(
            self,
            "RX Demod Block",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1), # single in
            gr.io_signature(1, 1, gr.sizeof_char*1)       # single out
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.agc_enable = rf_params.agc_enable
        if self.agc_enable:
            self.threshold = 0.5
        else:
            self.threshold = rf_params.threshold
        self.symbol_time = bb_params.symbol_time

        ##################################################
        # Variables
        ##################################################


        ##################################################
        # Blocks
        ##################################################
        if self.agc_enable:
            # the following blocks provide the AGC
            self.blocks_rms_xx_0 = blocks.rms_cf(self.symbol_time / 10)
            self.connect((self, 0), (self.blocks_rms_xx_0, 0))

            self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vff((2,))
            self.connect((self.blocks_rms_xx_0, 0), (self.blocks_multiply_const_vxx_0, 0))

            self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
            self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_float_to_complex_0, 0))

            self.blocks_divide_xx_0 = blocks.divide_cc(1)
            self.connect((self, 0), (self.blocks_divide_xx_0, 0))
            self.connect((self.blocks_float_to_complex_0, 0), (self.blocks_divide_xx_0, 1))

        # demodulation and cleanup
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(1)
        if self.agc_enable:
            # get input from agc output
            self.connect((self.blocks_divide_xx_0, 0), (self.blocks_complex_to_mag_0, 0))
        else:
            # connect input directly to input
            self.connect((self, 0), (self.blocks_complex_to_mag_0))


        self.blocks_add_const_vxx_0 = blocks.add_const_vff((-1 *  self.threshold,))
        self.connect((self.blocks_complex_to_mag_0, 0), (self.blocks_add_const_vxx_0, 0))

        self.digital_binary_slicer_fb_0 = digital.binary_slicer_fb()
        self.connect((self.blocks_add_const_vxx_0, 0), (self.digital_binary_slicer_fb_0, 0))

        # output from block
        self.connect((self.digital_binary_slicer_fb_0, 0), (self, 0))


    ######################################################
    # don't need all of the helper functions, this flowgraph
    # will be stopped and recreated with new parameters;
    def get_threshold(self):
        return self.threshold

    def set_threshold(self, threshold):
        self.threshold = threshold


class RxGmskDemod(gr.hier_block2):

    def __init__(self,
                 bb_params,
                 working_samp_rate):
        gr.hier_block2.__init__(
            self,
            "RX Demod Block",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1), # single in
            gr.io_signature(1, 1, gr.sizeof_char*1)       # single out
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.symbol_time = bb_params.symbol_time
        self.working_samp_rate = working_samp_rate

        ##################################################
        # Variables
        ##################################################
        self.sps = int(self.symbol_time * self.working_samp_rate)

        ##################################################
        # Blocks
        ##################################################
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc(
            rfm.PWR_SQUELCH_DB,
            1e-4,
            0,
            False)
        self.connect((self, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.digital_gmsk_demod_0 = digital.gmsk_demod(
            samples_per_symbol=self.sps,
            gain_mu=0.175,
            mu=0.5,
            omega_relative_limit=0.005,
            freq_error=0.0,
            verbose=False,
            log=False,
        )
        self.connect((self.analog_pwr_squelch_xx_0, 0),
                     (self.digital_gmsk_demod_0, 0))

        # output from block
        self.connect((self.digital_gmsk_demod_0, 0), (self, 0))


class RxGfskDemod(gr.hier_block2):

    def __init__(self,
                 rf_params,
                 bb_params,
                 working_samp_rate):
        gr.hier_block2.__init__(
            self,
            "RX Demod Block",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1), # single in
            gr.io_signature(1, 1, gr.sizeof_char*1)       # single out
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.symbol_time = bb_params.symbol_time
        self.working_samp_rate = working_samp_rate
        self.fsk_dev = rf_params.fsk_dev

        ##################################################
        # Variables
        ##################################################
        self.sps = int(self.symbol_time * self.working_samp_rate)
        self.sensitivity = 2 * 3.1415 * self.fsk_dev / self.working_samp_rate

        ##################################################
        # Blocks
        ##################################################
        self.analog_pwr_squelch_xx_0 = analog.pwr_squelch_cc(
            rfm.PWR_SQUELCH_DB,
            1e-4,
            0,
            False)
        self.connect((self, 0), (self.analog_pwr_squelch_xx_0, 0))
        self.digital_gfsk_demod_0 = digital.gfsk_demod(
            samples_per_symbol=self.sps,
            sensitivity=self.sensitivity,
            gain_mu=0.175,
            mu=0.5,
            omega_relative_limit=0.005,
            freq_error=0.0,
            verbose=False,
            log=False,
        )
        self.connect((self.analog_pwr_squelch_xx_0, 0),
                     (self.digital_gfsk_demod_0, 0))

        # output from block
        self.connect((self.digital_gfsk_demod_0, 0), (self, 0))


class RxPskDemod(gr.hier_block2):

    def __init__(self,
                 rf_params,
                 bb_params,
                 working_samp_rate):
        gr.hier_block2.__init__(
            self,
            "RX Demod Block",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1), # single in
            gr.io_signature(1, 1, gr.sizeof_char*1)       # single out
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.psk_const_num = rf_params.psk_const_num
        self.symbol_time = bb_params.symbol_time
        self.working_samp_rate = working_samp_rate

        ##################################################
        # Variables
        ##################################################
        self.sps = int(self.symbol_time * self.working_samp_rate)

        ##################################################
        # Blocks
        ##################################################
        self.digital_psk_demod_0 = digital.psk.psk_demod(
            constellation_points=self.psk_const_num,
            differential=True,
            samples_per_symbol=self.sps,
            excess_bw=0.35,
            phase_bw=6.28 / 100.0,
            timing_bw=6.28 / 100.0,
            mod_code="gray",
            verbose=False,
            log=False,
        )
        self.connect((self, 0), (self.digital_psk_demod_0, 0))

        # output from block
        self.connect((self.digital_psk_demod_0, 0), (self, 0))

