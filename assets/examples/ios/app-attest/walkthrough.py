"""Print every attestation step for Apple's sample attestation object.

Run fetch_apple_files.py first. The sample's credCert expired on
2026-04-23, so the chain is checked at 2026-04-21 (the sample's time).
"""

import base64
import datetime as dt

import cbor2
from cryptography import x509
from cryptography.hazmat.primitives import serialization

from appattest_verify import (
    nonce_from_cred_cert, parse_auth_data, sha256, validation_category,
    verify_attestation, verify_chain, VerificationError,
)

APP_ID = "1234567890.com.example.myapp"
KEY_ID = base64.b64decode("zgSY9YSD+7TaDXssY6WlOPVS1K3Lmk+pFhlcSWE+ZV0=")
CDH = b"example_server_challenge"  # see the note in test_verify.py
AT = dt.datetime(2026, 4, 21, tzinfo=dt.timezone.utc)
b64 = lambda b: base64.b64encode(b).decode()

raw = base64.b64decode(open("apple_sample_attestation.b64").read())
root = x509.load_pem_x509_certificate(
    open("Apple_App_Attestation_Root_CA.pem", "rb").read())
obj = cbor2.loads(raw)
print("fmt:", obj["fmt"], "| x5c:", len(obj["attStmt"]["x5c"]),
      "| receipt:", len(obj["attStmt"]["receipt"]), "bytes",
      "| authData:", len(obj["authData"]), "bytes")

cred = verify_chain(obj["attStmt"]["x5c"], root, AT)
print("1. chain OK at", AT.date(), "| leaf valid",
      cred.not_valid_before_utc, "~", cred.not_valid_after_utc)
try:
    verify_chain(obj["attStmt"]["x5c"], root,
                 dt.datetime(2026, 11, 28, tzinfo=dt.timezone.utc))
except VerificationError as e:
    print("   same chain on 2026-11-28:", e.code)

nonce = sha256(obj["authData"] + CDH)
print("2-3. nonce:", b64(nonce))
print("4. credCert nonce:", b64(nonce_from_cred_cert(cred)))
point = cred.public_key().public_bytes(
    serialization.Encoding.X962,
    serialization.PublicFormat.UncompressedPoint)
print("5. SHA256(X9.62 point):", b64(sha256(point)), "| keyId:", b64(KEY_ID))
ad = parse_auth_data(obj["authData"])
print("6. RP ID hash:", b64(ad.rp_id_hash))
print("   SHA256(App ID):", b64(sha256(APP_ID.encode())))
print("7. counter:", ad.counter, "| flags:", hex(ad.flags))
print("8. aaguid:", ad.aaguid)
print("9. credentialId:", b64(ad.credential_id))
print("10-11. extensions:", ad.extensions,
      "-> category", validation_category(ad.extensions))

key = verify_attestation(raw, KEY_ID, CDH, APP_ID, "production", root, AT)
print("verify_attestation: OK, public key", len(key.public_key), "bytes")
