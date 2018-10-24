#!/usr/bin/python

# The purpose of this file is to test the full transmit and receive
# flow in ZMQ loopback test mode.

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import radio_stack as rs

if __name__ == "__main__":
    # build flowgraph config objects
    rf_params = rfm.RfParams()
    bb_params = rfm.BbParams()

    # these are the new parameters we need to send to the xfil for
    # reconfig; default with change to freq and preamble
    rf_params2_host = rfm.RfParams()
    rf_params2_host.freq = 913.4e6
    #rf_params2_host.mod_scheme = rfm.MOD_GMSK
    #rf_params2_host.mod_scheme = rfm.MOD_GFSK
    rf_params2_host.mod_scheme = rfm.MOD_PSK
    bb_params2_host = rfm.BbParams()
    bb_params2_host.set_preamble([0xcc, 0x33])

    # instance the host and xfil
    host = rs.RadioStack(rx_rf_params=rf_params2_host,
                         rx_bb_params=bb_params2_host,
                         tx_rf_params=rf_params,
                         tx_bb_params=bb_params,
                         tcp_params=zmu.tcp_params_host)
    xfil = rs.RadioStack(rx_rf_params=rf_params,
                         rx_bb_params=bb_params,
                         tx_rf_params=rf_params,
                         tx_bb_params=bb_params,
                         tcp_params=zmu.tcp_params_xfil)

    # create new config vars for the xfil side (used below)
    rf_params2_xfil = rfm.RfParams()
    bb_params2_xfil = rfm.BbParams()

    # enable the host transmitter
    host.switch_to_tx()
    # enable the xfil receiver
    xfil.switch_to_rx()

    # priming the zmq receive socket (don't understand this fully...)
    for i in xrange(6):
        host.send_bytes(tx_bytes=rfm.DUMMY_PAYLOAD)

    # send command several times
    for i in xrange(8):
        time.sleep(0.1)
        # transmit the bytes
        host.send_uplink_config()
        time.sleep(0.1)
        # receive the bytes
        rx_data = xfil.recv_bytes()
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
            xfil.set_tx_config(rf_params=rf_params2_xfil,
                               bb_params=bb_params2_xfil)

    # now switch over to xfil mode, with xfil sending back data on
    # newly configured link
    host.switch_to_rx()
    xfil.switch_to_tx()
    time.sleep(1)

    print "********Switchover********\n\n\n"
    xfil.tx_rf_params.print_vals()
    xfil.tx_bb_params.print_vals()
    # read text into a list of lines; each of these lines will be a payload
    # for the xfil box to send upstream to the host
    with open("../src/raven.txt") as f:
        xfil_data = f.readlines()
    xfil_data = [x.strip() for x in xfil_data]

    # prime the pump
    for i in xrange(6):
        xfil.send_str(tx_str=rfm.DUMMY_PAYLOAD_STR)
        time.sleep(0.1)

    # send string and byte data
    for i in xrange(30):
        time.sleep(0.1)
        # transmit the bytes
        xfil.send_str(xfil_data[i])
        time.sleep(0.1)
        # receive the bytes
        rx_data = host.recv_str()
        if rx_data == rfm.DUMMY_PAYLOAD_STR:
            print "Got dummy payload"
        else:
            print "Received (len {}): ".format(len(rx_data)),
            print rx_data


    # stop the flowgraph and exit
    host.shutdown()
    xfil.shutdown()

    print "Finished Full TX-RX Unit Test"
    exit(0)