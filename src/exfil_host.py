#!/usr/bin/python
#import zmq_utils
import zmq
import sys
import time
import pmt
import numpy as np
import pylab

tcp_str = "tcp://127.0.0.1:5555"
preamble_bytes = [0, 0, 0, 0, 0, 0, 0, 0, 85, 85]




if __name__ == "__main__":
    # create socket for zmq
    context = zmq.Context.instance()
    zmq_socket = context.socket(zmq.PUSH)
    zmq_socket.bind(tcp_str)

    if True:
        for i in xrange(10):
            tx_pkt = [0,0,85,85,0,13,0,13,255,254,253,252,251,250,0,1,2,3,4,5,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            time.sleep(1)
            zmq_send_vec(tx_pkt, zmq_socket)
            time.sleep(1)
        exit(0)

    # sends a series of messages, each containing a vector PDU
    if True:
        for i in xrange(100):
            zmq_send_vec([0,1,2,3,4], zmq_socket)
            time.sleep(1)
            zmq_send_vec([8,14,22,33,44], zmq_socket)
            time.sleep(1)
            zmq_send_vec([255,254], zmq_socket)
        exit(0)

    # sends a series of messages, each containing a string PDU
    if False:
        zmq_send_str("The quick brown fox", zmq_socket)
        time.sleep(1)
        zmq_send_str("jumped over the lazy dog", zmq_socket)
        time.sleep(1)
        zmq_send_str("and then the wolves arrived...", zmq_socket)
        exit(0)

    # sends a single string PDU that you type in
    while True:

        # wait until key pressed
        user_text = raw_input("Hit ENTER to send a packet (or \'q\' to quit): ")
        if user_text == "q":
          zmq_socket.close()
          exit(0)

        zmq_send_str(user_text, zmq_socket)
