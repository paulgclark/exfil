#!/usr/bin/python

# The purpose of this file is to test the full transmit and receive
# flow in ZMQ loopback test mode.

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import xfil
import host

if __name__ == "__main__":

    # build flowgraph config objects
    rf_params = rfm.RfParams()
    bb_params = rfm.BbParams()

    # instance the host and xfil
    host = host.hostClass(init_rf_params=rf_params,
                          init_bb_params=bb_params,
                          tcp_tx=zmu.TCP_TX_HOST,
                          tcp_rx=zmu.TCP_RX_HOST)
    host.set_uplink_config(rf_params=rf_params,
                           bb_params=bb_params)
    xfil = xfil.xfilClass(init_rf_params=rf_params,
                          init_bb_params=bb_params,
                          tcp_rx=zmu.TCP_RX_XFIL,
                          tcp_tx=zmu.TCP_TX_XFIL)

    cmd_list = [1,2,3,4,5,6,7]

    rf_params.print_vals()

    # priming the zmq receive socket (don't understand this fully...)
    for i in xrange(10):
        host.send_bytes(cmd_bytes=cmd_list)

    rf_params2 = rfm.RfParams()
    bb_params2 = rfm.BbParams()

    # send string and byte data
    for i in xrange(5):
        time.sleep(0.2)
        # transmit the bytes
        host.send_uplink_config()
        time.sleep(0.2)
        # receive the bytes
        print "Received bytes:",
        rx_data = xfil.recv_command()
        print "len {}: ".format(len(rx_data)),
        print rx_data

        # now setup new param vars with this data
        if len(rx_data) < 14:
            print "Transmission too short, no decoding attempted"
        else:
            rf_params2.restore_from_cmd(rx_data[0:14])
            print rx_data[0:14]
            bb_params2.restore_from_cmd(rx_data[13:])
            print rx_data[13:]
            rf_params2.print_vals()
            bb_params2.print_vals()


    # stop the flowgraph and exit
    host.shutdown()
    xfil.shutdown()

    print "Finished Full TX-RX Unit Test"
    exit(0)