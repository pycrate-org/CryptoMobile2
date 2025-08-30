# −*− coding: UTF−8 −*−
#/**
# * Software Name : CryptoMobile 
# * Version : 0.4
# *
# * Copyright 2020. Benoit Michau. P1Sec.
# *
# *--------------------------------------------------------
# * File Name : CryptoMobile/ECIES.py
# * Created : 2020-01-21
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

#__all__ = ['ECIES_UE', 'ECIES_HN']


import hashlib  # for SHA-256
import hmac     # HMAC–SHA-256
from struct     import unpack
from binascii   import hexlify

from .AES import AES_CTR
from .EC  import *


########################################################
# CryptoMobile python toolkit
#
# ECIES: Elliptic Curve Integrated Encryption Scheme
# as defined by 3GPP to protect subscriber's fixed identity SUPI into SUCI
# TS 33.501, section 6.12 and annex C
#
# Based on an elliptic curve algorithm:
# - profile A: Curve25519 / X25519
# - profile B: NIST secp256r1
# and ANSI-X9.63-KDF, SHA-256 hash function, HMAC–SHA-256 MAC function and
# AES–128 in CTR mode encryption function
#######################################################


class ECIES_UE(object):
    """ECIES_UE handles the ECIES computation required on the UE side to
    protect its fixed identity SUPI into a SUCI
    """
    
    def __init__(self, profile='A'):
        if profile == 'A':
            self.EC = X25519()
        elif profile == 'B':
            self.EC = ECDH_SECP256R1()
        else:
            raise(CMException('unknown ECIES profile %s' % profile))
    
    def generate_sharedkey(self, hn_pub_key, fresh=True):
        """generates a shared keystream based on a UE ephemeral keypair (regenerated
        if fresh is True) and the HN public key
        """
        if fresh:
            # regenerate a new UE ephemeral keypair
            self.EC.generate_keypair()
        # get the UE ephemeral pubkey
        self.EK = self.EC.get_pubkey()
        # generate the shared keystream by mixing the UE ephemeral key with HN pubkey
        self.SK = KDF(self.EK, self.EC.generate_sharedkey(hn_pub_key))
    
    def protect(self, plaintext):
        """protects the given plaintext and returns a 3-tuple of bytes:
        UE ephemeral pubkey, ciphertext, MAC
        """
        aes_key, aes_nonce, aes_cnt, mac_key = (
            self.SK[:16],
            self.SK[16:24],
            unpack('>Q', self.SK[24:32])[0],
            self.SK[32:64]
            )
        # encryption
        aes = AES_CTR(aes_key, aes_nonce, aes_cnt)
        ciphertext = aes.encrypt(plaintext)
        # MAC
        mac = hmac.new(mac_key, ciphertext, hashlib.sha256).digest()
        #
        return self.EK, ciphertext, mac[0:8]


class ECIES_HN(object):
    """ECIES_HN handles the ECIES computation required on the Home Network side
    to unprotect a subscriber's SUCI into a fixed identity SUPI
    """
    
    def __init__(self, hn_priv_key, profile='A'):
        if profile == 'A':
            self.EC = X25519(loc_privkey=hn_priv_key)
        elif profile == 'B':
            self.EC = ECDH_SECP256R1(loc_privkey=hn_priv_key)
        else:
            raise(CMException('unknown ECIES profile %s' % profile))
    
    def unprotect(self, ue_pubkey, ciphertext, mac):
        """unprotects the given ciphertext using associated MAC and UE ephemeral 
        public key
        
        returns the decrypted cleartext bytes buffer or None if MAC verification 
        failed
        """
        SK = KDF(ue_pubkey, self.EC.generate_sharedkey(ue_pubkey))
        aes_key, aes_nonce, aes_cnt, mac_key = (
            SK[:16],
            SK[16:24],
            unpack('>Q', SK[24:32])[0],
            SK[32:64]
            )
        #
        # verify MAC
        mac_hn = hmac.new(mac_key, ciphertext, hashlib.sha256).digest()
        mac_verif = hmac.compare_digest(mac_hn[0:8], mac)
        # decrypt
        aes = AES_CTR(aes_key, aes_nonce, aes_cnt)
        cleartext = aes.decrypt(ciphertext)
        #
        if mac_verif:
            return cleartext
        else:
            return None

