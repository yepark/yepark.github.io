"""SYNTHETIC test data. Not from Apple and not from a device.

Builds a fake CA chain and fake App Attest objects with our own keys so
the server code can be exercised without an iPhone. The fake root must be
passed to the verifier in place of Apple's root CA.
"""

from __future__ import annotations

import base64
import datetime as dt
import hashlib

import cbor2
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

NONCE_OID = x509.ObjectIdentifier("1.2.840.113635.100.8.2")


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def _name(cn: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, cn)])


def _cert(subject, issuer, pub, signer, ca: bool, ski_of, aki_of, extra=()):
    now = dt.datetime.now(dt.timezone.utc)
    b = (
        x509.CertificateBuilder()
        .subject_name(_name(subject))
        .issuer_name(_name(issuer))
        .public_key(pub)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - dt.timedelta(days=1))
        .not_valid_after(now + dt.timedelta(days=30))
        .add_extension(
            x509.BasicConstraints(ca=ca, path_length=None), critical=True
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ski_of), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(aki_of),
            critical=False,
        )
    )
    if ca:
        b = b.add_extension(
            x509.KeyUsage(False, False, False, False, False, True, True,
                          False, False),
            critical=True,
        )
    for ext in extra:
        b = b.add_extension(ext, critical=False)
    return b.sign(signer, hashes.SHA256())


class FakeCA:
    def __init__(self):
        self.root_key = ec.generate_private_key(ec.SECP384R1())
        self.int_key = ec.generate_private_key(ec.SECP384R1())
        rp = self.root_key.public_key()
        ip = self.int_key.public_key()
        self.root = _cert("SYNTHETIC Root", "SYNTHETIC Root", rp,
                          self.root_key, True, rp, rp)
        self.intermediate = _cert("SYNTHETIC CA 1", "SYNTHETIC Root", ip,
                                  self.root_key, True, ip, rp)

    def root_pem(self) -> bytes:
        return self.root.public_bytes(serialization.Encoding.PEM)


def _nonce_extension(nonce: bytes) -> x509.UnrecognizedExtension:
    # SEQUENCE { [1] { OCTET STRING nonce } }
    inner = b"\x04\x20" + nonce
    tagged = b"\xa1" + bytes([len(inner)]) + inner
    der = b"\x30" + bytes([len(tagged)]) + tagged
    return x509.UnrecognizedExtension(NONCE_OID, der)


def auth_data(app_id: str, counter: int, flags: int = 0x40,
              aaguid: bytes = b"", cred_id: bytes = b"",
              cose: bytes = b"", extensions: dict | None = None) -> bytes:
    out = sha256(app_id.encode()) + bytes([flags])
    out += counter.to_bytes(4, "big")
    if flags & 0x40:
        out += aaguid + len(cred_id).to_bytes(2, "big") + cred_id + cose
    if extensions is not None:
        out += cbor2.dumps(extensions)
    return out


def make_attestation(ca: FakeCA, app_id: str, client_data_hash: bytes,
                     aaguid: bytes = b"appattestdevelop",
                     category: int = 3):
    """Returns (device_private_key, key_id_bytes, attestation_bytes)."""
    device = ec.generate_private_key(ec.SECP256R1())
    point = device.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    key_id = sha256(point)
    nums = device.public_key().public_numbers()
    cose = cbor2.dumps({1: 2, 3: -7, -1: 1,
                        -2: nums.x.to_bytes(32, "big"),
                        -3: nums.y.to_bytes(32, "big")})
    ad = auth_data(app_id, 0, 0x40, aaguid, key_id, cose,
                   {"apple_bundle_version_01": "1",
                    "apple_validation_category_01":
                        category.to_bytes(4, "little")})
    nonce = sha256(ad + client_data_hash)
    leaf = _cert(key_id.hex(), "SYNTHETIC CA 1", device.public_key(),
                 ca.int_key, False, device.public_key(),
                 ca.int_key.public_key(), [_nonce_extension(nonce)])
    der = serialization.Encoding.DER
    obj = {
        "fmt": "apple-appattest",
        "attStmt": {
            "x5c": [leaf.public_bytes(der),
                    ca.intermediate.public_bytes(der)],
            "receipt": b"SYNTHETIC-RECEIPT",
        },
        "authData": ad,
    }
    return device, key_id, cbor2.dumps(obj)


def make_assertion(device: ec.EllipticCurvePrivateKey, client_data: bytes,
                   app_id: str, counter: int) -> bytes:
    ad = auth_data(app_id, counter, flags=0x00)
    nonce = sha256(ad + sha256(client_data))
    sig = device.sign(nonce, ec.ECDSA(hashes.SHA256()))
    return cbor2.dumps({"signature": sig, "authenticatorData": ad})


def b64(b: bytes) -> str:
    return base64.b64encode(b).decode()
