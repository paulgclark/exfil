# this module contains helper functions for the ZeroMQ API

import zmq
import array
import pmt
import time
import struct
import numpy as np

# the following tcp addresses are used by ZeroMQ pairs
## for test mode connection between tx and rx flowgraphs
TCP_TEST = "tcp://127.0.0.1:5559"
## for connection between tx control code and tx flowgraph
TCP_TX = "tcp://127.0.0.1:5555"
## for connection between rx control code and rx flowgraph
TCP_RX = "tcp://127.0.0.1:5558"

# this class creates a pull socket for grabbing float
# data from a flowgraph
class zmq_pull_socket():
    def __init__(self, tcp_str, verbose=0):
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.connect(tcp_str)


    def poll(self, type_str='f', verbose=0):
        raw_data = self.receiver.recv()
        a = array.array(type_str, raw_data)
        return a

    # incomplete attempt to optimize data flow by
    # sending bytes instead of floats; flowgraph
    # changes needed to support this, as well
    # as all downstream code reworked to use
    # bytes
    def poll_short(self, type_str='h', verbose=0):
        raw_data = self.receiver.recv()
        a = array.array(type_str, raw_data)
        npa_s = np.asarray(a)
        npa_f = npa_s.astype(float)
        npa_f *= (1.0/10000.0)

        #fmt = "<%dI" % (len(raw_data) //4)
        #a = list(struct.unpack(fmt, raw_data))
        return list(npa_f)


# this class creates a pull socket for grabbing messages
# from a flowgraph
class zmq_pull_msg_socket():

    def __init__(self, tcp_str, verbose=0):
        if verbose:
            print "Opening MSG socket at: " + tcp_str
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.connect(tcp_str)


    def poll_str(self, verbose=0):
        if verbose:
            print "Polling MSG socket..."
        raw_data = self.receiver.recv()
        return zmq_msg_payload_to_str(raw_data)


    def poll_bytes(self, verbose=0):
        if verbose:
            print "Polling MSG socket..."
        raw_data = self.receiver.recv()
        return zmq_msg_payload_to_bytes(raw_data)


# This function takes a raw message and extracts the payload as str
def zmq_msg_payload_to_str(raw_msg):
    print "Entered zmq_msg_payload"
    msg = pmt.deserialize_str(raw_msg)
    cdr = pmt.cdr(msg)

    packet_len = pmt.length(cdr)
    cdr_str = pmt.serialize_str(cdr)
    output_str = cdr_str[-1*packet_len:]
    return output_str


# This function takes a raw message and extracts the payload as bytes
def zmq_msg_payload_to_bytes(raw_msg):
    print "Entered zmq_msg_payload"
    msg = pmt.deserialize_str(raw_msg)
    cdr = pmt.cdr(msg)

    packet_len = pmt.length(cdr)
    cdr_str = pmt.serialize_str(cdr)
    output_str = cdr_str[-1*packet_len:]
    byte_list = list()
    for i in xrange(len(output_str)):
        byte_list.append(ord(output_str[i]))
    return byte_list



def zmq_send_str(in_str, s):
    # convert string to byte array
    in_vec = bytearray(in_str)
    # then treat like a normal byte list
    # zmq_send_vec(in_vec, s)
    zmq_frame_and_send_vec(in_vec, s)

def zmq_send_vec(in_list, s):
    packet_size = len(in_list)
    data = pmt.make_u8vector(packet_size, 0x00)
    for i in xrange(packet_size):
        pmt.u8vector_set(data, i, in_list[i])
    meta = pmt.PMT_NIL
    msg = pmt.cons(pmt.PMT_NIL, data)
    msg = pmt.serialize_str(msg)
    s.send(msg)

def zmq_frame_and_send_vec(in_list, s):
    # build data vector
    payload_size = len(in_list)

    new_list = [] + preamble_bytes
    new_list.append(0x00)
    new_list.append(payload_size)
    new_list.append(0x00)
    new_list.append(payload_size)
    new_list += in_list

    packet_size = len(new_list)
    data = pmt.make_u8vector(packet_size, 0x00)
    for i in xrange(packet_size):
        pmt.u8vector_set(data, i, new_list[i])
    meta = pmt.PMT_NIL
    msg = pmt.cons(pmt.PMT_NIL, data)
    msg = pmt.serialize_str(msg)
    s.send(msg)


