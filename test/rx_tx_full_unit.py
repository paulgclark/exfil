#!/usr/bin/python

# The purpose of this file is to test the full transmit and receive
# flow in ZMQ loopback test mode.

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import tx_top
import rx_top

SAMP_RATE = 2e6
CENTER_FREQ = 433e6
FREQ = 432.5e6
CHANNEL_WIDTH = 20e3
SYMBOL_TIME = 100e-6
#PREAMBLE_BITS = [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1]
PREAMBLE_BYTES = [0x55, 0x55]
# send these via the flowgraph
raw_bytes = [0xC0, 0x3F, 0xEB, 0x00, 0x13]

if __name__ == "__main__":

    # build flowgraph config objects
    rf_params = rfm.RfParams(sdr_hw=rfm.HW_TEST,
                             samp_rate=SAMP_RATE,
                             center_freq=CENTER_FREQ,
                             freq=FREQ,
                             channel_width=CHANNEL_WIDTH,
                             mod_scheme=rfm.MOD_OOK,
                             threshold=0.5,
                             agc_enable=True,
                             fsk_dev=0,
                             psk_const_num=0,
                             rx_gain=50,
                             tx_gain=50
                             )
    bb_params = rfm.BbParams(encoding=rfm.ENC_NRZ,
                             preamble=PREAMBLE_BYTES,
                             symbol_time=SYMBOL_TIME
                             )

    # instance and start the tx flowgraph
    fg_tx = tx_top.TxTop(rf_params, bb_params, zmu.TCP_TX_HOST)
    fg_tx.start()
    # setup the zmq socket to feed the transmitter
    tx_zmq = zmu.ZmqPushMsgSocket(zmu.TCP_TX_HOST)

    # instance and start the rx flowgraph
    fg_rx = rx_top.RxTop(rf_params, bb_params, zmu.TCP_RX_XFIL)
    fg_rx.start()
    # setup the zmq socket to grab data from the receiver
    rx_zmq = zmu.ZmqPullMsgSocket(zmu.TCP_RX_XFIL)

    # priming the zmq receive socket (don't understand this fully...)
    # send some dead air
    #tx_zmq.send_raw_bytes(10000 * [0])
    for i in xrange(8):
        tx_zmq.send_framed_bytes(preamble=bb_params.preamble_bytes,
                                 byte_list=raw_bytes,
                                 verbose=False)

    # send string and byte data
    while True:
        time.sleep(1)
        # transmit the bytes
        tx_zmq.send_framed_bytes(preamble=bb_params.preamble_bytes,
                                 byte_list=raw_bytes,
                                 verbose=False)
        time.sleep(1)
        # receive the bytes
        print "Received bytes:",
        rx_data = rx_zmq.poll_bytes()
        print rx_data

        # transmit a string
        tx_zmq.send_framed_str(preamble=bb_params.preamble_bytes,
                               in_str="Testing now...",
                               verbose=False)
        time.sleep(1)
        print "Received string:",
        rx_str = rx_zmq.poll_str()
        print rx_str

    # stop the flowgraph and exit
    fg_rx.stop()
    fg_tx.stop()
    print "Finished Full TX-RX Unit Test"
    exit(0)