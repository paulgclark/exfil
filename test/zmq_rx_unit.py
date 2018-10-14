#!/usr/bin/python

# The purpose of this file is to test the zmq message
# functions

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
from gnuradio import gr
from gnuradio import blocks
from gnuradio import digital
from gnuradio import zeromq


# define a simple flowgraph that produces a message containing
# a four byte payload: [80d, 73d, 80d, 73d] == ['P', 'I', 'P', 'I']
class TestFlowgraph(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self, "ZMQ RX Test")

        ##################################################
        # Variables
        ##################################################
        self.tcp_addr_msg_out = zmu.TCP_RX
        self.samp_rate = samp_rate = 1e3
        self.preamble = (85,85,0,6,0,6,80,73,80,73,70,90,0,0,0,0,0,0,0)

        ##################################################
        # Blocks
        ##################################################
        self.zeromq_push_msg_sink_0 = \
            zeromq.push_msg_sink(self.tcp_addr_msg_out, 100)
        self.digital_correlate_access_code_xx_ts_0 = \
            digital.correlate_access_code_bb_ts(
                '0101010101010101',
                0,
                'packet_len')
        self.blocks_vector_source_x_0 = \
            blocks.vector_source_b(
                self.preamble, True, 1, [])
        self.blocks_throttle_0 = \
            blocks.throttle(gr.sizeof_char*1, samp_rate,True)
        self.blocks_tagged_stream_to_pdu_0 = \
            blocks.tagged_stream_to_pdu(blocks.byte_t, 'packet_len')
        self.blocks_repack_bits_bb_0 = \
            blocks.repack_bits_bb(1, 8, 'packet_len', False, gr.GR_MSB_FIRST)
        self.blocks_packed_to_unpacked_xx_0 = \
            blocks.packed_to_unpacked_bb(1, gr.GR_MSB_FIRST)

        ##################################################
        # Connections
        ##################################################
        self.msg_connect(
            (self.blocks_tagged_stream_to_pdu_0, 'pdus'),
            (self.zeromq_push_msg_sink_0, 'in'))
        self.connect(
            (self.blocks_packed_to_unpacked_xx_0, 0),
            (self.digital_correlate_access_code_xx_ts_0, 0))
        self.connect(
            (self.blocks_repack_bits_bb_0, 0),
            (self.blocks_tagged_stream_to_pdu_0, 0))
        self.connect(
            (self.blocks_throttle_0, 0),
            (self.blocks_packed_to_unpacked_xx_0, 0))
        self.connect(
            (self.blocks_vector_source_x_0, 0),
            (self.blocks_throttle_0, 0))
        self.connect(
            (self.digital_correlate_access_code_xx_ts_0, 0),
            (self.blocks_repack_bits_bb_0, 0))


if __name__ == "__main__":
    # instance and start the flowgraph
    fg = TestFlowgraph()
    fg.start()

    # setup the zmq socket
    socket = zmu.zmq_pull_msg_socket(zmu.TCP_RX)

    # poll the socket and acquire the data
    for _ in xrange(3):
        time.sleep(1)
        read_str = socket.poll_str()
        print read_str
        data = socket.poll_bytes()
        print data




