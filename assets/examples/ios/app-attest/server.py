"""Small App Attest server: challenges, /attest, and one protected API.

Run:
  APP_ID=TEAMID.com.example.app APPATTEST_ENV=development \
  uvicorn server:app --port 8000
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import os
import secrets
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field

from cryptography import x509
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from appattest_verify import (
    VerificationError,
    sha256,
    verify_assertion,
    verify_attestation,
)

log = logging.getLogger("appattest")

SCHEMA = """
CREATE TABLE IF NOT EXISTS challenges (
  value      TEXT PRIMARY KEY,   -- base64 of the random bytes
  purpose    TEXT NOT NULL,      -- 'attest' or 'assert'
  expires_at REAL NOT NULL,
  used       INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS app_keys (
  key_id      TEXT PRIMARY KEY,  -- base64, as the app sends it
  public_key  BLOB NOT NULL UNIQUE,
  counter     INTEGER NOT NULL,
  receipt     BLOB NOT NULL,
  environment TEXT NOT NULL,
  category    INTEGER,
  bundle_ver  TEXT,
  created_at  REAL NOT NULL
);
"""


@dataclass
class Config:
    app_id: str
    environment: str  # 'development' or 'production'
    root_ca_path: str
    db_path: str = "appattest.sqlite3"
    challenge_ttl: float = 300.0
    # None means "do not enforce". See the post for why.
    allowed_categories: set[int] | None = None
    challenges_per_minute: int = 30

    @classmethod
    def from_env(cls) -> "Config":
        cats = os.environ.get("ALLOWED_CATEGORIES")
        return cls(
            app_id=os.environ["APP_ID"],
            environment=os.environ.get("APPATTEST_ENV", "development"),
            root_ca_path=os.environ.get(
                "ROOT_CA_PATH", "Apple_App_Attestation_Root_CA.pem"
            ),
            db_path=os.environ.get("DB_PATH", "appattest.sqlite3"),
            allowed_categories=(
                {int(c) for c in cats.split(",")} if cats else None
            ),
        )


class ApiError(Exception):
    def __init__(self, status: int, code: str, detail: str = ""):
        self.status, self.code, self.detail = status, code, detail


def b64decode(value: str, name: str) -> bytes:
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise ApiError(400, "bad_base64", name)


@dataclass
class RateLimiter:
    """Fixed one-minute window per client. In memory, one process only."""

    limit: int
    hits: dict = field(default_factory=lambda: defaultdict(list))

    def check(self, client: str) -> None:
        now = time.monotonic()
        recent = [t for t in self.hits[client] if now - t < 60]
        if len(recent) >= self.limit:
            raise ApiError(429, "rate_limited")
        recent.append(now)
        self.hits[client] = recent


class ChallengeRequest(BaseModel):
    purpose: str  # 'attest' or 'assert'


class AttestRequest(BaseModel):
    key_id: str
    attestation: str
    challenge: str


def create_app(config: Config) -> FastAPI:
    with open(config.root_ca_path, "rb") as f:
        root = x509.load_pem_x509_certificate(f.read())
    db = sqlite3.connect(
        config.db_path, isolation_level=None, check_same_thread=False
    )
    db.executescript(SCHEMA)
    limiter = RateLimiter(config.challenges_per_minute)
    app = FastAPI()

    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError):
        log.warning("%s %s -> %s", request.url.path, exc.code, exc.detail)
        return JSONResponse(
            {"error": exc.code, "detail": exc.detail}, status_code=exc.status
        )

    def consume_challenge(value: str, purpose: str) -> None:
        """Mark a challenge used. Works once, and only before expiry."""
        cur = db.execute(
            "UPDATE challenges SET used = 1 WHERE value = ? AND purpose = ?"
            " AND used = 0 AND expires_at > ?",
            (value, purpose, time.time()),
        )
        if cur.rowcount != 1:
            raise ApiError(401, "bad_challenge", "unknown, used or expired")

    def check_category(category: int | None, required: bool) -> None:
        allowed = config.allowed_categories
        if allowed is None or (category is None and not required):
            return
        if category not in allowed:
            raise ApiError(401, "bad_category", f"category {category}")

    @app.post("/challenge")
    def new_challenge(body: ChallengeRequest, request: Request):
        if body.purpose not in ("attest", "assert"):
            raise ApiError(400, "bad_purpose")
        limiter.check(request.client.host if request.client else "?")
        value = base64.b64encode(secrets.token_bytes(32)).decode()
        db.execute(
            "INSERT INTO challenges (value, purpose, expires_at)"
            " VALUES (?, ?, ?)",
            (value, body.purpose, time.time() + config.challenge_ttl),
        )
        return {"challenge": value, "expires_in": int(config.challenge_ttl)}

    @app.post("/attest", status_code=201)
    def attest(body: AttestRequest):
        key_id = b64decode(body.key_id, "key_id")
        attestation = b64decode(body.attestation, "attestation")
        challenge = b64decode(body.challenge, "challenge")
        consume_challenge(body.challenge, "attest")
        try:
            key = verify_attestation(
                attestation,
                key_id=key_id,
                client_data_hash=sha256(challenge),
                app_id=config.app_id,
                environment=config.environment,
                root=root,
            )
        except VerificationError as e:
            raise ApiError(401, e.code, str(e))
        check_category(key.validation_category, required=True)
        try:
            db.execute(
                "INSERT INTO app_keys (key_id, public_key, counter, receipt,"
                " environment, category, bundle_ver, created_at)"
                " VALUES (?, ?, 0, ?, ?, ?, ?, ?)",
                (
                    body.key_id,
                    key.public_key,
                    key.receipt,
                    config.environment,
                    key.validation_category,
                    key.bundle_version,
                    time.time(),
                ),
            )
        except sqlite3.IntegrityError:
            raise ApiError(409, "key_already_registered")
        log.info("attested key %s...", body.key_id[:8])
        return {"status": "registered"}

    @app.post("/api/check-in")
    async def check_in(
        request: Request,
        x_app_attest_key_id: str = Header(),
        x_app_attest_assertion: str = Header(),
    ):
        client_data = await request.body()  # the exact signed bytes
        assertion = b64decode(x_app_attest_assertion, "assertion")
        row = db.execute(
            "SELECT public_key, counter FROM app_keys WHERE key_id = ?",
            (x_app_attest_key_id,),
        ).fetchone()
        if row is None:
            raise ApiError(401, "unknown_key")
        public_key, stored_counter = row
        try:
            result = verify_assertion(
                assertion,
                client_data=client_data,
                public_key=public_key,
                app_id=config.app_id,
                previous_counter=stored_counter,
            )
        except VerificationError as e:
            raise ApiError(401, e.code, str(e))
        # Assertions may carry no extensions; check only when present.
        check_category(result.validation_category, required=False)
        try:
            payload = json.loads(client_data)
            challenge = payload["challenge"]
        except (ValueError, KeyError, TypeError):
            raise ApiError(400, "bad_client_data")

        # Step 6 (challenge) and storing the counter happen together.
        db.execute("BEGIN IMMEDIATE")
        try:
            consume_challenge(challenge, "assert")
            cur = db.execute(
                "UPDATE app_keys SET counter = ?"
                " WHERE key_id = ? AND counter < ?",
                (result.counter, x_app_attest_key_id, result.counter),
            )
            if cur.rowcount != 1:
                raise ApiError(401, "replayed_counter")
            db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK")
            raise

        # Only now is the request trusted. Real work goes here.
        return {"status": "checked-in", "user": payload.get("userID")}

    return app


if os.environ.get("APP_ID"):
    logging.basicConfig(level=logging.INFO)
    app = create_app(Config.from_env())
