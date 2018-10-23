#!/usr/bin/python

# This script is intended for use with a second xfil_radio.py script
# with which it communicates. The xfil_radio.py script will either run on
# the same machine (test mode) or on a different machine if SDR hardware
# is used
import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import radio_stack as rs
import argparse
from collections import Counter
from itertools import combinations

parser = argparse.ArgumentParser("Run host radio to get data from xfil unit")
parser.add_argument("-s", "--sdr_hw", help="0-test, 1-uhd, 2-hackrf", type=int)
parser.add_argument("-v", "--verbose", help="increase output verbosity",
                    action="store_true")
args = parser.parse_args()

sdr_hw = rfm.HW_TEST if (args.sdr_hw is None) else args.sdr_hw
verbose = False if (args.verbose is None) else bool(args.verbose)
if verbose:
    print "Command Line Args:"
    print "  SDR Sel = {}".format(sdr_hw)
    print "  Verbose = {}".format(verbose)
    temp = raw_input("press any key to continue")

if __name__ == "__main__":
    # build flowgraph config objects using defaults
    tx_rf_params = rfm.RfParams()
    tx_rf_params.sdr_hw = sdr_hw
    tx_bb_params = rfm.BbParams()

    # setup a second set of params that we will change and then
    # send to the xfil box for reconfig; these parameters represent
    # those to which we will change the host's receiver and the xfil's
    # transmitter
    rx_rf_params = rfm.RfParams()
    rx_rf_params.sdr_hw = sdr_hw
    rx_bb_params = rfm.BbParams()

    # instance the host
    host = rs.RadioStack(rx_rf_params=rx_rf_params,
                         rx_bb_params=rx_bb_params,
                         tx_rf_params=tx_rf_params,
                         tx_bb_params=tx_bb_params,
                         tcp_params=zmu.tcp_params_host,
                         sdr_sel=sdr_hw)

    # main loop; each time through the host changes the params, sends them
    # to the xfil box and gets the xfil data back
    payloads_received = []
    while True:
        # change the outgoing configuration per user command
        while True:
            # print the current config
            print(chr(27) + "[2J") # clear the screen first
            print "Payloads Received:"
            for i in xrange(len(payloads_received)):
                print payloads_received[i]
            print "\nCurrent RF and BB Params:"
            host.rx_rf_params.print_vals()
            host.rx_bb_params.print_vals()
            # prompt user for change
            print "Changes allowed to (f)req, (m)odulation, (p)reamble"
            user_input = raw_input("Enter selection (or (c)onfig: ")

            # process user input
            if user_input == 'f':
                user_input2 = raw_input("Enter new frequency (912-914MHz): ")
                if (912e6 < float(user_input2) < 914e6):
                    host.rx_rf_params.freq = float(user_input2)
            elif user_input == 'm':
                user_input2 = raw_input("Enter 1 for OOK, 2 for GMSK, 3 for FSK: ")
                if (1 <= int(user_input2) <= 3):
                    host.rx_rf_params.mod_scheme = int(user_input2)
            elif user_input == 'p':
                user_input2 = raw_input("Enter 1[AAAA], 2[C3C3], 3[E77E]: ")
                if int(user_input2) == 1:
                    host.rx_bb_params.set_preamble([0xAA, 0xAA])
                elif int(user_input2) == 2:
                    host.rx_bb_params.set_preamble([0xC3, 0xC3])
                elif int(user_input2) == 3:
                    host.rx_bb_params.set_preamble([0xE7, 0x7E])
            elif user_input == 'c':
                break

        # send control signal to xfil
        print "Sending config data to xfil device..."
        host.switch_to_tx()
        for i in xrange(7):
            host.send_bytes(tx_bytes=rfm.DUMMY_PAYLOAD)
        for i in xrange(7):
            time.sleep(0.1)
            host.send_uplink_config()

        # now reconfigure to receive data from xfil
        time.sleep(4)
        print "Reconfiguring to receive from xfil..."
        host.switch_to_rx()

        good_payloads = []
        for i in xrange(7):
            rx_data = host.recv_bytes_timeout()
            if verbose:
                print "--- Raw Payload: ",
                print rx_data
            # if the payload is good, then add it to the list
            if rx_data != [] and rx_data != rfm.DUMMY_PAYLOAD:
                good_payloads.append(rx_data)

        # now find the most common payload and add it to the
        # master list (later; for now just take the first one)
        if len(good_payloads) > 0:
            payloads_received.append(good_payloads[0])
        else:
            payloads_received.append(["No payload received"])




