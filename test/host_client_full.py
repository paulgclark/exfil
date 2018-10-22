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
    #rf_params.print_vals()

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

    # these are the new parameters we need to send to the xfil for
    # reconfig; default with change to freq and preamble
    rf_params2_host = rfm.RfParams()
    rf_params2_host.freq = 913.4e6
    bb_params2_host = rfm.BbParams()
    bb_params2_host.set_preamble([0xcc, 0x33])
    host.set_uplink_config(rf_params=rf_params2_host, bb_params=bb_params2_host)

    # create new config vars for the xfil side (used below)
    rf_params2_xfil = rfm.RfParams()
    bb_params2_xfil = rfm.BbParams()

    # priming the zmq receive socket (don't understand this fully...)
    for i in xrange(10):
        host.send_bytes(cmd_bytes=rfm.DUMMY_PAYLOAD)

    # send command several times
    for i in xrange(7):
        time.sleep(0.1)
        # transmit the bytes
        host.send_uplink_config()
        time.sleep(0.1)
        # receive the bytes
        rx_data = xfil.recv_command()
        #print "Received bytes, len={}: ".format(len(rx_data)),
        #print rx_data

        # now setup new param vars with this data
        if len(rx_data) < 14:
            print "Transmission too short, no decoding attempted"
        else:
            # convert bytes into config vars
            rf_params2_xfil.restore_from_cmd(rx_data[0:13])
            rf_params2_xfil.print_vals()
            bb_params2_xfil.restore_from_cmd(rx_data[13:])
            bb_params2_xfil.print_vals()
            # use vars to update xfil config
            xfil.set_uplink_config(rf_params=rf_params2_xfil,
                                   bb_params=bb_params2_xfil)


    # now switch over to uplink mode, with xfil sending back data on
    # newly configured link
    host.shutdown()
    xfil.shutdown()
    host.switch_to_uplink()
    xfil.switch_to_uplink()

    print "********Switchover********\n\n\n"
    xfil_data = [[3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5],
                 [8, 6, 7, 5, 3, 0, 9],
                 [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
                 [255, 0, 254, 1, 253, 2, 252, 3, 251, 4, 250, 5],
                 [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5],
                 [8, 6, 7, 5, 3, 0, 9],
                 [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
                 [255, 0, 254, 1, 253, 2, 252, 3, 251, 4, 250, 5]]

    # prime the pump
    for i in xrange(6):
        xfil.send_bytes(payload_list=rfm.DUMMY_PAYLOAD)
        time.sleep(0.1)

    # send string and byte data
    for i in xrange(8):
        time.sleep(0.5)
        # transmit the bytes
        xfil.send_bytes(xfil_data[i])
        time.sleep(0.5)
        # receive the bytes
        rx_data = host.recv_bytes()
        if rx_data == rfm.DUMMY_PAYLOAD:
            print "Got dummy payload"
        else:
            print "Received bytes:",
            print "len {}: ".format(len(rx_data)),
            print rx_data


    # stop the flowgraph and exit
    host.shutdown()
    xfil.shutdown()

    print "Finished Full TX-RX Unit Test"
    exit(0)