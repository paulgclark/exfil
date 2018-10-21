#!/usr/bin/python

# The purpose of this file is to test the zmq message
# functions; The flowgraph ./grc/zmq_tx_unit.grc can
# be used to manually view the output (switch the Message
# Debug Sink connection from the "print_pdu" to the
# "print" inputs to view the bytes and the strings
# respectively

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu

PREAMBLE = [0x55, 0x55]
raw_bytes = [0xC0, 0x3F, 0xEB, 0x00, 0x13]

if __name__ == "__main__":
    # setup the zmq socket
    msg_push = zmu.ZmqPushMsgSocket(zmu.TCP_TX_HOST)

    # send string and byte data
    while True:
        time.sleep(1)
        msg_push.send_framed_bytes(preamble=PREAMBLE,
                                 byte_list=raw_bytes)
        time.sleep(1)
        msg_push.send_framed_str(preamble=PREAMBLE,
                               in_str="Testing now...")
