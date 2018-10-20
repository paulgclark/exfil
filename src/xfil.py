#!/usr/bin/python

# Contains the code for the xfil box. Calls gnuradio and zmq code
# from other modules.

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import tx_top
import rx_top


# define the exfil radio
class xfilClass():
    def __init__(self, init_rf_params, init_bb_params, tcp_rx):
        # build flowgraph object with initial params
        self.fg_rx = rx_top.RxTop(init_rf_params, init_bb_params)
        # start the flowgraph
        self.fg_rx.start()

        # open zmq socket for payload xfr from flowgraph
        self.rx_zmq = zmu.zmq_pull_msg_socket(tcp_rx)

        self.rf_params = init_rf_params
        self.bb_params = init_bb_params
        self.verbose = False

    def shutdown(self):
        self.fg_rx.stop()

    def recv_command(self, verbose=False):
        # wait for valid transmission
        raw_data = self.rx_zmq.poll_bytes(self.verbose)

        # checksum
        cs_computed = rfm.acs(raw_data[:-1])
        if verbose:
            print "Raw command bytes:",
            print raw_data
            print "Checksum: {}".format(cs_computed)

        # if we have a valid command, reconfigure the flowgraph
        if cs_computed == raw_data[-1]:
            return raw_data[:-1]
        else:
            return []
