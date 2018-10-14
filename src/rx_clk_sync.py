# This module contains a hier block that bundles the functions
# required to convert an oversampled baseband signal to a
# clock-synchronized baseband signal. Most demodulators contain
# this function, so this block will likely only be used with the
# OOK demodulator.
#
# Input:
#   - oversampled baseband date; a binary-valued unsigned char
# Output:
#   - clock synchronized baseband data

from gnuradio import gr
from gnuradio import blocks
from gnuradio import digital
from gnuradio.filter import firdes

class rx_clk_sync(gr.hier_block2):

    def __init__(self,
                 bb_params,
                 working_samp_rate):
        gr.hier_block2.__init__(
            self,
            "RX Clock Sync",
            gr.io_signature(1, 1, gr.sizeof_char * 1),  # single in
            gr.io_signature(1, 1, gr.sizeof_char * 1)  # single out
        )

        # parameters
        self.bb_params = bb_params
        self.working_samp_rate = working_samp_rate

        # variables
        self.nfilts = 32
        self.sps = int(self.working_samp_rate * bb_params.symbol_time)
        self.rrc_taps = firdes.root_raised_cosine(
            self.nfilts,
            self.nfilts,
            1.0/float(self.sps),
            0.35,
            11*self.sps*self.nfilts)

        # convert to float and shift down to center around zero
        self.blocks_uchar_to_float_0 = blocks.uchar_to_float()
        self.connect((self,0), (self.blocks_uchar_to_float_0, 0))
        self.blocks_add_const_vxx_0_0 = blocks.add_const_vff((-0.5,))
        self.connect((self.blocks_uchar_to_float_0, 0),
                     (self.blocks_add_const_vxx_0_0, 0))

        # clock sync block
        self.digital_pfb_clock_sync_xxx_0 = digital.pfb_clock_sync_fff(
            self.sps,
            6.28 / 100.0,
            (self.rrc_taps),
            self.nfilts,
            self.nfilts/2,
            1.5,
            1)
        self.connect((self.blocks_add_const_vxx_0_0, 0),
                     (self.digital_pfb_clock_sync_xxx_0, 0))

        # convert back to uchar
        self.digital_binary_slicer_fb_0_0 = digital.binary_slicer_fb()
        self.connect((self.digital_pfb_clock_sync_xxx_0, 0),
                     (self.digital_binary_slicer_fb_0_0, 0))

        # connect hier block output
        self.connect((self.digital_binary_slicer_fb_0_0, 0),
                     (self, 0))
