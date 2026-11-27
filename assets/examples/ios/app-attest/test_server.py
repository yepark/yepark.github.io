"""End-to-end server tests with SYNTHETIC attestation and assertions."""

import base64
import json

import pytest
from fastapi.testclient import TestClient

import synthetic
from server import Config, create_app

APP_ID = "ABCDE12345.com.example.checkin"


@pytest.fixture
def env(tmp_path):
    ca = synthetic.FakeCA()
    root = tmp_path / "root.pem"
    root.write_bytes(ca.root_pem())
    cfg = Config(app_id=APP_ID, environment="development",
                 root_ca_path=str(root), db_path=str(tmp_path / "t.db"),
                 allowed_categories={2, 3, 4}, challenges_per_minute=10)
    return ca, TestClient(create_app(cfg)), cfg


def challenge(client, purpose):
    r = client.post("/challenge", json={"purpose": purpose})
    assert r.status_code == 200
    return r.json()["challenge"]


def register(ca, client, category=3):
    ch = challenge(client, "attest")
    cdh = synthetic.sha256(base64.b64decode(ch))
    device, key_id, att = synthetic.make_attestation(
        ca, APP_ID, cdh, category=category)
    r = client.post("/attest", json={
        "key_id": synthetic.b64(key_id),
        "attestation": synthetic.b64(att), "challenge": ch})
    return device, synthetic.b64(key_id), r, ch, att


def check_in(client, device, key_id, counter, ch=None, body=None):
    ch = ch or challenge(client, "assert")
    data = body or json.dumps({"challenge": ch, "userID": "u1"}).encode()
    a = synthetic.make_assertion(device, data, APP_ID, counter)
    return client.post("/api/check-in", content=data, headers={
        "X-App-Attest-Key-Id": key_id,
        "X-App-Attest-Assertion": synthetic.b64(a),
        "Content-Type": "application/json"})


def test_full_flow(env):
    ca, client, _ = env
    device, key_id, r, *_ = register(ca, client)
    assert r.status_code == 201
    assert check_in(client, device, key_id, 1).status_code == 200
    assert check_in(client, device, key_id, 2).status_code == 200


def test_attest_challenge_single_use(env):
    ca, client, _ = env
    _, _, r, ch, att = register(ca, client)
    assert r.status_code == 201
    r2 = client.post("/attest", json={
        "key_id": "AAAA", "attestation": synthetic.b64(att),
        "challenge": ch})
    assert r2.json()["error"] == "bad_challenge"


def test_attest_unknown_challenge(env):
    ca, client, _ = env
    r = client.post("/attest", json={
        "key_id": "AAAA", "attestation": "AAAA",
        "challenge": base64.b64encode(b"x" * 32).decode()})
    assert (r.status_code, r.json()["error"]) == (401, "bad_challenge")


def test_attest_category_not_allowed(env):
    ca, client, _ = env
    _, _, r, *_ = register(ca, client, category=10)
    assert (r.status_code, r.json()["error"]) == (401, "bad_category")


def test_assert_challenge_reuse(env):
    ca, client, _ = env
    device, key_id, *_ = register(ca, client)
    ch = challenge(client, "assert")
    assert check_in(client, device, key_id, 1, ch=ch).status_code == 200
    r = check_in(client, device, key_id, 2, ch=ch)
    assert r.json()["error"] == "bad_challenge"


def test_assert_replayed_request(env):
    ca, client, _ = env
    device, key_id, *_ = register(ca, client)
    ch = challenge(client, "assert")
    data = json.dumps({"challenge": ch, "userID": "u1"}).encode()
    a = synthetic.make_assertion(device, data, APP_ID, 1)
    headers = {"X-App-Attest-Key-Id": key_id,
               "X-App-Attest-Assertion": synthetic.b64(a)}
    first = client.post("/api/check-in", content=data, headers=headers)
    again = client.post("/api/check-in", content=data, headers=headers)
    assert first.status_code == 200
    assert again.json()["error"] == "replayed_counter"


def test_assert_attest_challenge_not_accepted(env):
    ca, client, _ = env
    device, key_id, *_ = register(ca, client)
    ch = challenge(client, "attest")
    r = check_in(client, device, key_id, 1, ch=ch)
    assert r.json()["error"] == "bad_challenge"


def test_failed_assert_keeps_challenge_and_counter(env):
    ca, client, _ = env
    device, key_id, *_ = register(ca, client)
    ch = challenge(client, "assert")
    other = synthetic.make_attestation(ca, APP_ID, b"x" * 32)[0]
    bad = check_in(client, other, key_id, 1, ch=ch)
    assert bad.json()["error"] == "bad_signature"
    assert check_in(client, device, key_id, 1, ch=ch).status_code == 200


def test_unknown_key(env):
    ca, client, _ = env
    device, *_ = register(ca, client)
    r = check_in(client, device, "bm9wZQ==", 1)
    assert (r.status_code, r.json()["error"]) == (401, "unknown_key")


def test_rate_limit(env):
    _, client, _ = env
    codes = [client.post("/challenge", json={"purpose": "assert"})
             .status_code for _ in range(11)]
    assert codes[-1] == 429 and codes[:10] == [200] * 10


def test_expired_challenge(tmp_path):
    ca = synthetic.FakeCA()
    root = tmp_path / "root.pem"
    root.write_bytes(ca.root_pem())
    cfg = Config(app_id=APP_ID, environment="development",
                 root_ca_path=str(root), db_path=str(tmp_path / "e.db"),
                 challenge_ttl=-1)  # already expired when issued
    client = TestClient(create_app(cfg))
    _, _, r, *_ = register(ca, client)
    assert r.json()["error"] == "bad_challenge"
