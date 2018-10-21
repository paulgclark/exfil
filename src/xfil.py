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
    def __init__(self, init_rf_params, init_bb_params, tcp_rx, tcp_tx):
        # build flowgraph object with initial params
        self.fg_rx = rx_top.RxTop(init_rf_params, init_bb_params, tcp_rx, zmu.TCP_TEST)
        # start the flowgraph
        self.fg_rx.start()

        # open zmq socket for payload xfr from rx flowgraph
        self.rx_zmq = zmu.ZmqPullMsgSocket(tcp_rx)

        # instance a socket for sending tx data to tx flowgraph
        self.tx_zmq = zmu.ZmqPushMsgSocket(tcp_tx)

        self.downlink_rf_params = init_rf_params
        self.downlink_bb_params = init_bb_params
        self.uplink_rf_params = None
        self.uplink_bb_params = None
        self.tcp_rx = tcp_rx
        self.tcp_tx = tcp_tx
        self.verbose = False

        self.cmd_count = 0

    # update configuration for host->xfil connection
    def set_downlink_config(self, rf_params, bb_params):
        self.downlink_rf_params = rf_params
        self.downlink_bb_params = bb_params

    # set or update configuration for xfil->host connection
    def set_uplink_config(self, rf_params, bb_params):
        self.uplink_rf_params = rf_params
        self.uplink_bb_params = bb_params

    # waits until receiving data, then checks the message and
    # returns it if the checksum is valid, else returns an empy
    # list
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

    # switch to uplink mode, stopping rx flowgraph and starting
    # a tx flowgraph
    def switch_to_uplink(self):
        # shutdown receive flowgraph
        self.shutdown()

        # instance a tx flowgraph with current uplink settings
        self.fg_tx = tx_top.TxTop(rf_params=self.uplink_rf_params,
                                  bb_params=self.uplink_bb_params,
                                  tcp_addr=self.tcp_tx,
                                  tcp_test=zmu.TCP_TEST2)
        self.fg_tx.start()

    # switch to uplink mode, stopping rx flowgraph and starting
    # a tx flowgraph
    def switch_to_downlink(self):
        # shutdown receive flowgraph
        self.shutdown()

        # instance a tx flowgraph with current uplink settings
        self.fg_rx = rx_top.RxTop(rf_params=self.downlink_rf_params,
                                  bb_params=self.downlink_bb_params,
                                  tcp_addr=self.tcp_rx,
                                  tcp_test=zmu.TCP_TEST)
        self.fg_rx.start()

    # sends data, then
    def send_bytes(self, payload_list, verbose=False):
        # send the payload N times
        for i in xrange(rfm.TX_REP):
            self.tx_zmq.send_framed_bytes(
                byte_list=payload_list,
                preamble=self.uplink_bb_params.preamble_bytes)

        # shut down flowgraph
        #self.tx_shutdown()

    # to keep from operating tx and rx simultaneously
    def rx_shutdown(self):
        if ('fg_rx' in vars(self)) and (self.fg_rx is not None):
            self.fg_rx.stop()
            time.sleep(1)
            #del self.fg_rx
            self.fg_rx = None

    def tx_shutdown(self):
        if ('fg_tx' in vars(self)) and (self.fg_tx is not None):
            self.fg_tx.stop()
            time.sleep(1)
            #del self.fg_tx
            self.fg_tx = None

    # shut down both (used at exit)
    def shutdown(self):
        self.rx_shutdown()
        self.tx_shutdown()
