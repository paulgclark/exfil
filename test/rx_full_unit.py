#!/usr/bin/python

# The purpose of this file is to test the full receive flow

import sys
import time
sys.path.append('../src')
import zmq_utils as zmu
import rf_mgt as rfm
import rx_top

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
#PREAMBLE = [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1]
PREAMBLE_BYTES = [0x55, 0x55]

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

    # instance and start the flowgraph
    fg = rx_top.RxTop(rf_params, bb_params)
    fg.start()

    # setup the zmq socket
    socket = zmu.zmq_pull_msg_socket(zmu.TCP_RX)

    # poll the socket and acquire the data
    for _ in xrange(3):
        time.sleep(1)
        str = socket.poll_str()
        print str
        data = socket.poll_bytes()
        print data

    # stop the flowgraph and exit
    fg.stop()
    print "Finished Full RX Unit Test"
    exit(0)



