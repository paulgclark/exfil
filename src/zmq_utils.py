# this module contains helper functions for the ZeroMQ API

import zmq
import array
import pmt
import time
import struct
import numpy as np

# the following tcp addresses are used by ZeroMQ pairs
# for connection between tx control code and host flowgraph
TCP_TX_HOST = "tcp://127.0.0.1:5555"
# for connection between rx control code and xfil flowgraph
TCP_RX_XFIL = "tcp://127.0.0.1:5556"
# for test mode connection between tx and rx flowgraphs (downlink)
TCP_TEST = "tcp://127.0.0.1:5557"
# for test mode connection between tx and rx flowgraphs (uplink)
TCP_TEST2 = "tcp://127.0.0.1:5561"
# for connection to a debug port for viewing in grc
TCP_DEBUG = "tcp://127.0.0.1:5558"
# for connection between tx control code and xfil flowgraph
TCP_TX_XFIL = "tcp://127.0.0.1:5559"
# # for connection between rx control code and xfil flowgraph
TCP_RX_HOST = "tcp://127.0.0.1:5560"

# this class just bundles together all the tcp addresses that a
# radio stack object will need for ZMQ sources/sinks
class TcpParams():
    def __init__(self, rx, tx, test_rx, test_tx, debug=None):
        self.rx = rx
        self.tx = tx
        self.test_rx = test_rx
        self.test_tx = test_tx
        self.debug = debug

tcp_params_host = TcpParams(rx=TCP_RX_HOST,
                            tx=TCP_TX_HOST,
                            test_rx=TCP_TEST2,
                            test_tx=TCP_TEST,
                            debug=None)
tcp_params_xfil = TcpParams(rx=TCP_RX_XFIL,
                            tx=TCP_TX_XFIL,
                            test_rx=TCP_TEST,
                            test_tx=TCP_TEST2,
                            debug=None)

# this class creates a pull socket for grabbing byte
# data from a flowgraph
class ZmqPullSocket():
    def __init__(self, tcp_str, verbose=0):
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.connect(tcp_str)

    def poll(self, type_str='f', verbose=0):
        raw_data = self.receiver.recv()
        a = array.array(type_str, raw_data)
        return a


# this class creates a pull socket for grabbing messages
# from a flowgraph
class ZmqPullMsgSocket():
    def __init__(self, tcp_str, verbose=False):
        if verbose:
            print "Opening PULL MSG socket at: " + tcp_str
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.connect(tcp_str)

    def poll_str(self, verbose=False):
        if verbose:
            print "Polling MSG socket..."
        raw_data = self.receiver.recv()
        return zmq_msg_payload_to_str(raw_data)

    def poll_bytes(self, verbose=False):
        if verbose:
            print "Polling MSG socket..."
        raw_data = self.receiver.recv()
        return zmq_msg_payload_to_bytes(raw_data)


# This function takes a raw message and extracts the payload as str
def zmq_msg_payload_to_str(raw_msg):
    msg = pmt.deserialize_str(raw_msg)
    cdr = pmt.cdr(msg)

    packet_len = pmt.length(cdr)
    cdr_str = pmt.serialize_str(cdr)
    output_str = cdr_str[-1*packet_len:]
    return output_str


# This function takes a raw message and extracts the payload as bytes
def zmq_msg_payload_to_bytes(raw_msg):
    msg = pmt.deserialize_str(raw_msg)
    cdr = pmt.cdr(msg)

    packet_len = pmt.length(cdr)
    cdr_str = pmt.serialize_str(cdr)
    output_str = cdr_str[-1*packet_len:]
    byte_list = list()
    for i in xrange(len(output_str)):
        byte_list.append(ord(output_str[i]))
    return byte_list


# this class creates a push socket for sending messages
# to a flowgraph as well as the methods required to send
# both byte and string data
class ZmqPushMsgSocket():
    def __init__(self, tcp_str, verbose=0):
        if verbose:
            print "Opening PUSH MSG socket at: " + tcp_str
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.bind(tcp_str)

    # sends raw bytes via ZMQ connection; this fn assumes that
    # the ZMQ source on the other side is expecting packed bytes
    # of type unsigned char
    def send_raw_bytes(self, byte_list, verbose=0):
        if verbose:
            print "Sending Raw Bytes:",
            print byte_list

        # get payload size
        payload_size = len(byte_list)
        # build an empty vector
        data = pmt.make_u8vector(payload_size, 0x00)
        # fill the vector with unsigned byte data to send
        for i in xrange(payload_size):
            pmt.u8vector_set(data, i, byte_list[i])
        # build the message, which is a pair consisting of
        # the message metadata (not needed here) and the
        # information we want to send (the vector)
        msg = pmt.cons(pmt.PMT_NIL, data)
        # the message must be serialized as a string so that
        # it's in the form the gnuradio source expects
        msg = pmt.serialize_str(msg)
        self.socket.send(msg)

    # Sends a message framed in the basic gnuradio format:
    #   - preamble
    #   - two bytes containing the payload length (MSB)
    #   - a second copy of the length byte pair
    #   - the payload
    #
    # Both the preamble and the byte_list must be lists of packed,
    # 8-bit values.
    def send_framed_bytes(self, preamble, byte_list, verbose=0):
        if verbose:
            print "Sending Framed Bytes:",
            print byte_list

        # get payload size
        payload_size = len(byte_list)

        # build the framed vector (starting/ending with some dead air)
        framed_list = 20*[0x00] + preamble
        framed_list.append(0x00)
        framed_list.append(payload_size)
        framed_list.append(0x00)
        framed_list.append(payload_size)
        framed_list += byte_list
        framed_list += 20*[0x00]

        # send it
        self.send_raw_bytes(framed_list, verbose)

    # converts the string to a byte list and sends it via
    # the preceding functions
    def send_framed_str(self, preamble, in_str, verbose=0):
        if verbose:
            print "Sending Framed String:",
            print in_str

        byte_list = bytearray(in_str)
        self.send_framed_bytes(preamble, byte_list, verbose)
