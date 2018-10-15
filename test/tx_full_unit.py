#!/usr/bin/python

# The purpose of this file is to test the full transmit flow. This
# file is meant for use in conjunction with the receive-side flowgraph
# located at ./grc/ook_tx_msg.grc

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import tx_top

from gnuradio import gr
from gnuradio import blocks
from gnuradio import digital
from gnuradio import zeromq
from gnuradio.eng_option import eng_option

SAMP_RATE = 2e6
CENTER_FREQ = 433e6
FREQ = 432.5e6
CHANNEL_WIDTH = 20e3
SYMBOL_TIME = 100e-6
PREAMBLE_BITS = [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1]
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
                             preamble=PREAMBLE_BITS,
                             symbol_time=SYMBOL_TIME
                             )

    # instance and start the flowgraph
    fg = tx_top.TxTop(rf_params, bb_params)
    fg.start()

    # setup the zmq socket
    msg_push = zmu.ZmqPushMsgSocket(zmu.TCP_TX)

    # send string and byte data
    while True:
        time.sleep(1)
        msg_push.send_framed_bytes(preamble=PREAMBLE_BYTES,
                                   byte_list=raw_bytes,
                                   verbose=True)
        time.sleep(1)
        msg_push.send_framed_str(preamble=PREAMBLE_BYTES,
                                 in_str="Testing now...",
                                 verbose=True)

    # stop the flowgraph and exit
    fg.stop()
    print "Finished Full RX Unit Test"
    exit(0)