"""App Attest attestation / assertion verification.

Follows Apple's "Validating apps that connect to your server":
https://developer.apple.com/documentation/devicecheck/validating-apps-that-connect-to-your-server
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
from dataclasses import dataclass

import cbor2
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.verification import (
    ExtensionPolicy,
    PolicyBuilder,
    Store,
    VerificationError as ChainError,
)

NONCE_OID = x509.ObjectIdentifier("1.2.840.113635.100.8.2")
AAGUID = {
    "development": b"appattestdevelop",
    "production": b"appattest" + b"\x00" * 7,
}
FLAG_ATTESTED_CREDENTIAL_DATA = 0x40


class VerificationError(Exception):
    """A check failed. `code` is a short machine-readable reason."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


@dataclass
class AuthData:
    rp_id_hash: bytes
    flags: int
    counter: int
    aaguid: bytes | None = None
    credential_id: bytes | None = None
    cose_key: dict | None = None
    extensions: dict | None = None


def parse_auth_data(data: bytes) -> AuthData:
    """Split authenticator data into its fields (WebAuthn layout)."""
    if len(data) < 37:
        raise VerificationError("bad_auth_data", "authenticator data too short")
    ad = AuthData(
        rp_id_hash=data[0:32],
        flags=data[32],
        counter=int.from_bytes(data[33:37], "big"),
    )
    pos = 37
    if ad.flags & FLAG_ATTESTED_CREDENTIAL_DATA:
        if len(data) < 55:
            raise VerificationError("bad_auth_data", "missing credential data")
        ad.aaguid = data[37:53]
        cred_len = int.from_bytes(data[53:55], "big")
        ad.credential_id = data[55 : 55 + cred_len]
        pos = 55 + cred_len
        stream = io.BytesIO(data[pos:])
        decoder = cbor2.CBORDecoder(stream)
        ad.cose_key = decoder.decode()
        pos += stream.tell()
    # Apple's sample sets only the AT flag (0x40) but still appends an
    # extensions map, so read any remaining bytes as CBOR.
    if pos < len(data):
        ad.extensions = cbor2.loads(data[pos:])
    return ad


def _read_der(buf: bytes, pos: int) -> tuple[int, bytes, int]:
    """Read one DER TLV at pos. Returns (tag, value, next_pos)."""
    tag = buf[pos]
    length = buf[pos + 1]
    pos += 2
    if length & 0x80:
        n = length & 0x7F
        length = int.from_bytes(buf[pos : pos + n], "big")
        pos += n
    return tag, buf[pos : pos + length], pos + length


def nonce_from_cred_cert(cert: x509.Certificate) -> bytes:
    """Extension 1.2.840.113635.100.8.2 = SEQUENCE { [1] { OCTET STRING } }."""
    try:
        ext = cert.extensions.get_extension_for_oid(NONCE_OID)
    except x509.ExtensionNotFound:
        raise VerificationError("no_nonce_ext", "credCert has no nonce extension")
    der = ext.value.value
    tag, seq, _ = _read_der(der, 0)
    if tag != 0x30:
        raise VerificationError("bad_nonce_ext", "not a SEQUENCE")
    tag, tagged, _ = _read_der(seq, 0)
    if tag != 0xA1:
        raise VerificationError("bad_nonce_ext", "missing [1] tag")
    tag, octets, _ = _read_der(tagged, 0)
    if tag != 0x04:
        raise VerificationError("bad_nonce_ext", "missing OCTET STRING")
    return octets


def verify_chain(x5c: list[bytes], root: x509.Certificate, now: dt.datetime):
    certs = [x509.load_der_x509_certificate(c) for c in x5c]
    verifier = (
        PolicyBuilder()
        .store(Store([root]))
        .time(now)
        .extension_policies(
            ca_policy=ExtensionPolicy.webpki_defaults_ca(),
            ee_policy=ExtensionPolicy.permit_all(),
        )
        .build_client_verifier()
    )
    try:
        verifier.verify(certs[0], certs[1:])
    except ChainError as e:
        raise VerificationError("bad_chain", f"certificate chain: {e}")
    return certs[0]


def validation_category(extensions: dict | None) -> int | None:
    """apple_validation_category_01. Apple's sample stores it as 4 bytes
    (01 00 00 00 for category 1), i.e. a little-endian UInt32."""
    if not extensions:
        return None
    value = extensions.get("apple_validation_category_01")
    if value is None:
        value = extensions.get("validationCategory")
    if isinstance(value, bytes):
        return int.from_bytes(value, "little")
    return value


