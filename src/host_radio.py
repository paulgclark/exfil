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

if __name__ == "__main__":
    # build flowgraph config objects using defaults
    tx_rf_params = rfm.RfParams()
    tx_bb_params = rfm.BbParams()

    # setup a second set of params that we will change and then
    # send to the xfil box for reconfig; these parameters represent
    # those to which we will change the host's receiver and the xfil's
    # transmitter
    rx_rf_params = rfm.RfParams()
    rx_bb_params = rfm.BbParams()

    # instance the host
    host = rs.RadioStack(rx_rf_params=rx_rf_params,
                         rx_bb_params=rx_bb_params,
                         tx_rf_params=tx_rf_params,
                         tx_bb_params=tx_bb_params,
                         tcp_params=zmu.tcp_params_host)

    # main loop; each time through the host changes the params, sends them
    # to the xfil box and gets the xfil data back
    while True:
        # change the outgoing configuration per user command
        while True:
            # print the current config
            print(chr(27) + "[2J") # clear the screen first
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
                user_input2 = raw_input("Enter 1 for OOK, 2 for FSK: ")
                if (1 <= user_input2 <= 2):
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
        host.switch_to_rx()
        user_input = raw_input("Setup xfil tx and press enter to receive...")
        while True:
            rx_data = host.recv_bytes()
            if rx_data != rfm.DUMMY_PAYLOAD:
                print "Received Bytes:",
                print rx_data

            user_input = raw_input("press q to terminate receiver: ")
            if user_input.lower() == "q":
                break


