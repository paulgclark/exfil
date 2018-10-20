#!/usr/bin/python

# Contains the code for the host system. Calls gnuradio and zmq code
# from other modules.

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import tx_top
import rx_top


# define the host
class hostClass():
    def __init__(self, init_rf_params, init_bb_params, tcp_tx, verbose=False):
        # build flowgraph object with initial params
        self.fg_tx = tx_top.TxTop(init_rf_params, init_bb_params)
        # start the flowgraph
        self.fg_tx.start()

        # open zmq socket for payload xfr to flowgraph
        self.tx_zmq = zmu.ZmqPushMsgSocket(tcp_tx)

        self.downlink_rf_params = init_rf_params
        self.downlink_bb_params = init_bb_params
        self.uplink_rf_params = None
        self.uplink_bb_params = None
        self.verbose = verbose

    # update configuration for host->xfil connection
    def set_downlink_config(self, rf_params, bb_params):
        self.downlink_rf_params = rf_params
        self.downlink_bb_params = bb_params

    # set or update configuration for xfil->host connection
    def set_uplink_config(self, rf_params, bb_params):
        self.uplink_rf_params = rf_params
        self.uplink_bb_params = bb_params

    # send the current uplink parameters in byte form
    def send_uplink_config(self):
        cmd_bytes = self.uplink_rf_params.params_to_bytes()
        print cmd_bytes
        cmd_bytes += self.uplink_bb_params.params_to_bytes()
        print self.uplink_bb_params.params_to_bytes()
        self.send_bytes(cmd_bytes=cmd_bytes)

    def send_bytes(self, cmd_bytes):
        # add checksum to commands
        combo_bytes = cmd_bytes[:]
        combo_bytes.append(rfm.acs(cmd_bytes))
        self.tx_zmq.send_framed_bytes(
            preamble=self.downlink_bb_params.preamble_bytes,
            byte_list=combo_bytes,
            verbose=self.verbose)

    def shutdown(self):
        self.fg_tx.stop()

