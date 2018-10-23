# This module contains a hier block for modulating On-Off-Keying (OOK)
# signals. It is assumed that the input baseband signal consists of
# packed bytes and that the framing has been added.
#
# The output of this block typically feeds a tuner.
#
# Input:
#   - baseband data (including framing) as packed bytes
# Output:
#   - IQ data containing modulated signal

from gnuradio import gr
from gnuradio import blocks
from gnuradio import analog
from gnuradio import digital

class TxOokMod(gr.hier_block2):

    def __init__(self,
                 rf_params,
                 bb_params):
        gr.hier_block2.__init__(
            self,
            "TX Mod Block",
            gr.io_signature(1, 1, gr.sizeof_char*1),       # single in
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1)  # single out
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.symbol_time = bb_params.symbol_time

        ##################################################
        # Variables
        ##################################################
        self.sps = int(rf_params.samp_rate*bb_params.symbol_time)

        ##################################################
        # Blocks
        ##################################################
        # convert to unpacked
        self.blocks_packed_to_unpacked_xx_0 = \
            blocks.packed_to_unpacked_bb(1, gr.GR_MSB_FIRST)
        self.connect((self,0), (self.blocks_packed_to_unpacked_xx_0, 0))

        # convert to float
        self.blocks_uchar_to_float_0 = blocks.uchar_to_float()
        self.connect((self.blocks_packed_to_unpacked_xx_0, 0),
                     (self.blocks_uchar_to_float_0, 0))

        # stretch out waveform to match eventual samp_rate
        self.blocks_repeat_0 = blocks.repeat(gr.sizeof_float * 1, self.sps)
        self.connect((self.blocks_uchar_to_float_0, 0),
                     (self.blocks_repeat_0, 0))

        # modulate by conversion to complex stream with:
        # - real portion equal to baseband (1 or 0)
        # - imaginary portion equal to 0
        self.analog_const_source_x_0 = \
            analog.sig_source_f(0, analog.GR_CONST_WAVE, 0, 0, 0)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.connect((self.analog_const_source_x_0, 0),
                     (self.blocks_float_to_complex_0, 1))
        self.connect((self.blocks_repeat_0, 0),
                     (self.blocks_float_to_complex_0, 0))

        # send to hier block output
        self.connect((self.blocks_float_to_complex_0, 0), (self, 0))


class TxGmskMod(gr.hier_block2):
    def __init__(self, rf_params, bb_params):
        gr.hier_block2.__init__(
            self,
            "TX Mod Block",
            gr.io_signature(1, 1, gr.sizeof_char * 1),
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1)
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.samp_rate = rf_params.samp_rate
        self.symbol_time = bb_params.symbol_time

        ##################################################
        # Variables
        ##################################################
        self.sps = int(self.samp_rate*self.symbol_time)

        ##################################################
        # Blocks
        ##################################################
        # just the modulator
        self.digital_gmsk_mod_0 = digital.gmsk_mod(
            samples_per_symbol=self.sps,
            bt=0.35,
            verbose=False,
            log=False,
        )
        self.connect((self,0), (self.digital_gmsk_mod_0, 0))

        # send to hier block output
        self.connect((self.digital_gmsk_mod_0, 0), (self, 0))


class TxGfskMod(gr.hier_block2):
    def __init__(self, rf_params, bb_params):
        gr.hier_block2.__init__(
            self,
            "TX Mod Block",
            gr.io_signature(1, 1, gr.sizeof_char * 1),
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1)
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.samp_rate = rf_params.samp_rate
        self.fsk_dev = rf_params.fsk_dev
        self.symbol_time = bb_params.symbol_time

        ##################################################
        # Variables
        ##################################################
        self.sps = int(self.samp_rate*self.symbol_time)
        self.sensitivity = 2*3.1415*self.fsk_dev/self.samp_rate

        ##################################################
        # Blocks
        ##################################################
        # just the modulator
        self.digital_gfsk_mod_0 = digital.gfsk_mod(
            samples_per_symbol=self.sps,
            sensitivity=self.sensitivity,
            bt=0.35,
            verbose=False,
            log=False,
        )
        self.connect((self,0), (self.digital_gfsk_mod_0, 0))

        # send to hier block output
        self.connect((self.digital_gfsk_mod_0, 0), (self, 0))


class TxPskMod(gr.hier_block2):
    def __init__(self, rf_params, bb_params):
        gr.hier_block2.__init__(
            self,
            "TX Mod Block",
            gr.io_signature(1, 1, gr.sizeof_char * 1),
            gr.io_signature(1, 1, gr.sizeof_gr_complex * 1)
        )

        ##################################################
        # Parameters
        ##################################################
        # ADD VALIDITY CHECKS TO EACH OF THESE
        self.samp_rate = rf_params.samp_rate
        self.psk_const_num = rf_params.psk_const_num
        self.symbol_time = bb_params.symbol_time

        ##################################################
        # Variables
        ##################################################
        self.sps = int(self.samp_rate*self.symbol_time)

        ##################################################
        # Blocks
        ##################################################
        # just the modulator
        self.digital_psk_mod_0 = digital.psk.psk_mod(
            constellation_points=self.psk_const_num,
            mod_code="gray",
            differential=True,
            samples_per_symbol=self.sps,
            excess_bw=0.35,
            verbose=False,
            log=False,
        )
        self.connect((self,0), (self.digital_psk_mod_0, 0))

        # send to hier block output
        self.connect((self.digital_psk_mod_0, 0), (self, 0))