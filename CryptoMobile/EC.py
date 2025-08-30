# −*− coding: UTF−8 −*−
#/**
# * Software Name : CryptoMobile 
# * Version : 0.4
# *
# * Copyright 2020. Benoit Michau. P1Sec.
# *
# *--------------------------------------------------------
# * File Name : CryptoMobile/EC.py
# * Created : 2020-01-21
# * Authors : Benoit Michau 
# *--------------------------------------------------------
#*/

__all__ = ['X25519', 'ECDH_SECP256R1', 'KDF']

from .utils import *

# this is a wrapper around the cryptography Python librar and its elliptic curve
# module for ECDH computation
# cryptography is a wrapper around openssl, recent versions support both X25519 and secp256r1

try:
    from cryptography.hazmat.backends                       import default_backend
    from cryptography.hazmat.primitives                     import serialization
    from cryptography.hazmat.primitives.asymmetric          import ec
    from cryptography.hazmat.primitives.asymmetric.x25519   import X25519PrivateKey, X25519PublicKey
    from cryptography.hazmat.primitives.kdf.x963kdf         import X963KDF
    from cryptography.hazmat.primitives                     import hashes
except ImportError:
    raise(ImportError('missing ECC backend: requires cryptography Python library'))
else:
    _backend = default_backend()


class X25519(object):
    """wrapper around Python cryptography library to handle a Diffie-Hellman
    exchange over a Curve25519 elliptic curve
    
    private key and public key are handle as simple bytes buffer
    """
    
    def __init__(self, loc_privkey=None):
        if not loc_privkey:
            self.generate_keypair()
        else:
            self.PrivKey = X25519PrivateKey.from_private_bytes(loc_privkey)
    
    def generate_keypair(self):
        self.PrivKey = X25519PrivateKey.generate()
    
    def get_pubkey(self):
        return self.PrivKey.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw)
    
    def get_privkey(self, encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw):
        return self.PrivKey.private_bytes(
            encoding=encoding,
            format=format,
            encryption_algorithm=serialization.NoEncryption())
    
    def generate_sharedkey(self, ext_pubkey):
        ExtPubKey = X25519PublicKey.from_public_bytes(ext_pubkey)
        return self.PrivKey.exchange(ExtPubKey)


class ECDH_SECP256R1(object):
    """wrapper around Python cryptography library to handle an ECDH  exchange over 
    a NIST secp256r1 elliptic curve
    
    private key and public key are handle as simple bytes buffer,
    private key is the private value encoded as is
    public key is the compressed point value encoded according to ANSI X9.62
    """
    
    def __init__(self, loc_privkey=None):
        if not loc_privkey:
            self.generate_keypair()
        else:
            self.PrivKey = ec.derive_private_key(
                int_from_bytes(loc_privkey),
                ec.SECP256R1(),
                backend=_backend)
    
    def generate_keypair(self):
        self.PrivKey = ec.generate_private_key(
            curve=ec.SECP256R1(),
            backend=_backend)
    
    def get_pubkey(self):
        return self.PrivKey.public_key().public_bytes(
            format=serialization.PublicFormat.CompressedPoint,
            encoding=serialization.Encoding.X962)
    
    def get_privkey(self):
        return bytes_from_int(self.PrivKey.private_numbers().private_value, 32)

    def get_privkey_pem(self):
        return self.PrivKey.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption())

    def generate_sharedkey(self, ext_pubkey):
        ExtPubKey = ec.EllipticCurvePublicKey.from_encoded_point(
            curve=ec.SECP256R1(),
            data=ext_pubkey)
        return self.PrivKey.exchange(ec.ECDH(), ExtPubKey)


def KDF(sharedinfo, sharedkey):
    return X963KDF(
         algorithm=hashes.SHA256(),
         length=64, # 16 bytes AES key, 16 bytes AES CTR IV, 32 bytes HMAC-SHA-256 key
         sharedinfo=sharedinfo,
         backend=_backend).derive(sharedkey)
