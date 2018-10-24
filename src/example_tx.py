#!/usr/bin/python

# This script is an example showing how to implement a simple transmitter. It
# is intended for use with the example_rx.py script.
import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import radio_stack as rs
import argparse

parser = argparse.ArgumentParser("Run simple transmitter to send strings")
parser.add_argument("-s", "--sdr_hw", help="0-test, 1-uhd, 2-hackrf", type=int)
parser.add_argument("-m", "--mod",
                    help="1-OOK, 2-GMSK, 3-GFSK, 4-PSK", type=int)
parser.add_argument("-g", "--tx_gain", help="tx gain (0-70)", type=int)
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
args = parser.parse_args()

sdr_hw = rfm.HW_TEST if (args.sdr_hw is None) else args.sdr_hw
mod_scheme = rfm.MOD_OOK if (args.mod is None) else args.mod
if (args.tx_gain is None) or not(0<=args.tx_gain<=70):
    tx_gain = args.tx_gain
else:
    tx_gain = rfm.DEF_TX_GAIN
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
    rf_params.tx_gain = tx_gain
    bb_params = rfm.BbParams()

    # instance a radio (this is a half-duplex transceiver, but we'll
    # only use it in transmit mode)
    tx_radio = rs.RadioStack(rx_rf_params=rf_params,
                             rx_bb_params=bb_params,
                             tx_rf_params=rf_params,
                             tx_bb_params=bb_params,
                             tcp_params=zmu.tcp_params_host,
                             sdr_sel=sdr_hw)
    # enable the transmitter
    tx_radio.switch_to_tx()

    if verbose:
        print "Radio Config:"
        tx_radio.tx_rf_params.print_vals()
        tx_radio.tx_bb_params.print_vals()

    # main loop; each time through you are asked for an input string,
    # which is then transmitted using the configured parameters
    while True:
        # prompt for text to transmit
        tx_string = raw_input("Enter text to transmit (q to quit): ")
        if tx_string.lower() == 'q':
            break

        # send a dummy payload to flush the system
        for i in xrange(7):
            tx_radio.send_bytes(tx_bytes=rfm.DUMMY_PAYLOAD)

        # now send the string
        for i in xrange(rfm.TX_REP):
            time.sleep(0.1)
            tx_radio.send_str(tx_string)

    # all done
    tx_radio.shutdown()
    print "Exiting..."


