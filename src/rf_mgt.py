# This module contains the classes required for handling modulation
# setup.

import cmd_mgt

HW_TEST = 0
HW_UHD = 1
HW_HACKRF = 2

MOD_ZMQ_TEST = 0
MOD_OOK = 1
MOD_GMSK = 2
MOD_GFSK = 3
MOD_PSK = 4

ENC_NRZ = 1
# the following are not supported
ENC_MANCH = 2
ENC_PWM = 3
ENC_PIE = 4

# these are the scaling factors used for the parameters below
ISM_LOW = 902e6
S_NONE = 1
S_BOOL = 0
S_MEG = 1000000 # megs are scaled to 1MHz
S_FREQS = 10000000 # freqs are scaled to 10MHz
S_DELTA_F = 100000 # delta f is scaled to 100kHz
S_FILT = 1000 # filter parameters are scaled to 1kHz
S_THRESH = 0.002 # thresholds have a range from 0.002 to about 0.5 (256x)
S_SYMB_TIME = 10e-5 # symbol times range from 10us to 2.5ms

# default values for rf params, allows easier setup for test
DEF_SDR_HW = HW_TEST
DEF_SAMP_RATE = 2e6
DEF_CENTER_FREQ = 913e6
DEF_FREQ = 912.5e6
DEF_CHANNEL_WIDTH = 80e3
DEF_MOD_SCHEME = MOD_OOK
DEF_THRESHOLD = 0.5
DEF_AGC_ENABLE = True
DEF_FSK_DEV = 40e3
DEF_PSK_CONST_NUM = 2
DEF_RX_GAIN = 40
DEF_TX_GAIN = 60
# defaults for bb params
DEF_PREAMBLE_BYTES = [0x55, 0x55]
DEF_ENCODING = ENC_NRZ
DEF_SYMBOL_TIME = 100e-6

# this payload is used to clear the zmq pipe, it is typically ignored
DUMMY_PAYLOAD = [1, 2, 3, 4, 5, 6, 7]
# this is the number of identical commands required before it is acted on
CMD_REP_REQ = 2
TX_REP = 10

# miscellaneous values
PWR_SQUELCH_DB = -50

# use this value as a designator for the payload type (not implemented)
#CMD_ID = 0xD7
#DATA_ID = 0xC3
#TEST_ID = 0xEE


