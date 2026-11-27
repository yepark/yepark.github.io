import base64
import datetime as dt
import pathlib

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import ec

import synthetic
from appattest_verify import (
    VerificationError, sha256, verify_assertion, verify_attestation,
)

HERE = pathlib.Path(__file__).parent
ROOT = HERE / "Apple_App_Attestation_Root_CA.pem"
SAMPLE = HERE / "apple_sample_attestation.b64"
need_apple = pytest.mark.skipif(
    not (ROOT.exists() and SAMPLE.exists()),
    reason="run fetch_apple_files.py first")

# Values from Apple's "Attestation Object Validation Guide".
APPLE_APP_ID = "1234567890.com.example.myapp"
APPLE_KEY_ID = base64.b64decode(
    "zgSY9YSD+7TaDXssY6WlOPVS1K3Lmk+pFhlcSWE+ZV0=")
# The sample's nonce is reproduced only when the raw challenge bytes are
# used as clientDataHash (not SHA256 of them).
APPLE_CDH = b"example_server_challenge"
# credCert is valid 2026-04-20 18:13:12Z .. 2026-04-23 18:13:12Z.
APPLE_TIME = dt.datetime(2026, 4, 21, tzinfo=dt.timezone.utc)


def apple(**kw):
    args = dict(
        attestation=base64.b64decode(SAMPLE.read_text()),
        key_id=APPLE_KEY_ID, client_data_hash=APPLE_CDH,
        app_id=APPLE_APP_ID, environment="production",
        root=x509.load_pem_x509_certificate(ROOT.read_bytes()),
        now=APPLE_TIME)
    args.update(kw)
    return verify_attestation(**args)


@need_apple
def test_apple_sample_passes_at_its_time():
    key = apple()
    assert sha256(key.public_key) == APPLE_KEY_ID
    assert key.validation_category == 1
    assert key.bundle_version == "1"
    assert len(key.receipt) == 3977


@need_apple
def test_apple_sample_expired_today():
    with pytest.raises(VerificationError) as e:
        apple(now=dt.datetime(2026, 11, 28, tzinfo=dt.timezone.utc))
    assert e.value.code == "bad_chain"


@need_apple
@pytest.mark.parametrize("change, code", [
    ({"client_data_hash": sha256(APPLE_CDH)}, "nonce_mismatch"),
    ({"key_id": b"\x00" * 32}, "key_id_mismatch"),
    ({"app_id": "1234567890.com.example.other"}, "rp_id_mismatch"),
    ({"environment": "development"}, "bad_aaguid"),
])
def test_apple_sample_rejects(change, code):
    with pytest.raises(VerificationError) as e:
        apple(**change)
    assert e.value.code == code


# ---- SYNTHETIC: our own keys, not Apple data ----

APP_ID = "ABCDE12345.com.example.checkin"


def test_synthetic_attestation_passes_with_fake_root():
    ca = synthetic.FakeCA()
    cdh = sha256(b"challenge")
    _, key_id, att = synthetic.make_attestation(ca, APP_ID, cdh)
    key = verify_attestation(att, key_id, cdh, APP_ID, "development",
                             ca.root)
    assert key.validation_category == 3


def test_synthetic_attestation_rejected_by_apple_root():
    if not ROOT.exists():
        pytest.skip("no Apple root")
    ca = synthetic.FakeCA()
    cdh = sha256(b"challenge")
    _, key_id, att = synthetic.make_attestation(ca, APP_ID, cdh)
    apple_root = x509.load_pem_x509_certificate(ROOT.read_bytes())
    with pytest.raises(VerificationError) as e:
        verify_attestation(att, key_id, cdh, APP_ID, "development",
                           apple_root)
    assert e.value.code == "bad_chain"


@pytest.fixture
def device():
    return ec.generate_private_key(ec.SECP256R1())


def point(device):
    from cryptography.hazmat.primitives import serialization as s
    return device.public_key().public_bytes(
        s.Encoding.X962, s.PublicFormat.UncompressedPoint)


def test_assertion_valid(device):
    data = b'{"challenge":"abc"}'
    a = synthetic.make_assertion(device, data, APP_ID, counter=1)
    r = verify_assertion(a, data, point(device), APP_ID, previous_counter=0)
    assert r.counter == 1


def test_assertion_wrong_signature(device):
    other = ec.generate_private_key(ec.SECP256R1())
    data = b'{"challenge":"abc"}'
    a = synthetic.make_assertion(other, data, APP_ID, counter=1)
    with pytest.raises(VerificationError) as e:
        verify_assertion(a, data, point(device), APP_ID, 0)
    assert e.value.code == "bad_signature"


def test_assertion_body_changed(device):
    a = synthetic.make_assertion(device, b'{"points":1}', APP_ID, 1)
    with pytest.raises(VerificationError) as e:
        verify_assertion(a, b'{"points":999}', point(device), APP_ID, 0)
    assert e.value.code == "bad_signature"


def test_assertion_replayed_counter(device):
    data = b'{"challenge":"abc"}'
    a = synthetic.make_assertion(device, data, APP_ID, counter=5)
    with pytest.raises(VerificationError) as e:
        verify_assertion(a, data, point(device), APP_ID, previous_counter=5)
    assert e.value.code == "replayed_counter"


def test_assertion_wrong_rp_id(device):
    data = b'{"challenge":"abc"}'
    a = synthetic.make_assertion(device, data, "OTHER.app", counter=1)
    with pytest.raises(VerificationError) as e:
        verify_assertion(a, data, point(device), APP_ID, 0)
    assert e.value.code == "rp_id_mismatch"
