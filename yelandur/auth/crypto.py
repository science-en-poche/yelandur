from hashlib import sha512

from M2Crypto import EC, BIO


class ECVerifier(object):

    def __init__(self, device):
        self.device = device
        self._ecs = []
        bio = BIO.MemoryBuffer(str(self.device.pubkey_ec))
        self._ecs.append(EC.load_pub_key_bio(bio))

    def verify(self, datastring, sigfile):
        """Verify a signature allegedly performed by our MetaAppInstance."""
        digest = sha512(datastring).digest()
        sigfile.seek(0)
        sig = sigfile.read()
        return sum([bool(ec.verify_dsa_asn1(digest, sig))
                    for ec in self._ecs])
