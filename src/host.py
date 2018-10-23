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
    def __init__(self, init_rf_params, init_bb_params, tcp_tx, tcp_rx):
        # build flowgraph object with initial params
        self.fg_tx = tx_top.TxTop(rf_params=init_rf_params,
                                  bb_params=init_bb_params,
                                  tcp_addr=tcp_tx,
                                  tcp_test=zmu.TCP_TEST)
        # start the flowgraph
        self.fg_tx.start()

        # open zmq socket for payload xfr to flowgraph
        self.tx_zmq = zmu.ZmqPushMsgSocket(tcp_tx)

        # open zmq socket for payload xfr from rx flowgraph
        self.rx_zmq = zmu.ZmqPullMsgSocket(tcp_rx)

        self.downlink_rf_params = init_rf_params
        self.downlink_bb_params = init_bb_params
        self.uplink_rf_params = None
        self.uplink_bb_params = None
        self.tcp_tx = tcp_tx
        self.tcp_rx = tcp_rx
        self.verbose = False

    # switch to uplink mode, stopping rx flowgraph and starting
    # a tx flowgraph
    def switch_to_uplink(self):
        # shutdown receive flowgraph
        self.shutdown()

        # instance a tx flowgraph with current uplink settings
        self.fg_rx = rx_top.RxTop(rf_params=self.uplink_rf_params,
                                  bb_params=self.uplink_bb_params,
                                  tcp_addr=self.tcp_rx,
                                  tcp_test=zmu.TCP_TEST2)
        self.fg_rx.start()

    # switch to uplink mode, stopping rx flowgraph and starting
    # a tx flowgraph
    def switch_to_downlink(self):
        # shutdown receive flowgraph
        self.shutdown()

        # instance a tx flowgraph with current uplink settings
        self.fg_tx = tx_top.TxTop(rf_params=self.downlink_rf_params,
                                  bb_params=self.downlink_bb_params,
                                  tcp_addr=self.tcp_tx,
                                  tcp_test=zmu.TCP_TEST)
        self.fg_tx.start()

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
        if self.verbose:
            print self.uplink_rf_params.params_to_bytes()
            print self.uplink_bb_params.params_to_bytes()
        cmd_bytes = self.uplink_rf_params.params_to_bytes()
        cmd_bytes += self.uplink_bb_params.params_to_bytes()
        self.send_bytes(cmd_bytes=cmd_bytes)

    def send_bytes(self, cmd_bytes):
        # add checksum to commands
        combo_bytes = cmd_bytes[:]
        combo_bytes.append(rfm.acs(cmd_bytes))
        self.tx_zmq.send_framed_bytes(
            preamble=self.downlink_bb_params.preamble_bytes,
            byte_list=combo_bytes,
            verbose=self.verbose)

    # same as recv_cmd in xfil; need to have a single class for this
    def recv_bytes(self, verbose=False):
        # wait for valid transmission
        raw_data = self.rx_zmq.poll_bytes(self.verbose)

        # checksum
        cs_computed = rfm.acs(raw_data[:-1])
        if verbose:
            print "Raw data bytes:",
            print raw_data
            print "Checksum: {}".format(cs_computed)

        # if we have a valid command, reconfigure the flowgraph
        if cs_computed == raw_data[-1]:
            return raw_data[:-1]
        else:
            return []


    # to keep from operating tx and rx simultaneously
    def rx_shutdown(self):
        if 'fg_rx' in vars(self):
            self.fg_rx.stop()
            time.sleep(1)
            del self.fg_rx

    def tx_shutdown(self):
        if 'fg_tx' in vars(self):
            self.fg_tx.stop()
            time.sleep(1)
            del self.fg_tx

    # shut down both (used at exit)
    def shutdown(self):
        self.rx_shutdown()
        self.tx_shutdown()


