# This module provides baseband input to the transmitter by
# means of a ZMQ pipe.
# Input:
#   - ZMQ message, no streaming inputs
# Output:
#   - Packed, framed baseband bytes (unsigned char)

import zmq_utils as zmq
from gnuradio import gr
from gnuradio import blocks
from gnuradio import zeromq


class TxSource(gr.hier_block2):

    def __init__(self,
                 rf_params,
                 tcp_addr):
        gr.hier_block2.__init__(
            self,
            "TX Source Block",
            gr.io_signature(0, 0, 0),  # no inputs
            gr.io_signature(1, 1, gr.sizeof_char * 1)  # single out
        )

        # parameters
        self.rf_params = rf_params
        self.tcp_addr = tcp_addr

        # instantiate the zmq source
        self.bb_src = zeromq.pull_msg_source(
                self.tcp_addr,
                100)

        # convert the message PDU to a stream with tags
        self.pdu_to_ts = blocks.pdu_to_tagged_stream(
            blocks.byte_t,
            'len_key')
        self.msg_connect(
            (self.bb_src, 'out'),
            (self.pdu_to_ts, 'pdus'))
        self.connect((self.pdu_to_ts, 0), (self, 0))
