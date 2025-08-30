# −*− coding: UTF−8 −*−
#/**
# * Software Name : CryptoMobile 
# * Version : 0.4
# *
# * Copyright 2018. Benoit Michau. P1Sec.
# *
# *--------------------------------------------------------
# * File Name : CryptoMobile/TUAK.py
# * Created : 2018-12-20
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

########################################################
# CryptoMobile python toolkit
#
# TUAK authentication algorithm
# as proposed by 3GPP as an alternative to Milenage
# algorithm based on SHA-3 (more exactly its KeccakP-1600 permutation)
# see 3GPP TS 35.231, 232 and 233
#######################################################

from binascii import *

import sys
python_version = sys.version_info[0]

import pykeccakp1600 as kec
keccakp1600 = kec.pykeccakp1600

from .utils        import *


__all__ = ['TUAK', 'make_TOPc']


def make_TOPc( K, TOP, ALGONAME, KeccakIterations ):
    """derives TOP with K to produce TOPc
    requires the TUAK global parameters ALGONAME and KeccakIterations"""
    if len(K) == 16:
        INSTANCE = b'\x00'
    else:
        #len(K) == 32
        INSTANCE = b'\x01'
    
    INOUT = []
    INOUT.append( TOP[::-1] )
    INOUT.append( INSTANCE[::-1] )
    INOUT.append( ALGONAME[::-1] )
    INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
    INOUT.append( K[::-1] )
    if len(K) == 16:
        INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
    # add padding
    INOUT.append( b'\x1f\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x80' )
    INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'\
                  b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
    INOUT = b''.join(INOUT)
    
    for i in range(KeccakIterations):
        INOUT = keccakp1600(INOUT)
    return INOUT[:32][::-1]


###
# 3GPP TUAK authentication algorithm
###

