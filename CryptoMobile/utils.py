# −*− coding: UTF−8 −*−
#/**
# * Software Name : CryptoMobile 
# * Version : 0.4
# *
# * Copyright 2017. Benoit Michau. ANSSI.
# *
# *--------------------------------------------------------
# * File Name : CryptoMobile/utils.py
# * Created : 2017-08-22
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

import sys
if sys.version_info[0] < 3:
    py_vers = 2
    int_types = (int, long)
else:
    py_vers = 3
    int_types = (int, )


MAX_UINT32 = 1<<32
MAX_UINT64 = 1<<64


if py_vers > 2:
    
    def xor_buf(b1, b2):
        return bytes([b1[i]^b2[i] for i in range(0, min(len(b1), len(b2)))])
    
    def int_from_bytes(b):
        return int.from_bytes(b, 'big')
    
    def bytes_from_int(i, length):
        return i.to_bytes(length, 'big')
    
else:
    
    def xor_buf(b1, b2):
        b1, b2 = bytearray(b1), bytearray(b2)
        return b''.join([chr(b1[i]^b2[i]) for i in range(0, min(len(b1), len(b2)))])

    def int_from_bytes(b):
        return reduce(lambda x, y: (x<<8) + y, map(ord, b))
    
    def bytes_from_int(i, length):
        return bytes(bytearray([(i>>o) & 0xff for o in range(8*(length-1), -1, -8)]))


# CryptoMobile-wide Exception handler
class CMException(Exception):
    """CryptoMobile specific exception
    """
    pass


# convinience function: change the content if required
def log(level='DBG', msg=''):
    # log wrapper
    print('[%s] %s' % (level, msg))