def bundle_version(extensions: dict | None) -> str | None:
    if not extensions:
        return None
    return extensions.get("apple_bundle_version_01") or extensions.get(
        "bundleVersion"
    )


@dataclass
class AttestedKey:
    public_key: bytes  # X9.62 uncompressed point, 65 bytes
    receipt: bytes
    counter: int
    validation_category: int | None
    bundle_version: str | None


def verify_attestation(
    attestation: bytes,
    key_id: bytes,
    client_data_hash: bytes,
    app_id: str,
    environment: str,
    root: x509.Certificate,
    now: dt.datetime | None = None,
) -> AttestedKey:
    """Apple's attestation steps, in order. Raises VerificationError."""
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        obj = cbor2.loads(attestation)
        fmt = obj["fmt"]
        x5c = obj["attStmt"]["x5c"]
        receipt = obj["attStmt"]["receipt"]
        auth_data = obj["authData"]
    except Exception:
        raise VerificationError("bad_format", "not an App Attest CBOR object")
    if fmt != "apple-appattest":
        raise VerificationError("bad_format", f"unexpected fmt {fmt!r}")

    # 1. x5c chains up to the Apple App Attestation Root CA.
    cred_cert = verify_chain(x5c, root, now)

    # 2-3. nonce = SHA256(authData || clientDataHash)
    nonce = sha256(auth_data + client_data_hash)

    # 4. Compare with the octet string in credCert extension.
    if nonce_from_cred_cert(cred_cert) != nonce:
        raise VerificationError("nonce_mismatch", "nonce does not match")

    # 5. SHA256(public key as X9.62 uncompressed point) == key id.
    public_key = cred_cert.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    if sha256(public_key) != key_id:
        raise VerificationError("key_id_mismatch", "key id does not match")

    ad = parse_auth_data(auth_data)

    # 6. RP ID hash == SHA256(App ID)
    if ad.rp_id_hash != sha256(app_id.encode()):
        raise VerificationError("rp_id_mismatch", "App ID does not match")

    # 7. counter == 0
    if ad.counter != 0:
        raise VerificationError("bad_counter", "counter is not 0")

    # 8. aaguid matches the environment.
    if ad.aaguid != AAGUID[environment]:
        raise VerificationError("bad_aaguid", f"aaguid {ad.aaguid!r}")

    # 9. credentialId == key id
    if ad.credential_id != key_id:
        raise VerificationError("cred_id_mismatch", "credentialId != key id")

    # 10-11. extensions are returned; the caller applies its policy.
    return AttestedKey(
        public_key=public_key,
        receipt=receipt,
        counter=0,
        validation_category=validation_category(ad.extensions),
        bundle_version=bundle_version(ad.extensions),
    )


@dataclass
class VerifiedAssertion:
    counter: int
    validation_category: int | None
    bundle_version: str | None


def verify_assertion(
    assertion: bytes,
    client_data: bytes,
    public_key: bytes,
    app_id: str,
    previous_counter: int,
) -> VerifiedAssertion:
    """Apple's assertion steps 1-5. The caller checks the challenge
    (step 6) and stores the new counter."""
    try:
        obj = cbor2.loads(assertion)
        signature = obj["signature"]
        auth_data = obj["authenticatorData"]
    except Exception:
        raise VerificationError("bad_format", "not an assertion CBOR object")

    # 1. clientDataHash = SHA256(clientData)
    client_data_hash = sha256(client_data)
    # 2. nonce = SHA256(authenticatorData || clientDataHash)
    nonce = sha256(auth_data + client_data_hash)

    # 3. The signature is valid for nonce. ECDSA-SHA256 over the nonce
    #    bytes, the same as CryptoKit isValidSignature(_:for: Data).
    key = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(), public_key
    )
    try:
        key.verify(signature, nonce, ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        raise VerificationError("bad_signature", "signature is not valid")

    ad = parse_auth_data(auth_data)

    # 4. RP ID hash == SHA256(App ID)
    if ad.rp_id_hash != sha256(app_id.encode()):
        raise VerificationError("rp_id_mismatch", "App ID does not match")

    # 5. counter must grow.
    if ad.counter <= previous_counter:
        raise VerificationError("replayed_counter", "counter did not grow")

    return VerifiedAssertion(
        counter=ad.counter,
        validation_category=validation_category(ad.extensions),
        bundle_version=bundle_version(ad.extensions),
    )