class RfParams():
    def __init__(self,
                 sdr_hw = DEF_SDR_HW,
                 samp_rate = DEF_SAMP_RATE,
                 center_freq = DEF_CENTER_FREQ, # must be 902-925MHz
                 freq = DEF_FREQ,
                 channel_width = DEF_CHANNEL_WIDTH,
                 mod_scheme = DEF_MOD_SCHEME,
                 threshold = DEF_THRESHOLD,
                 agc_enable = DEF_AGC_ENABLE,
                 fsk_dev = DEF_FSK_DEV,
                 psk_const_num = DEF_PSK_CONST_NUM,
                 rx_gain = DEF_RX_GAIN,
                 tx_gain = DEF_TX_GAIN,
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

    # output command bytes corresponding to current values; the goal
    # is to convert each field into an integer ranging from 0-256
    def params_to_bytes(self):
        cmd_bytes = []
        cmd_bytes.append(scale_to_int(self.sdr_hw, S_NONE))
        cmd_bytes.append(scale_to_int(self.samp_rate, S_MEG))
        # we handle center_freq differently, treating it as a
        # difference between the value and the bottom ISM freq
        relative_freq = self.center_freq - ISM_LOW
        cmd_bytes.append(scale_to_int(relative_freq, S_DELTA_F))
        # we handle freq differently, by treating it as a difference
        # from the center_freq - samp_rate/2 (the bottom of the sampling range)
        relative_freq = self.freq - self.center_freq + self.samp_rate/2
        cmd_bytes.append(scale_to_int(relative_freq, S_DELTA_F))
        cmd_bytes.append(scale_to_int(self.channel_width, S_FILT))
        cmd_bytes.append(scale_to_int(self.transition_width, S_FILT))
        cmd_bytes.append(scale_to_int(self.mod_scheme, S_NONE))
        cmd_bytes.append(scale_to_int(self.threshold, S_THRESH))
        cmd_bytes.append(scale_to_int(self.agc_enable, S_BOOL))
        cmd_bytes.append(scale_to_int(self.fsk_dev, S_FILT))
        cmd_bytes.append(scale_to_int(self.psk_const_num, S_NONE))
        cmd_bytes.append(scale_to_int(self.rx_gain, S_NONE))
        cmd_bytes.append(scale_to_int(self.tx_gain, S_NONE))
        return cmd_bytes

    # take the command bytes and build a record from them
    def restore_from_cmd(self, cmd_bytes):
        self.sdr_hw = restore_from_scaled(cmd_bytes[0], S_NONE)
        self.samp_rate = restore_from_scaled(cmd_bytes[1], S_MEG)
        # we encoded center_freq in a special way (see above)
        relative_freq = restore_from_scaled(cmd_bytes[2], S_DELTA_F)
        self.center_freq = ISM_LOW + relative_freq
        # we encoded frequency in a special way (see above)
        relative_freq = restore_from_scaled(cmd_bytes[3], S_DELTA_F)
        self.freq = relative_freq + self.center_freq - self.samp_rate/2
        self.channel_width = restore_from_scaled(cmd_bytes[4], S_FILT)
        self.transition_width = restore_from_scaled(cmd_bytes[5], S_FILT)
        self.mod_scheme = restore_from_scaled(cmd_bytes[6], S_NONE)
        self.threshold = restore_from_scaled(cmd_bytes[7], S_THRESH)
        self.agc_enable = restore_from_scaled(cmd_bytes[8], S_BOOL)
        self.fsk_dev = restore_from_scaled(cmd_bytes[9], S_FILT)
        self.psk_const_num = restore_from_scaled(cmd_bytes[10], S_NONE)
        self.rx_gain = restore_from_scaled(cmd_bytes[11], S_NONE)
        self.tx_gain = restore_from_scaled(cmd_bytes[12], S_NONE)


    def print_vals(self):
        print "SDR HW:        {}".format(self.sdr_hw)
        print "samp rate:     {} MHz".format(self.samp_rate)
        print "center freq:   {} MHz".format(self.center_freq)
        print "freq:          {} MHz".format(self.freq)
        print "chan width:    {} kHz".format(self.channel_width)
        print "trans width:   {} kHz".format(self.transition_width)
        print "mod scheme:    {}".format(self.mod_scheme)
        print "threshold:     {}".format(self.threshold)
        print "agc enable:    {}".format(self.agc_enable)
        print "fsk deviation: {} kHz".format(self.fsk_dev)
        print "psk const #:   {}".format(self.psk_const_num)
        print "rx gain:       {} dB".format(self.rx_gain)
        print "tx gain:       {} dB".format(self.tx_gain)


class BbParams():
    def __init__(self,
                 preamble = DEF_PREAMBLE_BYTES,
                 encoding = DEF_ENCODING,
                 symbol_time = DEF_SYMBOL_TIME,
                 ):
        self.set_preamble(preamble_bytes=preamble)
        self.encoding = encoding
        self.symbol_time = symbol_time

    # use this rather than set the preamble directly, as it takes care
    # of keeping the bit and byte-wise versions correct
    def set_preamble(self, preamble_bytes):
        self.preamble_bytes = preamble_bytes
        self.preamble = unpack_list(preamble_bytes)

    # output command bytes corresponding to current values; the goal
    # is to convert each field into an integer ranging from 0-256
    def params_to_bytes(self):
        cmd_bytes = self.preamble_bytes[:]
        cmd_bytes.append(scale_to_int(self.encoding, S_NONE))
        cmd_bytes.append(scale_to_int(self.symbol_time, S_SYMB_TIME))
        return cmd_bytes

    # take the command bytes and build a record from them
    def restore_from_cmd(self, cmd_bytes):
        # get the preamble in byte form
        preamble_len = len(cmd_bytes) - 2 # all but last two bytes are pre
        for i in xrange(preamble_len):
            self.preamble_bytes[i] = cmd_bytes[i]
        # update the bit-wise preamble
        self.preamble = unpack_list(self.preamble_bytes)

        self.encoding = restore_from_scaled(cmd_bytes[-2], S_NONE)
        self.symbol_time = restore_from_scaled(cmd_bytes[-1], S_SYMB_TIME)

    def print_vals(self):
        print "preamble: ",
        print self.preamble_bytes
        print "encoding:      {}".format(self.encoding)
        print "symbol time:   {} us".format(self.symbol_time)


# converts an input float to an integer factor of the provided
# scaling
def scale_to_int(input_val, scale_factor):
    if scale_factor == S_BOOL:
        return 1 if input_val else 0
    else:
        return int(1.0*input_val/scale_factor)


# converts an input byte to the scaled float or int
def restore_from_scaled(byte_val, scale_factor):
    if scale_factor == S_BOOL:
        return True if byte_val == 1 else False
    elif scale_factor == S_NONE:
        return int(byte_val)
    else:
        return float(byte_val*scale_factor)


# compute single-byte arithmetic checksum of an input array
def acs(byte_list):
    return sum(byte_list) % 256


# unpacks list of values into a list of 1s and 0s
def unpack_list(val_list, bit_count =  8):
    master_bit_list = []
    for v in val_list:
        # ensure that we don't have an illegal byte size
        if v >= 2**bit_count:
            print "ERROR: byte->bits conversion unsuccessful: > 255"

        # use this list to store the converted value
        b_list = bit_count * [0]
        for i in xrange(bit_count):
            exp = bit_count - 1 - i
            bit = 1 if v >= 2 ** exp else 0
            b_list[i] = bit
            v -= bit * 2 ** exp
        master_bit_list += b_list
    return master_bit_list