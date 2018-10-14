# This module contains the classes required for handling modulation
# setup.

HW_TEST = 0
HW_UHD = 1
HW_HACKRF = 2

MOD_ZMQ_TEST = 0
MOD_OOK = 1
MOD_FSK = 2
# the following are not supported
MOD_GFSK = 3
MOD_DPSK = 4

ENC_NRZ = 1
# the following are not supported
ENC_MANCH = 2
ENC_PWM = 3
ENC_PIE = 4


class RfParams():
    def __init__(self,
                 sdr_hw,
                 samp_rate,
                 center_freq,
                 freq,
                 channel_width,
                 mod_scheme,
                 threshold,
                 agc_enable,
                 fsk_dev,
                 psk_const_num,
                 rx_gain,
                 tx_gain,
                 transition_width = 0
                 ):
        self.sdr_hw = sdr_hw
        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.freq = freq
        self.channel_width = channel_width
        self.transition_width = transition_width
        self.mod_scheme = mod_scheme
        self.threshold = threshold
        self.agc_enable = agc_enable
        self.fsk_dev = fsk_dev
        self.psk_const_num = psk_const_num
        self.rx_gain = rx_gain
        self.tx_gain = tx_gain


class BbParams():
    def __init__(self,
                 preamble,
                 encoding,
                 symbol_time,
                 ):
        self.preamble = preamble
        self.encoding = encoding
        self.symbol_time = symbol_time

