#!/usr/bin/python

# The purpose of this file is to test the full transmit and receive
# flow in ZMQ loopback test mode.

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import radio_stack as rs

xfil_data = [[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5],
             [8, 6, 7, 5, 3, 0, 9],
             [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
             [255, 0, 254, 1, 253, 2, 252, 3, 251, 4, 250, 5],
             [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5],
             [8, 6, 7, 5, 3, 0, 9],
             [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
             [255, 0, 254, 1, 253, 2, 252, 3, 251, 4, 250, 5]]

if __name__ == "__main__":
    # build flowgraph config objects for the control channel
    rf_params = rfm.RfParams()
    bb_params = rfm.BbParams()

    # create some param objects to hold the reconfiguration when it comes in
    tx_rf_params = rfm.RfParams()
    tx_bb_params = rfm.BbParams()

    # instance the xfil, using the default for both rx and tx
    # (tx will be changed later via control link)
    xfil = rs.RadioStack(rx_rf_params=rf_params,
                         rx_bb_params=bb_params,
                         tx_rf_params=rf_params,
                         tx_bb_params=bb_params,
                         tcp_params=zmu.tcp_params_xfil)

    # master loop
    master_loop_index = 0
    while True:

        # turn on receiver function
        print "Receive mode enabled..."
        xfil.switch_to_rx()

        cmd_count = 0
        last_cmd = []
        while True:
            cmd = xfil.recv_bytes()
            print "Received CMD: ",
            print cmd

            if len(cmd) == 17:
                tx_rf_params.restore_from_cmd(cmd_bytes=cmd[0:13])
                tx_bb_params.restore_from_cmd(cmd_bytes=cmd[13:])
                # make sure the command is valid by demanding n copies of it
                if cmd_count == 0:
                    last_cmd = cmd
                    cmd_count += 1
                if cmd_count < rfm.CMD_REP_REQ:
                    if cmd == last_cmd:
                        cmd_count += 1
                else:
                    # we have a good cmd; set the transmit config and exit loop
                    tx_rf_params.print_vals()
                    tx_bb_params.restore_from_cmd(cmd_bytes=cmd[13:])
                    tx_bb_params.print_vals()
                    xfil.set_tx_config(rf_params=tx_rf_params, bb_params=tx_bb_params)
                    break
            else:
                print "CMD too short, len={}".format(len(cmd))

        # wait until the host finishes up
        time.sleep(5)

        print "Transmit mode enabled..."
        # now configure for transmit and send the payload data
        xfil.switch_to_tx()

        # prime the pump
        for i in xrange(6):
            xfil.send_bytes(tx_bytes=rfm.DUMMY_PAYLOAD)
            time.sleep(0.1)

        # send the byte data
        for i in xrange(rfm.TX_REP):
            time.sleep(0.1)
            xfil.send_bytes(tx_bytes=xfil_data[master_loop_index])
            time.sleep(0.1)

        # go back to listening mode
        print "Done with xfil tx, returning to listen mode..."
        master_loop_index += 1

