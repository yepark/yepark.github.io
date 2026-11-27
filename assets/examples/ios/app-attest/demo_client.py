"""SYNTHETIC client for trying the server with curl (no iPhone).

  python demo_client.py init                 # fake CA -> demo/root.pem
  python demo_client.py attest CHALLENGE     # prints /attest JSON body
  python demo_client.py assert CHALLENGE N   # writes demo/body.json,
                                             # prints the assertion header
"""

import base64
import json
import pathlib
import sys

from cryptography.hazmat.primitives import serialization as s

import synthetic

APP_ID = "ABCDE12345.com.example.checkin"
D = pathlib.Path("demo")


def save_key(path, key):
    path.write_bytes(key.private_bytes(
        s.Encoding.PEM, s.PrivateFormat.PKCS8, s.NoEncryption()))


def load_key(path):
    return s.load_pem_private_key(path.read_bytes(), None)


cmd = sys.argv[1]
if cmd == "init":
    D.mkdir(exist_ok=True)
    ca = synthetic.FakeCA()
    (D / "root.pem").write_bytes(ca.root_pem())
    (D / "int.pem").write_bytes(ca.intermediate.public_bytes(s.Encoding.PEM))
    save_key(D / "int.key", ca.int_key)
    print("wrote demo/root.pem")
elif cmd == "attest":
    from cryptography import x509
    ca = synthetic.FakeCA.__new__(synthetic.FakeCA)
    ca.intermediate = x509.load_pem_x509_certificate(
        (D / "int.pem").read_bytes())
    ca.int_key = load_key(D / "int.key")
    cdh = synthetic.sha256(base64.b64decode(sys.argv[2]))
    device, key_id, att = synthetic.make_attestation(ca, APP_ID, cdh)
    save_key(D / "device.key", device)
    (D / "key_id").write_text(synthetic.b64(key_id))
    print(json.dumps({"key_id": synthetic.b64(key_id),
                      "attestation": synthetic.b64(att),
                      "challenge": sys.argv[2]}))
elif cmd == "assert":
    body = json.dumps({"challenge": sys.argv[2], "userID": "u1",
                       "date": "2026-11-28"}).encode()
    (D / "body.json").write_bytes(body)
    a = synthetic.make_assertion(load_key(D / "device.key"), body,
                                 APP_ID, int(sys.argv[3]))
    print(synthetic.b64(a))
