# This module takes an untagged byte stream and does the following:
#  - detects and tags the preamble
#  - extracts the payload based on the gnuradio packet structure
#  - packs the payload bits into bytes
#  - converts each packet's bytes to a message PDU
#  - sends this message out to a ZeroMQ sink for pickup by the main prog
#
# Input:
#   - synchronized bits (uchar stream from clock sync)
# Output:
#   - PDU sent via ZeroMQ

from gnuradio import gr
from gnuradio import blocks
from gnuradio import zeromq
from gnuradio import digital
import zmq_utils as zmqu


class BuildPacketToZmq(gr.hier_block2):

    def __init__(self,
                 bb_params):
        gr.hier_block2.__init__(
            self,
            "Build and Send Pkt",
            gr.io_signature(1, 1, gr.sizeof_char * 1),  # single in
            gr.io_signature(0, 0, 0) # output via zmq
        )

        # parameters
        self.bb_params = bb_params

        # variables
        self.tag_name = "packet_len"
        self.preamble_str = ""
        for bit in self.bb_params.preamble:
            if bit == 1:
                self.preamble_str = self.preamble_str + '1'
            else:
                self.preamble_str = self.preamble_str + '0'

        # blocks
        # detect and tag any preambles
        self.digital_correlate_access_code_xx_ts_0 = \
            digital.correlate_access_code_bb_ts(
                self.preamble_str,
                0,
                self.tag_name)
        self.connect((self,0),
                     (self.digital_correlate_access_code_xx_ts_0, 0))

        # pack the bits into bytes
        self.blocks_repack_bits_bb_0 = \
            blocks.repack_bits_bb(
                1,
                8,
                self.tag_name,
                False,
                gr.GR_MSB_FIRST)
        self.connect((self.digital_correlate_access_code_xx_ts_0, 0),
                     (self.blocks_repack_bits_bb_0, 0))

        # convert payloads to PDUs
        self.blocks_tagged_stream_to_pdu_0 = \
            blocks.tagged_stream_to_pdu(blocks.byte_t, 'packet_len')
        self.connect((self.blocks_repack_bits_bb_0, 0),
                     (self.blocks_tagged_stream_to_pdu_0, 0))

        # send PDU to zmq sink
        self.zeromq_push_msg_sink_0 = \
            zeromq.push_msg_sink(
                zmqu.TCP_RX,
                100)

