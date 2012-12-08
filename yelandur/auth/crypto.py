from hashlib import sha256, sha512

from M2Crypto import EC, BIO


def sha256_hash(string):
    """Hash a string with the sha256 function."""
    sha = sha256()
    sha.update(string)
    return sha.digest()


def sha256_hash_hex(string):
    """Hash a string with the sha256 function and return the hex
    representation."""
    sha = sha256()
    sha.update(string)
    return sha.hexdigest()


def sha512_hash(string):
    """Hash a string with the sha512 function."""
    sha = sha512()
    sha.update(string)
    return sha.digest()


def sha512_hash_hex(string):
    """Hash a string with the sha512 function and return the hex
    representation."""
    sha = sha512()
    sha.update(string)
    return sha.hexdigest()


class ECVerifier(object):

    def __init__(self, device):
        """Initialize the structure with a device.

        Arguments:
          * ``device``: the device whose public key is used to verify
            signatures

        """

        self.device = device
        self._ecs = []
        bio = BIO.MemoryBuffer(str(self.device.pubkey_ec))
        self._ecs.append(EC.load_pub_key_bio(bio))

    def verify(self, datastring, sigfile):
        """Verify a signature allegedly performed by our MetaAppInstance."""
        digest = sha512_hash(datastring)
        sigfile.seek(0)
        sig = sigfile.read()
        return sum([bool(ec.verify_dsa_asn1(digest, sig))
                    for ec in self._ecs])