class TUAK:
    """TUAK cryptographic functions, based on KeccakP-1600
    
    see 3GPP TS 35.231
    """
    
    ALGONAME = b'TUAK1.0'
    
    KeccakIterations = 1
    
    ####################
    # OPERATOR SETTING #
    ####################
    # defined operator settings for the length of the differents outputs
    LEN_MAC  = 64  # can be 64, 128 or 256 bit
    LEN_RES  = 64  # can be 32, 64, 128 or 256 bit
    LEN_CK   = 128 # can be 128 or 256 bit
    LEN_IK   = 128 # can be 128 or 256 bit
    # input length for K: 128 or 256 bit
    # input length for TOP: 256 bit
    
    
    def __init__(self, TOP):
        self.TOP  = TOP
        self.TOPc = None
    
    def make_topc(self, K, TOP=None):
        """return the TOPc value derived from K, TOP and the TUAK configuration
        if TOP is None, relies on the instance self.TOP value
        """
        if TOP is None:
            return make_TOPc(K, self.TOP, self.ALGONAME, self.KeccakIterations)
        else:
            return make_TOPc(K, TOP, self.ALGONAME, self.KeccakIterations)
    
    def set_topc(self, TOPc):
        """set TOPc and save some Keccak rounds in f1, f1star, f2345, f5star
        when producing several vectors for a single subscriber
        """
        self.TOPc = TOPc
    
    def unset_opc(self):
        self.TOPc = None
    
    ##################
    # TUAK FUNCTIONS #
    ##################
    
    def f1(self, K, RAND, SQN, AMF, TOP=None):
        """return MAC_A [8, 16 or 32 bytes buffer] or None on error
        """
        if len(K) not in (16, 32) or len(RAND) != 16 or len(SQN) != 6 or len(AMF) != 2:
            log('ERR', 'TUAK.f1: invalid args')
            return None
        
        if self.LEN_MAC == 64:
            INSTANCE = 0x08
            off = 8
        elif self.LEN_MAC == 128:
            INSTANCE = 0x10
            off = 16
        else:
            #self.LEN_MAC == 256
            INSTANCE = 0x20
            off = 32
        if len(K) == 32:
            INSTANCE += 1
        if python_version > 2:
            INSTANCE = bytes([INSTANCE])
        else:
            INSTANCE = chr(INSTANCE)
        
        if self.TOPc is not None:
            TOPc = self.TOPc
        else:
            TOPc = self.make_topc(K, TOP)
        
        INOUT = []
        INOUT.append( TOPc[::-1] )
        INOUT.append( INSTANCE[::-1] )
        INOUT.append( self.ALGONAME[::-1] )
        INOUT.append( RAND[::-1] )
        INOUT.append( AMF[::-1] )
        INOUT.append( SQN[::-1] )
        INOUT.append( K[::-1] )
        if len(K) == 16:
            INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
        # add padding
        INOUT.append( b'\x1f\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x80' )
        INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'\
                      b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
        INOUT = b''.join(INOUT)
        
        for i in range(self.KeccakIterations):
            INOUT = keccakp1600(INOUT)
        return INOUT[:off][::-1]
    
    def f1star(self, K, RAND, SQN, AMF, TOP=None):
        """return MAC_S [8, 16 or 32 bytes buffer] or None on error
        """
        if len(K) not in (16, 32) or len(RAND) != 16 or len(SQN) != 6 or len(AMF) != 2:
            log('ERR', 'TUAK.f1star: invalid args')
            return None
        
        if self.LEN_MAC == 64:
            INSTANCE = 0x88
            off = 8
        elif self.LEN_MAC == 128:
            INSTANCE = 0x90
            off = 16
        else:
            #self.LEN_MAC == 256
            INSTANCE = 0xa0
            off = 32
        if len(K) == 32:
            INSTANCE += 1
        if python_version > 2:
            INSTANCE = bytes([INSTANCE])
        else:
            INSTANCE = chr(INSTANCE)
        
        if self.TOPc is not None:
            TOPc = self.TOPc
        else:
            TOPc = self.make_topc(K, TOP)
        
        INOUT = []
        INOUT.append( TOPc[::-1] )
        INOUT.append( INSTANCE[::-1] )
        INOUT.append( self.ALGONAME[::-1] )
        INOUT.append( RAND[::-1] )
        INOUT.append( AMF[::-1] )
        INOUT.append( SQN[::-1] )
        INOUT.append( K[::-1] )
        if len(K) == 16:
            INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
        # add padding
        INOUT.append( b'\x1f\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x80' )
        INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'\
                      b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
        INOUT = b''.join(INOUT)
        
        for i in range(self.KeccakIterations):
            INOUT = keccakp1600(INOUT)
        return INOUT[:off][::-1]
    
    def f2345(self, K, RAND, TOP=None):
        """return RES [4, 8, 16 or 32], CK [16 or 32], IK [16 or 32] and AK [6] bytes buffers or None on error
        """
        if len(K) not in (16, 32) or len(RAND) != 16:
            log('ERR', 'TUAK.f234: invalid args')
            return None
        
        if self.LEN_RES == 32:
            INSTANCE = 0x40
            offres = 4
        elif self.LEN_RES == 64:
            INSTANCE = 0x48
            offres = 8
        elif self.LEN_RES == 128:
            INSTANCE = 0x50
            offres = 16
        else:
            #self.LEN_RES == 256
            INSTANCE = 0x60
            offres = 32
        if self.LEN_CK == 256:
            INSTANCE += 4
            offck = 32
        else:
            offck = 16
        if self.LEN_IK == 256:
            INSTANCE += 2
            offik = 32
        else:
            offik = 16
        if len(K) == 32:
            INSTANCE += 1
        
        if python_version > 2:
            INSTANCE = bytes([INSTANCE])
        else:
            INSTANCE = chr(INSTANCE)
        
        if self.TOPc is not None:
            TOPc = self.TOPc
        else:
            TOPc = self.make_topc(K, TOP)
        
        INOUT = []
        INOUT.append( TOPc[::-1] )
        INOUT.append( INSTANCE[::-1] )
        INOUT.append( self.ALGONAME[::-1] )
        INOUT.append( RAND[::-1] )
        INOUT.append( b'\0\0\0\0\0\0\0\0' )
        INOUT.append( K[::-1] )
        if len(K) == 16:
            INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
        # add padding
        INOUT.append( b'\x1f\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x80' )
        INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'\
                      b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
        INOUT = b''.join(INOUT)
        
        for i in range(self.KeccakIterations):
            INOUT = keccakp1600(INOUT)
        return INOUT[:offres][::-1], INOUT[32:32+offck][::-1], INOUT[64:64+offik][::-1], INOUT[96:102][::-1]
    
    def f5star(self, K, RAND, TOP=None):
        """return AK [6 bytes buffer] or None on error
        """
        if len(K) not in (16, 32) or len(RAND) != 16:
            log('ERR', 'TUAK.f5star: invalid args')
            return None
        
        INSTANCE = 0xc0
        if len(K) == 32:
            INSTANCE += 1
        
        if python_version > 2:
            INSTANCE = bytes([INSTANCE])
        else:
            INSTANCE = chr(INSTANCE)
        
        if self.TOPc is not None:
            TOPc = self.TOPc
        else:
            TOPc = self.make_topc(K, TOP)
        
        INOUT = []
        INOUT.append( TOPc[::-1] )
        INOUT.append( INSTANCE[::-1] )
        INOUT.append( self.ALGONAME[::-1] )
        INOUT.append( RAND[::-1] )
        INOUT.append( b'\0\0\0\0\0\0\0\0' )
        INOUT.append( K[::-1] )
        if len(K) == 16:
            INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
        # add padding
        INOUT.append( b'\x1f\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\x80' )
        INOUT.append( b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0'\
                      b'\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0\0' )
        INOUT = b''.join(INOUT)
        
        for i in range(self.KeccakIterations):
            INOUT = keccakp1600(INOUT)
        return INOUT[96:102][::-1]

