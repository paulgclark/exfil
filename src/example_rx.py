#!/usr/bin/python

# This script is an example showing how to implement a simple receiver. It
# is intended for use with the example_tx.py script.
import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import radio_stack as rs
import argparse

parser = argparse.ArgumentParser("Run simple receiver to get strings")
parser.add_argument("-s", "--sdr_hw", help="0-test, 1-uhd, 2-hackrf", type=int)
parser.add_argument("-m", "--mod", help="1-OOK, 2-GMSK", type=int)
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
args = parser.parse_args()

sdr_hw = rfm.HW_TEST if (args.sdr_hw is None) else args.sdr_hw
mod_scheme = rfm.MOD_OOK if (args.mod is None) else args.mod
verbose = False if (args.verbose is None) else bool(args.verbose)
if verbose:
    print "Command Line Args:"
    print "  SDR Sel = {}".format(sdr_hw)
    print "  Mod Scheme = {}".format(mod_scheme)
    print "  Verbose = {}".format(verbose)
    temp = raw_input("press any key to continue")

if __name__ == "__main__":
    # build flowgraph config objects using defaults
    # to change these, simply assign fields to you chosen values
    rf_params = rfm.RfParams()
    rf_params.mod_scheme = mod_scheme
    bb_params = rfm.BbParams()

    # instance a radio (this is a half-duplex transceiver, but we'll
    # only use it in transmit mode)
    rx_radio = rs.RadioStack(rx_rf_params=rf_params,
                             rx_bb_params=bb_params,
                             tx_rf_params=rf_params,
                             tx_bb_params=bb_params,
                             tcp_params=zmu.tcp_params_xfil,
                             sdr_sel=sdr_hw)
    # start the ZMQ/flowgraph combo
    rx_radio.switch_to_rx()

    if verbose:
        print "Radio Config:"
        rx_radio.rx_rf_params.print_vals()
        rx_radio.rx_bb_params.print_vals()

    # main loop; just sits and waits to receive, then prints out strings
    while True:
        rx_str = rx_radio.recv_str()
        if rx_str != "":
            print rx_str

    # all done
    rx_radio.shutdown()
    print "Exiting..."


