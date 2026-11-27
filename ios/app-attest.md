---
title: "App Attest와 attestKey"
description: "DeviceCheck의 App Attest로 키를 만들고 attestKey로 증명받은 뒤, Python 서버에서 challenge 발급, attestation 검증, assertion 검증과 재전송 방지를 직접 구현하고 Apple 예제 데이터로 확인합니다."
parent: iOS
nav_order: 23
permalink: /ios/app-attest/
date: 2026-11-26
last_modified_at: 2026-11-28
seo:
  type: BlogPosting
last_modified_date: 2026-11-28
tags: [iOS, Security, DeviceCheck, App-Attest]
---

# App Attest와 attestKey
{: .no_toc }

{% include article-toc.md %}

출석 체크를 하면 포인트를 주는 앱이 있다고 생각해 보자. 서버 API는 `POST /rewards/check-in` 하나다. 앱의 네트워크 요청을 복사하면 스크립트로 이 API를 수천 번 호출할 수 있다. 로그인 토큰만으로는 요청을 보낸 쪽이 우리가 배포한 앱인지, 앱을 흉내 내는 프로그램인지 구분하기 어렵다.

**App Attest**는 이 질문에 답하기 위한 기능이다. 앱은 기기의 Secure Enclave(개인 키를 꺼낼 수 없게 보관하는 칩 안의 별도 보안 영역)에 키를 만들고, Apple에 이 키가 정상 기기의 정상 앱에서 만들어졌다는 증명(attestation)을 받는다. 서버는 이 증명을 검증해 공개 키를 저장하고, 이후 중요한 요청마다 그 키로 서명한 assertion을 확인한다.

이 글은 DeviceCheck 프레임워크의 `DCAppAttestService`를 기준으로 한다. iOS 14부터 사용할 수 있다. 앞부분은 앱(Swift) 쪽, 뒷부분은 서버(Python) 쪽이다. 서버 코드는 글 끝의 [실습 소스](#실습-소스)에 전부 올려 두었다.

## 세 단계로 나뉘는 흐름

App Attest는 한 번의 API 호출로 끝나지 않는다. 앱과 서버가 각자 해야 할 일이 있다.

| 단계 | 앱에서 호출하는 API | 서버가 하는 일 |
| --- | --- | --- |
| 0. challenge 받기 | (서버 API 호출) | 일회용 임의 값 발급 |
| 1. 키 생성 | `generateKey()` | 없음 |
| 2. 키 증명 | `attestKey(_:clientDataHash:)` | attestation 검증, 공개 키와 카운터 저장 |
| 3. 요청 서명 | `generateAssertion(_:clientDataHash:)` | assertion 서명과 카운터 검증 |

1·2단계는 키 하나에 한 번 한다. 3단계는 포인트 지급이나 결제처럼 보호하려는 요청마다 한다. `attestKey`는 Apple 서버와 통신하므로 요청마다 호출하면 안 된다.

## 준비: 지원 여부와 entitlement

먼저 `isSupported`를 확인한다. 시뮬레이터나 지원하지 않는 환경에서는 `false`가 나온다.

```swift
import DeviceCheck

let service = DCAppAttestService.shared
guard service.isSupported else {
    // App Attest 없이 처리할 경로로 보낸다
    return
}
```

앱 타깃의 Signing & Capabilities에서 **App Attest**를 추가하면 entitlements 파일에 다음 키가 생긴다.

```xml
<key>com.apple.developer.devicecheck.appattest-environment</key>
<string>development</string>
```

`development`로 받은 증명은 개발 환경용이다. Apple 문서에 따르면 TestFlight, App Store, Enterprise로 배포한 앱은 이 값과 상관없이 항상 운영(production) 환경으로 동작한다. 서버는 환경에 따라 검증 기준(아래의 `aaguid`)이 달라지므로, 어느 환경의 증명을 받을지 정해 둔다.

## 1단계: generateKey로 키 만들기

```swift
let keyID = try await service.generateKey()
```

`generateKey()`는 Secure Enclave에 P-256 키 쌍을 만들고, 그 키를 가리키는 식별자(`keyID`, Base64 문자열)를 돌려준다. 개인 키는 기기 밖으로 나오지 않는다. 앱이 저장해야 하는 것은 `keyID`뿐이다.

이 키는 앱 설치에 묶인다. 앱을 지웠다가 다시 설치하거나, 백업을 다른 기기로 복원하면 사용할 수 없다. 그래서 `keyID`를 저장했더라도 이후 호출에서 `DCError.invalidKey`가 나오면 새 키를 만드는 경로가 필요하다.

{: .tip }
`keyID`는 사실 **공개 키의 SHA-256 해시**다. 서버는 이 성질을 이용해 "앱이 보낸 keyID"와 "인증서 안의 공개 키"가 같은 키를 가리키는지 확인한다. 아래 서버 5단계에서 직접 계산해 본다.

## 2단계: attestKey로 키 증명받기

`attestKey`가 이 글의 핵심이다. 앱은 키와 함께 **서버가 준 일회용 challenge의 해시**를 넘긴다.

```swift
import CryptoKit

// 서버가 준 Base64 문자열을 바이트로 되돌린다
let challengeB64 = try await api.fetchChallenge("attest")
let challenge = Data(base64Encoded: challengeB64)!
let clientDataHash = Data(SHA256.hash(data: challenge))

let attestation = try await service.attestKey(
    keyID, clientDataHash: clientDataHash)
try await api.registerAttestation(
    keyID: keyID, attestation: attestation,
    challenge: challengeB64)
```

`attestKey`를 호출하면 시스템이 Apple 서버에 이 키의 증명을 요청한다. 결과인 `attestation`은 CBOR(JSON과 비슷한 구조를 더 작은 바이너리로 표현하는 형식)로 인코딩된 객체다.

```
{
  fmt: "apple-appattest",
  attStmt: { x5c: [credCert, intermediateCert], receipt: <bytes> },
  authData: <bytes>
}
```

- `x5c`: Apple App Attestation Root CA로 이어지는 인증서 체인. 첫 번째 인증서(credCert)에 앱이 만든 공개 키가 들어 있다.
- `authData`: 앱 ID 해시, 카운터, 키 식별자 등이 정해진 바이트 배치로 들어 있다.
- `receipt`: 나중에 Apple에 위험 지표를 조회할 때 쓰는 영수증.

challenge를 서버가 만들어야 하는 이유는 재전송 방지다. 앱이 직접 만든 값을 쓰면 공격자가 예전에 성공한 attestation을 그대로 다시 보낼 수 있다. 서버는 challenge를 발급하고, 한 번 사용되거나 일정 시간이 지나면 버린다. Apple은 challenge를 16바이트 이상으로 만들라고 안내한다. 이 글의 서버는 32바이트를 쓴다.

### 키 생성과 증명을 하나로 묶기

실제 앱에서는 1·2단계를 함께 처리하고, **서버 등록이 성공한 뒤에만** `keyID`를 저장한다. 중간에 실패한 키를 저장해 두면 이후 assertion이 모두 서버에서 거절된다.

```swift
import CryptoKit
import DeviceCheck

enum AppAttestError: Error {
    case unsupported
}

final class AppAttestClient {
    private let service = DCAppAttestService.shared
    private let store: KeyIDStore  // Keychain 등에 저장
    private let api: AttestAPI

    init(store: KeyIDStore, api: AttestAPI) {
        self.store = store
        self.api = api
    }

    func attestedKeyID() async throws -> String {
        guard service.isSupported else {
            throw AppAttestError.unsupported
        }
        if let saved = store.load() { return saved }

        let keyID = try await service.generateKey()
        let b64 = try await api.fetchChallenge("attest")
        let challenge = Data(base64Encoded: b64)!
        let hash = Data(SHA256.hash(data: challenge))
        let attestation = try await service.attestKey(
            keyID, clientDataHash: hash)

        try await api.registerAttestation(
            keyID: keyID, attestation: attestation,
            challenge: b64)
        store.save(keyID)
        return keyID
    }

    func resetKey() {
        store.delete()
    }
}
```

Apple 문서는 `attestKey`가 `serverUnavailable`을 던지면 **같은 키로** 나중에 다시 시도하고, 그 밖의 오류면 `keyID`를 버리고 새 키를 만들라고 안내한다. 위 코드는 단순하게 실패한 키를 저장하지 않고 다음 시도에서 새로 만든다. 키를 자주 새로 만들면 아래에서 설명할 위험 지표(기기당 키 개수)가 커지므로, `serverUnavailable`만은 같은 키로 재시도하도록 바꾸는 편이 Apple 안내에 더 가깝다.

## 서버 만들기: 무엇이 필요한가

여기부터 서버 쪽이다. 서버는 세 개의 API와 두 개의 표(테이블)를 가진다.

| API | 하는 일 |
| --- | --- |
| `POST /challenge` | 일회용 challenge 발급. `purpose`는 `attest` 또는 `assert` |
| `POST /attest` | attestation 검증 후 공개 키·카운터·receipt 저장 |
| `POST /api/check-in` | assertion을 검증한 요청만 처리하는 보호 API |

Python의 **FastAPI**를 골랐다. 요청 JSON의 필드 검사를 대신 해 주고, 서버를 띄우지 않고도 API를 호출해 보는 테스트 도구(`TestClient`)가 있어서 검증 실패 경우를 테스트로 묶기 쉽다. 암호 처리는 `cryptography`, CBOR 해석은 `cbor2`를 쓴다. 저장소는 파일 하나로 동작하는 SQLite다.

실행한 버전은 Python 3.12.16, cryptography 50.0.2, cbor2 6.3.0, FastAPI 0.165.0, uvicorn 0.54.0이다.

```text
appattest/
├── appattest_verify.py   검증 로직 (웹과 무관)
├── server.py             FastAPI 서버 + SQLite
├── synthetic.py          테스트용 가짜 데이터 생성
├── test_verify.py        검증 로직 테스트
├── test_server.py        API 테스트
├── walkthrough.py        Apple 예제로 단계별 출력
├── demo_client.py        curl 실습용 가짜 클라이언트
├── fetch_apple_files.py  Apple 루트 CA·예제 내려받기
└── requirements.txt
```

검증 로직(`appattest_verify.py`)을 웹 서버와 떼어 둔 이유는 테스트 때문이다. 검증 함수는 바이트를 받아 결과를 돌려주기만 하므로, 서버 없이 Apple 예제 데이터를 바로 넣어 볼 수 있다.

### 저장할 것: challenge와 키

```sql
CREATE TABLE challenges (
  value      TEXT PRIMARY KEY, -- Base64
  purpose    TEXT NOT NULL,    -- attest | assert
  expires_at REAL NOT NULL,
  used       INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE app_keys (
  key_id      TEXT PRIMARY KEY,
  public_key  BLOB NOT NULL UNIQUE,
  counter     INTEGER NOT NULL,
  receipt     BLOB NOT NULL,
  environment TEXT NOT NULL,
  category    INTEGER,
  bundle_ver  TEXT,
  created_at  REAL NOT NULL
);
```

`public_key`에 `UNIQUE`를 붙인 데는 이유가 있다. Apple 문서는 재전송 공격에 대한 추가 방어로 "이 공개 키가 이미 다른 사용자와 연결돼 있지 않은지 확인하라"고 한다. 같은 키를 두 번 등록하려 하면 DB가 거절하고, 서버는 `409`를 돌려준다.

`environment`를 따로 저장하는 것도 Apple 안내 때문이다. 개발 환경 키·receipt와 운영 환경 키·receipt는 서로의 환경에서 쓸 수 없으므로 섞이지 않게 나눠 둔다.

## 서버: challenge 발급하기

challenge는 **일회용 번호표**라고 생각하면 된다. 은행 창구에서 번호표를 뽑으면 한 번 부르고 끝이고, 시간이 지나면 무효가 된다. 서버도 임의 값을 만들어 저장하고, 한 번 쓰이면 `used = 1`로 바꾼다.

```python
@app.post("/challenge")
def new_challenge(body: ChallengeRequest,
                  request: Request):
    if body.purpose not in ("attest", "assert"):
        raise ApiError(400, "bad_purpose")
    limiter.check(request.client.host)
    value = base64.b64encode(
        secrets.token_bytes(32)).decode()
    db.execute(
        "INSERT INTO challenges"
        " (value, purpose, expires_at)"
        " VALUES (?, ?, ?)",
        (value, body.purpose,
         time.time() + config.challenge_ttl))
    return {"challenge": value,
            "expires_in": int(config.challenge_ttl)}
```

`secrets.token_bytes`는 암호용 난수 생성기를 쓰는 Python 표준 함수다. `random` 모듈은 예측할 수 있으므로 쓰지 않는다.

쓸 때는 **확인과 사용 표시를 SQL 한 문장으로** 한다.

```python
def consume_challenge(value, purpose):
    cur = db.execute(
        "UPDATE challenges SET used = 1"
        " WHERE value = ? AND purpose = ?"
        " AND used = 0 AND expires_at > ?",
        (value, purpose, time.time()))
    if cur.rowcount != 1:
        raise ApiError(401, "bad_challenge",
                       "unknown, used or expired")
```

"먼저 SELECT로 확인하고 다음에 UPDATE"로 나누면, 같은 challenge로 동시에 두 요청이 들어왔을 때 둘 다 SELECT를 통과할 수 있다. 한 문장으로 쓰면 둘 중 하나만 `rowcount`가 1이 된다.

{: .note }
`purpose`를 나눈 이유: attestation용으로 받은 challenge를 assertion에 쓰지 못하게 하려는 것이다. 테스트 `test_assert_attest_challenge_not_accepted`가 이 경우를 확인한다.

## 서버: attestation 검증하기

먼저 진짜 attestation이 어떻게 생겼는지 보자. iPhone 없이 진짜 데이터를 볼 방법이 있다. Apple의 [Attestation Object Validation Guide](https://developer.apple.com/documentation/devicecheck/attestation-object-validation-guide)에 예제 앱(`팀 ID 1234567890`, 번들 ID `com.example.myapp`, challenge `example_server_challenge`)으로 만든 attestation 객체가 Base64로 실려 있다. `fetch_apple_files.py`가 이 예제와 Apple 루트 인증서를 내려받는다.

```bash
python fetch_apple_files.py
```

```text
saved Apple_App_Attestation_Root_CA.pem and apple_sample_attestation.b64 (7876 chars)
```

루트 인증서를 openssl로 열어 보면 이렇다.

```bash
openssl x509 -in Apple_App_Attestation_Root_CA.pem \
  -noout -subject -dates -fingerprint -sha256
```

```text
subject=CN=Apple App Attestation Root CA, O=Apple Inc., ST=California
notBefore=Mar 18 18:32:53 2020 GMT
notAfter=Mar 15 00:00:00 2045 GMT
sha256 Fingerprint=1C:B9:82:3B:A2:8B:A6:AD:2D:33:A0:06:94:1D:E2:AE:4F:51:3E:F1:D4:E8:31:B9:F7:E0:FA:7B:62:42:C9:32
```

공개 키는 P-384, 서명 알고리즘은 `ecdsa-with-SHA384`였다. 서버는 이 파일 하나를 **신뢰의 출발점(trust anchor)**으로 갖고 있다. 회사 출입증을 확인할 때 "인사팀 도장"을 기준으로 삼는 것과 같다. 앱이 보낸 인증서가 이 도장까지 이어지지 않으면 받아 주지 않는다.

`walkthrough.py`는 Apple 예제를 단계마다 출력한다. 실제로 실행한 결과를 아래 각 단계에 나눠 붙인다. 첫 줄은 객체 전체 모양이다.

```text
fmt: apple-appattest | x5c: 2 | receipt: 3977 bytes | authData: 226 bytes
```

### authData의 바이트 배치

`authData`는 WebAuthn(웹 브라우저의 지문·보안 키 로그인 표준)의 authenticator data 형식을 따른다. 정해진 위치에 정해진 길이로 값이 들어 있어서, 위치만 알면 잘라 읽으면 된다.

| 오프셋 | 길이 | 내용 |
| --- | --- | --- |
| 0 | 32 | RP ID 해시 |
| 32 | 1 | 플래그 |
| 33 | 4 | 카운터 (big-endian) |
| 37 | 16 | aaguid |
| 53 | 2 | credential ID 길이 |
| 55 | 32 | credential ID |
| 87 | 77 | COSE 형식 공개 키 |
| 164 | 가변 | extensions (CBOR 맵) |

```python
def parse_auth_data(data: bytes) -> AuthData:
    ad = AuthData(
        rp_id_hash=data[0:32],
        flags=data[32],
        counter=int.from_bytes(data[33:37], "big"),
    )
    pos = 37
    if ad.flags & 0x40:  # credential data 있음
        ad.aaguid = data[37:53]
        n = int.from_bytes(data[53:55], "big")
        ad.credential_id = data[55:55 + n]
        pos = 55 + n
        stream = io.BytesIO(data[pos:])
        ad.cose_key = cbor2.CBORDecoder(
            stream).decode()
        pos += stream.tell()
    if pos < len(data):
        ad.extensions = cbor2.loads(data[pos:])
    return ad
```

COSE 공개 키는 길이가 바이트 앞에 적혀 있지 않다. 그래서 CBOR 디코더로 한 객체만 읽게 하고, 디코더가 몇 바이트를 읽었는지(`stream.tell()`)로 다음 위치를 구한다. Apple 예제에서 COSE 키는 정확히 77바이트였다.

{: .warning }
WebAuthn 규칙으로는 extensions가 있으면 플래그에 `0x80`(ED)이 켜져야 한다. 그런데 Apple 예제의 플래그는 `0x40`뿐이고 extensions 맵은 붙어 있었다. 그래서 이 코드는 플래그를 보지 않고 "남은 바이트가 있으면 extensions"로 읽는다.

### Apple의 검증 목록

Apple 문서 [Validating apps that connect to your server](https://developer.apple.com/documentation/devicecheck/validating-apps-that-connect-to-your-server)가 정한 iOS 앱용 순서는 다음과 같다. 하나라도 실패하면 등록을 거절한다.

1. `x5c` 인증서 체인을 Apple App Attestation Root CA로 검증한다.
2. `clientDataHash = SHA256(challenge)`를 만들어 `authData` 끝에 붙인다.
3. 붙인 값의 SHA256을 `nonce`로 한다.
4. credCert의 확장 `1.2.840.113635.100.8.2`에서 octet string을 꺼내 `nonce`와 비교한다.
5. credCert 공개 키를 **X9.62 비압축 점 형식**으로 꺼내 SHA256한 값이 keyID와 같은지 본다.
6. `SHA256(App ID)`가 `authData`의 RP ID 해시와 같은지 본다.
7. `counter`가 0인지 본다.
8. `aaguid`가 개발 환경이면 `appattestdevelop`, 운영 환경이면 `appattest` 뒤에 `0x00` 7바이트인지 본다.
9. `credentialId`가 keyID와 같은지 본다.
10. extensions의 `apple_validation_category_01`을 확인한다.
11. extensions의 `apple_bundle_version_01`을 확인한다.

(macOS 앱은 4단계 뒤에 `aclBlob` 확인이 하나 더 있다. 이 글은 iOS만 다룬다.)

검증 함수의 모양은 이렇다. 서버 시간 `now`를 인자로 받게 한 것은, 유효 기간이 지난 Apple 예제를 "그때 시각"으로 검증하기 위해서다.

```python
def verify_attestation(
    attestation: bytes,     # CBOR 원본
    key_id: bytes,          # keyID를 Base64 디코딩
    client_data_hash: bytes,
    app_id: str,            # "팀ID.번들ID"
    environment: str,       # development|production
    root: x509.Certificate,
    now: dt.datetime | None = None,
) -> AttestedKey:
```

먼저 CBOR을 풀고 `fmt`가 `apple-appattest`인지 본다. Apple 문서는 "기대한 구조의 CBOR인지 확인하라"고 한다.

```python
obj = cbor2.loads(attestation)
fmt = obj["fmt"]
x5c = obj["attStmt"]["x5c"]
receipt = obj["attStmt"]["receipt"]
auth_data = obj["authData"]
if fmt != "apple-appattest":
    raise VerificationError("bad_format", fmt)
```

### 1단계: 인증서 체인

```python
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
verifier.verify(certs[0], certs[1:])
```

`cryptography`의 경로 검증기(`PolicyBuilder`)에 "믿는 루트는 Apple 루트 하나뿐"이라고 알려 주고, 리프(credCert)와 중간 인증서를 넘긴다. 서명이 이어지는지, 각 인증서가 `now` 시각에 유효한지를 검사한다.

`ee_policy=permit_all()`은 리프 인증서의 확장 검사를 풀어 준 것이다. 기본 정책은 웹 서버 인증서를 기준으로 하는데, credCert는 웹 서버 인증서가 아니라서(Apple 전용 확장과 용도를 쓴다) 기본 정책으로는 맞지 않는다. 중간 CA에는 기본 CA 정책을 그대로 둔다.

실행 결과:

```text
1. chain OK at 2026-04-21 | leaf valid 2026-04-20 18:13:12+00:00 ~ 2026-04-23 18:13:12+00:00
   same chain on 2026-11-28: bad_chain
```

Apple 예제의 credCert는 **사흘짜리** 인증서다. 2026-04-23에 만료됐으므로, 오늘 날짜로 검증하면 실패하고 예제가 만들어진 2026-04-21 기준으로는 통과한다. 실제 서버에서는 `now`를 넘기지 않아 현재 시각으로 검증한다. 중간 인증서는 `Apple App Attestation CA 1`(2020-03-18 ~ 2030-03-13)이었다.

### 2~4단계: nonce 비교

nonce는 **봉인 스티커**에 비유할 수 있다. Apple이 인증서를 만들 때 "이 authData와 이 challenge 해시를 합친 값"의 해시를 인증서 안에 새겨 둔다. 서버가 같은 계산을 해서 같은 값이 나오면, 이 인증서가 이번 challenge를 위해 만들어졌다는 뜻이다.

```python
nonce = sha256(auth_data + client_data_hash)
if nonce_from_cred_cert(cred_cert) != nonce:
    raise VerificationError("nonce_mismatch", "")
```

확장 값은 DER(인증서에 쓰는 바이너리 인코딩)로 `SEQUENCE { [1] { OCTET STRING } }` 모양이다. Apple 예제에서 꺼낸 바이트는 다음과 같았다.

```text
30 24  a1 22  04 20  87b7d06d...0bff6e
```

`30`(SEQUENCE) 안에 `a1`(태그 [1]) 안에 `04`(OCTET STRING, 길이 `0x20` = 32)가 들어 있다. 이 구조를 따라 32바이트를 꺼내는 함수다.

```python
def nonce_from_cred_cert(cert):
    ext = cert.extensions.get_extension_for_oid(
        NONCE_OID)  # 1.2.840.113635.100.8.2
    der = ext.value.value
    tag, seq, _ = _read_der(der, 0)      # 0x30
    tag, tagged, _ = _read_der(seq, 0)   # 0xA1
    tag, octets, _ = _read_der(tagged, 0)  # 0x04
    return octets
```

(실제 파일에는 각 태그가 기대값과 다르면 `bad_nonce_ext`로 거절하는 검사가 들어 있다.)

실행 결과:

```text
2-3. nonce: h7fQbZOkKU5G8BHma2zEAPC6sgcpl2xhlYC0KuYL/24=
4. credCert nonce: h7fQbZOkKU5G8BHma2zEAPC6sgcpl2xhlYC0KuYL/24=
```

{: .warning }
**Apple 예제는 challenge를 해시하지 않았다.** 이 nonce는 `clientDataHash` 자리에 challenge 원문 바이트 `example_server_challenge`를 그대로 넣었을 때만 나온다. 문서대로 `SHA256(challenge)`를 넣으면 `HRzniRKJ...`가 나와 일치하지 않는다(테스트에서 `nonce_mismatch`로 확인). 예제 receipt의 Client Hash 필드에도 원문이 들어 있다. 그래서 예제를 검증할 때만 `client_data_hash=b"example_server_challenge"`를 넘긴다. 실제 서버는 문서 순서대로 `SHA256(challenge)`를 쓰고, 앱도 위 Swift 코드처럼 해시를 넘긴다.

### 5단계: 공개 키와 keyID

```python
public_key = cred_cert.public_key().public_bytes(
    serialization.Encoding.X962,
    serialization.PublicFormat.UncompressedPoint,
)
if sha256(public_key) != key_id:
    raise VerificationError("key_id_mismatch", "")
```

"어떤 바이트를 해시하느냐"가 중요하다. Apple 문서는 **X9.62 비압축 점 형식**이라고 정해 두었다. P-256 공개 키를 `0x04 ‖ X좌표 32바이트 ‖ Y좌표 32바이트`, 모두 65바이트로 쓴 것이다. 인증서 안의 공개 키 정보 전체(SubjectPublicKeyInfo DER)를 해시하면 다른 값이 나온다. 직접 비교했다.

```text
5. SHA256(X9.62 point): zgSY9YSD+7TaDXssY6WlOPVS1K3Lmk+pFhlcSWE+ZV0= | keyId: zgSY9YSD+7TaDXssY6WlOPVS1K3Lmk+pFhlcSWE+ZV0=
```

같은 공개 키의 SubjectPublicKeyInfo DER를 해시하면 `T9/5kgtR...`가 나왔다. 앱이 보낸 keyID는 Base64 문자열이므로 서버는 먼저 Base64 디코딩한 32바이트와 비교한다. credCert의 CN(이름)도 이 32바이트의 16진수 `ce0498f5...`였다.

{: .warning }
Apple 가이드의 이 단계에는 "기대값"으로 `inGjK2Jb...`가 적혀 있다. 계산해 보니 이 값은 공개 키의 해시가 아니라 **keyID 바이트를 한 번 더 SHA256한 값**이었다. 문서 본문 규칙(공개 키 해시 = keyID)을 따르면 위처럼 정확히 일치한다. 같은 불일치를 Apple 개발자 포럼에 보고한 글도 있다(답변은 아직 없다).

### 6~9단계: authData 필드

```python
ad = parse_auth_data(auth_data)
if ad.rp_id_hash != sha256(app_id.encode()):
    raise VerificationError("rp_id_mismatch", "")
if ad.counter != 0:
    raise VerificationError("bad_counter", "")
if ad.aaguid != AAGUID[environment]:
    raise VerificationError("bad_aaguid", "")
if ad.credential_id != key_id:
    raise VerificationError("cred_id_mismatch", "")
```

```python
AAGUID = {
    "development": b"appattestdevelop",
    "production": b"appattest" + b"\x00" * 7,
}
```

- **RP ID 해시**: RP(Relying Party)는 "이 키를 믿고 쓰는 쪽", 즉 우리 앱이다. App ID는 `팀ID.번들ID` 형식이다. 다른 앱에서 만든 증명을 가져와도 이 해시가 달라서 걸러진다.
- **counter**: 키가 assertion을 몇 번 서명했는지 센다. 막 증명받은 키는 0이다.
- **aaguid**: 개발/운영 환경을 나타내는 16바이트 상수다.
- **credentialId**: 공개 키의 해시. keyID와 같아야 한다.

실행 결과:

```text
6. RP ID hash: 9EZtaPketsEGIMt+Y8coMkRoXuHWRntUFg51MXIFfwM=
   SHA256(App ID): 9EZtaPketsEGIMt+Y8coMkRoXuHWRntUFg51MXIFfwM=
7. counter: 0 | flags: 0x40
8. aaguid: b'appattest\x00\x00\x00\x00\x00\x00\x00'
9. credentialId: zgSY9YSD+7TaDXssY6WlOPVS1K3Lmk+pFhlcSWE+ZV0=
```

Apple 예제는 운영 환경 키였다. 같은 예제를 `environment="development"`로 검증하면 `bad_aaguid`로 거절되는 것을 테스트로 확인했다.

{: .warning }
Apple 문서끼리 개발 환경 값이 다르게 적혀 있다. 검증 목록에는 `appattestdevelop`, [Preparing to use the app attest service](https://developer.apple.com/documentation/devicecheck/preparing-to-use-the-app-attest-service)에는 `appattestsandbox`라고 되어 있다. 이 코드는 검증 목록을 따라 `appattestdevelop`만 받는다. 실기기 개발 빌드에서 `bad_aaguid`가 나오면 로그의 실제 aaguid 값을 먼저 확인한다.

### 10~11단계: 실행 분류와 번들 버전

extensions에는 앱이 어떻게 배포·서명됐는지(`apple_validation_category_01`)와 번들 버전(`apple_bundle_version_01`)이 들어 있다. Apple 문서가 밝힌 분류 값 중 주요한 것은 다음과 같다.

| 값 | 뜻 |
| --- | --- |
| 0 | 유효하지 않음 |
| 2 | TestFlight로 배포 |
| 3 | 개발용 코드 서명 |
| 4 | App Store로 배포 |
| 5 | Enterprise 또는 ad-hoc 배포 |

```text
10-11. extensions: {'apple_bundle_version_01': '1', 'apple_validation_category_01': b'\x01\x00\x00\x00'} -> category 1
```

분류 값은 4바이트 `01 00 00 00`로 들어 있었다. 이 코드는 이것을 little-endian(작은 자리부터 쓰는 순서) UInt32로 읽어 1로 바꾼다. Apple 가이드도 이 예제의 기대값을 1이라고 적었다. 가이드 문장은 번들 버전을 `"1.0"`이라고 했지만 실제 바이트는 `"1"`이었다.

Apple은 "확인하라"고만 하고 어떤 값을 허용할지는 정해 주지 않는다. 그래서 검증 함수는 값을 꺼내 돌려주기만 하고, 허용 여부는 서버 설정 `ALLOWED_CATEGORIES`로 정한다.

```python
def check_category(category, required):
    allowed = config.allowed_categories
    if allowed is None or (
            category is None and not required):
        return
    if category not in allowed:
        raise ApiError(401, "bad_category",
                       f"category {category}")
```

{: .tip }
실무에서는 운영 서버에 `ALLOWED_CATEGORIES=2,4`(TestFlight, App Store)처럼 실제로 배포하는 경로만 넣는 것을 권한다. 개발 서버에는 3(개발 서명)을 더한다. 처음에는 값을 기록만 하고 지켜본 뒤 막는 편이 안전하다. 어떤 OS 버전부터 이 확장이 붙는지는 Apple 문서에서 확인하지 못했기 때문이다.

마지막으로 전체 함수를 한 번에 실행한 결과다.

```text
verify_attestation: OK, public key 65 bytes
```

### /attest API

검증 함수를 서버 API로 감싼다. 순서가 중요하다.

```python
@app.post("/attest", status_code=201)
def attest(body: AttestRequest):
    key_id = b64decode(body.key_id, "key_id")
    att = b64decode(body.attestation, "attestation")
    challenge = b64decode(body.challenge, "challenge")
    consume_challenge(body.challenge, "attest")
    try:
        key = verify_attestation(
            att, key_id=key_id,
            client_data_hash=sha256(challenge),
            app_id=config.app_id,
            environment=config.environment,
            root=root)
    except VerificationError as e:
        raise ApiError(401, e.code, str(e))
    check_category(key.validation_category,
                   required=True)
    try:
        db.execute("INSERT INTO app_keys ...", (...))
    except sqlite3.IntegrityError:
        raise ApiError(409, "key_already_registered")
    return {"status": "registered"}
```

1. challenge를 **검증보다 먼저** 소비한다. 검증에 실패해도 그 challenge는 다시 쓸 수 없다. 공격자가 한 challenge로 여러 번 시험해 볼 수 없게 하려는 것이다.
2. `client_data_hash`는 서버가 직접 `SHA256(challenge)`로 계산한다. 앱이 보낸 해시를 믿지 않는다.
3. 통과하면 keyID, 65바이트 공개 키, counter 0, receipt를 저장한다.

오류는 모두 `{"error": 코드, "detail": 설명}` JSON으로 돌려준다. 앱은 `error` 값만 보고 분기하면 된다.

| HTTP | error | 원인 |
| --- | --- | --- |
| 400 | `bad_base64`, `bad_purpose`, `bad_client_data` | 요청 형식이 틀림 |
| 401 | `bad_challenge` | 없거나, 썼거나, 만료된 challenge |
| 401 | `bad_chain`, `nonce_mismatch`, `key_id_mismatch`, `rp_id_mismatch`, `bad_aaguid`, ... | attestation 검증 실패 |
| 401 | `unknown_key`, `bad_signature`, `replayed_counter` | assertion 검증 실패 |
| 409 | `key_already_registered` | 같은 키를 다시 등록 |
| 429 | `rate_limited` | challenge 요청이 너무 많음 |

## 3단계: generateAssertion으로 요청 서명하기

키가 등록되면 보호할 요청마다 assertion을 붙인다. 이번에도 서버가 준 challenge를 포함한 `clientData`를 만들고, 그 해시를 서명하게 한다.

```swift
struct CheckInRequest: Encodable {
    let challenge: String  // 서버가 준 Base64 그대로
    let userID: String
    let date: String
}

func sendCheckIn(userID: String) async throws {
    let keyID = try await attestClient.attestedKeyID()
    let challenge = try await api.fetchChallenge("assert")

    let body = CheckInRequest(
        challenge: challenge,
        userID: userID,
        date: ISO8601DateFormatter().string(from: .now)
    )
    let clientData = try JSONEncoder().encode(body)
    let clientDataHash = Data(SHA256.hash(data: clientData))

    let assertion = try await DCAppAttestService.shared
        .generateAssertion(keyID,
                           clientDataHash: clientDataHash)

    var req = URLRequest(url: baseURL
        .appending(path: "api/check-in"))
    req.httpMethod = "POST"
    req.setValue("application/json",
                 forHTTPHeaderField: "Content-Type")
    req.setValue(keyID,
                 forHTTPHeaderField: "X-App-Attest-Key-Id")
    req.setValue(
        assertion.base64EncodedString(),
        forHTTPHeaderField: "X-App-Attest-Assertion")
    req.httpBody = clientData  // 서명한 바이트 그대로
    let (_, res) = try await URLSession.shared
        .data(for: req)
    // res의 상태 코드와 error 값으로 분기한다
}
```

요청 본문(`clientData`)을 **그대로** 서버에 보낸다는 점이 중요하다. 서버는 받은 바이트로 해시를 다시 계산해야 하므로, 서명한 뒤 본문을 다시 인코딩하면 검증이 깨진다. 그래서 keyID와 assertion은 본문이 아니라 헤더에 실었다.

| 앱이 보내는 것 | 위치 | 형식 |
| --- | --- | --- |
| keyID | `X-App-Attest-Key-Id` 헤더 | `generateKey()`가 준 Base64 문자열 그대로 |
| assertion | `X-App-Attest-Assertion` 헤더 | `base64EncodedString()` |
| clientData | 본문 | 서명한 JSON 바이트 그대로 |
| challenge | 본문 JSON의 `challenge` | 서버가 준 Base64 문자열 그대로 |

`generateAssertion`은 Apple 서버와 통신하지 않고 기기에서 서명만 한다. 그래서 요청마다 호출해도 된다.

## 서버: assertion 검증하기

assertion은 `signature`와 `authenticatorData` 두 값을 담은 CBOR 객체다. `authenticatorData`는 attestation의 `authData`를 줄인 것으로, 앞의 RP ID 해시·플래그·카운터만 있다.

Apple 문서의 순서는 다음과 같다.

1. `clientDataHash = SHA256(clientData)`
2. `nonce = SHA256(authenticatorData ‖ clientDataHash)`
3. 저장한 공개 키로 `signature`가 `nonce`에 대해 유효한지 확인한다.
4. `SHA256(App ID)`가 RP ID 해시와 같은지 본다.
5. `counter`가 지난번 값보다 큰지(첫 assertion이면 0보다 큰지) 본다.
6. clientData 안의 challenge가 서버가 준 것과 같은지 본다.
7. extensions의 `validationCategory`를 확인한다.
8. extensions의 `bundleVersion`을 확인한다.

모두 통과하면 counter를 저장해 다음 5단계에 쓴다.

### 1~5단계: 서명과 카운터

```python
def verify_assertion(assertion, client_data,
                     public_key, app_id,
                     previous_counter):
    obj = cbor2.loads(assertion)
    signature = obj["signature"]
    auth_data = obj["authenticatorData"]

    client_data_hash = sha256(client_data)       # 1
    nonce = sha256(auth_data + client_data_hash)  # 2

    key = ec.EllipticCurvePublicKey \
        .from_encoded_point(ec.SECP256R1(), public_key)
    try:                                          # 3
        key.verify(signature, nonce,
                   ec.ECDSA(hashes.SHA256()))
    except InvalidSignature:
        raise VerificationError("bad_signature", "")

    ad = parse_auth_data(auth_data)
    if ad.rp_id_hash != sha256(app_id.encode()):  # 4
        raise VerificationError("rp_id_mismatch", "")
    if ad.counter <= previous_counter:            # 5
        raise VerificationError("replayed_counter", "")
    return VerifiedAssertion(counter=ad.counter, ...)
```

서명은 **도장**에 비유할 수 있다. 개인 키(도장)는 기기 안에만 있고, 서버는 등록 때 받아 둔 공개 키(인감 증명)로 "이 도장으로 찍은 게 맞는지"만 확인한다. 본문이 한 글자라도 바뀌면 `clientDataHash`가 달라지고, nonce가 달라져서 서명 확인이 실패한다.

`signature`는 DER로 인코딩된 ECDSA 서명이고, `cryptography`의 `verify`는 DER 서명을 그대로 받는다.

{: .warning }
3단계에서 "nonce에 대해 유효하다"를 어떻게 해석하느냐가 자주 틀리는 곳이다. 이 코드는 **nonce 32바이트를 메시지로 보고 ECDSA-SHA256으로 확인**한다. 즉 서명 안에서 nonce가 한 번 더 해시된다. Apple 문서에는 이 이상 자세한 설명이 없다. Apple 개발자 포럼에서 한 개발자가 "실기기 서명은 SHA256(SHA256(authData ‖ clientDataHash))에 대한 것이었고, 이렇게 바꾸니 검증됐다"고 보고했고, 이 코드와 같은 계산이다. 다만 Apple 직원의 답이 아니고, **나는 이 부분을 실기기 assertion으로 확인하지 못했다.** 실기기에서 `bad_signature`가 계속 나오면 이 줄부터 본다.

### 6단계와 카운터 저장: 한 트랜잭션으로

```python
@app.post("/api/check-in")
async def check_in(request: Request,
                   x_app_attest_key_id: str = Header(),
                   x_app_attest_assertion: str = Header()):
    client_data = await request.body()  # 원본 바이트
    assertion = b64decode(x_app_attest_assertion,
                          "assertion")
    row = db.execute(
        "SELECT public_key, counter FROM app_keys"
        " WHERE key_id = ?",
        (x_app_attest_key_id,)).fetchone()
    if row is None:
        raise ApiError(401, "unknown_key")
    public_key, stored = row
    try:
        result = verify_assertion(
            assertion, client_data=client_data,
            public_key=public_key,
            app_id=config.app_id,
            previous_counter=stored)
    except VerificationError as e:
        raise ApiError(401, e.code, str(e))
    check_category(result.validation_category,
                   required=False)
    payload = json.loads(client_data)
    challenge = payload["challenge"]
    ...
```

`request.body()`로 **파싱하기 전의 원본 바이트**를 받는 것이 핵심이다. FastAPI의 JSON 모델로 먼저 파싱하면 공백이나 키 순서가 바뀐 다른 바이트가 되어 해시가 맞지 않는다. 서명을 확인한 뒤에야 JSON을 파싱해 challenge를 꺼낸다.

7·8단계(extensions)는 assertion에도 확장이 붙어 있을 때만 확인한다(`required=False`). 실제 assertion 바이트를 보지 못해서 확장이 늘 붙는지 확인할 수 없었기 때문이다. 키 이름은 Apple 문서에 적힌 `validationCategory`, `bundleVersion`과 attestation의 `apple_..._01` 이름을 둘 다 찾게 했다.

마지막으로 challenge 소비와 counter 저장을 **한 트랜잭션**으로 묶는다.

```python
db.execute("BEGIN IMMEDIATE")
try:
    consume_challenge(challenge, "assert")
    cur = db.execute(
        "UPDATE app_keys SET counter = ?"
        " WHERE key_id = ? AND counter < ?",
        (result.counter, x_app_attest_key_id,
         result.counter))
    if cur.rowcount != 1:
        raise ApiError(401, "replayed_counter")
    db.execute("COMMIT")
except Exception:
    db.execute("ROLLBACK")
    raise
return {"status": "checked-in",
        "user": payload.get("userID")}
```

트랜잭션은 **"전부 하거나, 전부 안 하거나"**로 묶은 작업 단위다. challenge만 소비되고 counter 저장이 실패하는 어중간한 상태가 생기지 않는다. `BEGIN IMMEDIATE`는 SQLite에서 시작하자마자 쓰기 잠금을 잡는 방식이라, 같은 키로 동시에 들어온 두 요청이 같은 counter를 함께 통과하지 못한다.

`WHERE ... AND counter < ?`가 두 번째 안전장치다. 검증 함수에서 읽은 뒤 다른 요청이 counter를 먼저 올렸다면 이 UPDATE가 0행을 바꾸고 거절된다.

{: .question }
같은 assertion을 그대로 다시 보내면 어느 단계에서 막힐까? 서명은 여전히 맞다. 하지만 counter가 저장된 값과 같으므로 5단계에서 `replayed_counter`로 막힌다. 아래 curl 실습에서 직접 확인한다.

## 직접 돌려 보기

### 무엇을 어떻게 시험했나

솔직하게 적는다. 나는 **실기기에서 attestation이나 assertion을 받아 보지 않았다.** 대신 세 가지를 했다.

| 시험 | 데이터 | 확인한 것 |
| --- | --- | --- |
| Apple 예제 | Apple 가이드의 진짜 attestation | attestation 1~11단계 전부 |
| 가짜(synthetic) attestation | 직접 만든 가짜 CA와 키 | 서버 API 전체 흐름 |
| 가짜 assertion | 직접 만든 P-256 키로 서명 | 서명·카운터·RP ID·challenge 검사 |

`synthetic.py`는 **테스트 전용 가짜 데이터**를 만든다. 가짜 루트 CA와 중간 CA를 만들고, 그 아래에 nonce 확장을 넣은 credCert를 발급해 Apple과 같은 구조의 attestation을 꾸민다. 서버를 이 가짜 루트로 띄워야만 통과한다. Apple 루트로 검증하면 `bad_chain`으로 거절되는 것도 테스트로 확인했다.

### pytest

```bash
uv venv && uv pip install -r requirements.txt
python fetch_apple_files.py
python -m pytest -v
```

```text
test_server.py::test_full_flow PASSED                                    [  4%]
test_server.py::test_attest_challenge_single_use PASSED                  [  8%]
test_server.py::test_attest_unknown_challenge PASSED                     [ 12%]
test_server.py::test_attest_category_not_allowed PASSED                  [ 16%]
test_server.py::test_assert_challenge_reuse PASSED                       [ 20%]
test_server.py::test_assert_replayed_request PASSED                      [ 25%]
test_server.py::test_assert_attest_challenge_not_accepted PASSED         [ 29%]
test_server.py::test_failed_assert_keeps_challenge_and_counter PASSED    [ 33%]
test_server.py::test_unknown_key PASSED                                  [ 37%]
test_server.py::test_rate_limit PASSED                                   [ 41%]
test_server.py::test_expired_challenge PASSED                            [ 45%]
test_verify.py::test_apple_sample_passes_at_its_time PASSED              [ 50%]
test_verify.py::test_apple_sample_expired_today PASSED                   [ 54%]
test_verify.py::test_apple_sample_rejects[change0-nonce_mismatch] PASSED [ 58%]
test_verify.py::test_apple_sample_rejects[change1-key_id_mismatch] PASSED [ 62%]
test_verify.py::test_apple_sample_rejects[change2-rp_id_mismatch] PASSED [ 66%]
test_verify.py::test_apple_sample_rejects[change3-bad_aaguid] PASSED     [ 70%]
test_verify.py::test_synthetic_attestation_passes_with_fake_root PASSED  [ 75%]
test_verify.py::test_synthetic_attestation_rejected_by_apple_root PASSED [ 79%]
test_verify.py::test_assertion_valid PASSED                              [ 83%]
test_verify.py::test_assertion_wrong_signature PASSED                    [ 87%]
test_verify.py::test_assertion_body_changed PASSED                       [ 91%]
test_verify.py::test_assertion_replayed_counter PASSED                   [ 95%]
test_verify.py::test_assertion_wrong_rp_id PASSED                        [100%]

======================== 24 passed, 1 warning in 0.20s =========================
```

남은 경고 1개는 FastAPI의 `TestClient`가 내는 라이브러리 사용 중단 예고였다. 이 경고는 `pytest.ini`에서 숨겼다.

`test_failed_assert_keeps_challenge_and_counter`는 다른 키로 서명한 요청이 `bad_signature`로 거절된 뒤에도, 같은 challenge와 counter 1로 정상 요청이 통과하는지 본다. 서명 확인은 challenge를 소비하기 **전**에 하므로, 위조 요청 하나로 정상 사용자의 challenge가 날아가지 않는다.

### 서버 띄우고 curl로 호출하기

가짜 CA로 서버를 띄운다. `demo_client.py`는 iPhone 역할을 하는 **가짜 클라이언트**다.

```bash
python demo_client.py init   # demo/root.pem 생성
APP_ID=ABCDE12345.com.example.checkin \
APPATTEST_ENV=development \
ROOT_CA_PATH=demo/root.pem \
DB_PATH=demo.sqlite3 \
ALLOWED_CATEGORIES=2,3,4 \
uvicorn server:app --port 8765
```

다른 터미널에서 challenge를 받고, 가짜 attestation을 등록한다.

```bash
curl -s -X POST localhost:8765/challenge \
  -H 'Content-Type: application/json' \
  -d '{"purpose":"attest"}'
```

```text
{"challenge":"tUHmTN8GqtIz2Hb3P/Q+uVLYvik0sGwSAT4Ag9fj9e0=","expires_in":300}
```

```bash
CH='tUHmTN8GqtIz2Hb3P/Q+uVLYvik0sGwSAT4Ag9fj9e0='
python demo_client.py attest "$CH" > demo/attest.json
curl -s -X POST localhost:8765/attest \
  -H 'Content-Type: application/json' \
  -d @demo/attest.json
```

```text
{"status":"registered"} [201]
```

같은 파일을 한 번 더 보내면 challenge가 이미 쓰여 거절된다.

```text
{"error":"bad_challenge","detail":"unknown, used or expired"} [401]
```

이제 assert용 challenge로 본문을 만들고 서명해서 보호 API를 호출한다.

```bash
# CH2: {"purpose":"assert"}로 받은 challenge
A=$(python demo_client.py assert "$CH2" 1)
curl -s -X POST localhost:8765/api/check-in \
  -H 'Content-Type: application/json' \
  -H "X-App-Attest-Key-Id: $(cat demo/key_id)" \
  -H "X-App-Attest-Assertion: $A" \
  --data-binary @demo/body.json
```

`demo/body.json`의 내용과 응답:

```text
{"challenge": "E/MBlkgy6ceqH9rc37Be1Fo4/gu0bkCH2mpJpb2AgaI=", "userID": "u1", "date": "2026-11-28"}
{"status":"checked-in","user":"u1"} [200]
```

`-d`가 아니라 `--data-binary`를 쓴 이유는, 서명한 바이트를 한 글자도 바꾸지 않고 보내기 위해서다. 같은 요청을 그대로 다시 보내고, 본문의 `u1`을 `u2`로 바꿔서도 보내 봤다.

```text
--- same request again
{"error":"replayed_counter","detail":"counter did not grow"} [401]
--- body changed
{"error":"bad_signature","detail":"signature is not valid"} [401]
```

서버 로그에는 실패 이유가 코드로 남는다. keyID는 앞 8글자만 남겼다.

```text
INFO:appattest:attested key DkrM6pDH...
WARNING:appattest:/attest bad_challenge -> unknown, used or expired
WARNING:appattest:/api/check-in replayed_counter -> counter did not grow
WARNING:appattest:/api/check-in bad_signature -> signature is not valid
```

DB에는 counter가 1로 올라가 있었다.

```bash
sqlite3 demo.sqlite3 "select substr(key_id,1,8), counter,
  environment, category, bundle_ver, length(receipt)
  from app_keys"
```

```text
DkrM6pDH|1|development|3|1|17
```

(receipt 17바이트는 가짜 값 `SYNTHETIC-RECEIPT`다.)

## 오류 처리

`DCAppAttestService`는 `DCError`를 던진다. 원인별로 대응이 다르다.

| 오류 | 의미 | 앱의 대응 |
| --- | --- | --- |
| `.featureUnsupported` | 이 환경에서 App Attest를 쓸 수 없음 | App Attest 없는 경로로 처리 |
| `.invalidKey` | 키가 없거나 쓸 수 없음 (재설치·복원 등) | 저장된 `keyID`를 지우고 1단계부터 다시 |
| `.invalidInput` | 잘못된 인자 | 해시 길이(32바이트) 등 호출 코드를 점검 |
| `.serverUnavailable` | Apple 서버에 연결할 수 없음 | 같은 키로 잠시 뒤 재시도 |
| `.unknownSystemFailure` | 그 밖의 시스템 오류 | 재시도 후 실패하면 대체 경로 |

```swift
do {
    try await sendCheckIn(userID: userID)
} catch let error as DCError
            where error.code == .invalidKey {
    attestClient.resetKey()
    // 새 키로 한 번만 다시 시도
    try await sendCheckIn(userID: userID)
}
```

서버가 `unknown_key`를 돌려줄 때도 같은 처리가 필요하다. 서버 DB를 정리했거나 등록이 실패한 키일 수 있으므로, 앱은 `resetKey()` 후 한 번만 다시 등록한다.

## 정책: 무엇을 막고 무엇을 막지 못하는가

App Attest가 증명하는 것은 "이 요청은 정상 Apple 기기에서 실행 중인 우리 앱이 만든 키로 서명됐다"는 사실이다. 다음은 증명하지 않는다.

- 사용자가 악의가 없다는 것. 정상 앱으로도 어뷰징할 수 있다.
- 사용자 인증. 로그인과 App Attest는 별개이며, 서버는 둘 다 확인한다.
- 모든 탈옥·변조 환경의 차단. Apple 문서도 OS를 변조한 기기는 제한을 우회할 수 있다고 적고 있다.

WWDC21 세션 "Mitigate fraud with App Attest and DeviceCheck"는 검증 실패를 바로 차단하지 말고 **위험 신호**로 쓰라고 권한다. 실패한 호출자를 먼저 "신뢰하지 않음"으로 분류하고, 위험 평가에 따라 민감한 기능을 허용할지 정하라는 것이다. `isSupported`가 `false`인 경우, 출시 초기 요청 제한(throttling), 네트워크 오류도 신호의 하나로 다루라고 한다.

### 실무에서는

아래는 Apple 문서와 직접 만든 서버를 바탕으로 한 내 판단이다.

{: .tip }
**키는 기기의 사용자 계정마다 하나.** Apple은 "기기마다, 사용자 계정마다 고유한 키"를 만들고 한 기기에서 여러 사용자가 키를 같이 쓰지 말라고 한다. 같이 쓰면 변조된 기기 한 대가 여러 사용자에게 assertion을 대 주는 공격을 찾기 어렵다. 서버는 사용자 한 명에게 (키, receipt) 쌍을 여러 개 저장할 수 있게 설계한다. 이 글의 `app_keys` 표에 사용자 ID 열을 더하면 된다.

{: .tip }
**receipt는 바로 저장한다.** Apple은 attestation이 성공하면 receipt를 즉시 검증·저장하라고 한다. 이 receipt를 Apple 서버(개발: `data-development.appattest.apple.com`, 운영: `data.appattest.apple.com`의 `/v1/attestationData`)에 보내면, 최근 30일 동안 그 기기에서 우리 앱용으로 증명된 키의 대략적인 개수(위험 지표)가 담긴 새 receipt를 받는다. 이 서버는 receipt를 저장만 한다. receipt의 PKCS #7 서명 검증과 위험 지표 조회는 구현하지 않았다.

{: .tip }
**challenge 발급에 요청 제한을 둔다.** challenge는 누구나 요청할 수 있으므로, 막지 않으면 DB가 쓰레기 challenge로 찬다. 이 서버는 IP당 1분에 30개로 제한하고 넘으면 `429`를 준다. 메모리에 기록하는 방식이라 서버가 한 대일 때만 맞다. 여러 대라면 Redis 같은 공유 저장소로 옮긴다. 만료된 challenge를 주기적으로 지우는 작업도 따로 둔다.

{: .tip }
**단계적으로 켜고, 실패 시 대체 경로를 둔다.** Apple은 사용자가 많은 앱이면 하루 1천만 명 이하로 고르게 늘리고, 전체 설치 기준 `attestKey` 호출을 초당 100건 미만으로 유지하라고 권한다. 처음 몇 주는 서버가 검증 결과를 기록만 하고(차단하지 않고) 실패율을 본 뒤, 위험도가 높은 API부터 차단으로 넘어간다. 출석 포인트라면 App Attest가 없는 요청에 한도를 낮게 주고, 송금처럼 위험한 요청이라면 추가 인증을 요구하는 식이다.

{: .tip }
**개발과 운영을 섞지 않는다.** 서버의 `APPATTEST_ENV`와 앱 entitlement 환경이 다르면 모든 증명이 `bad_aaguid`로 실패한다. 개발 서버와 운영 서버를 나누거나, 최소한 키를 환경별로 따로 저장한다. Apple은 개발 환경 키·receipt를 운영에서 쓸 수 없다고 명시한다.

{: .tip }
**로그에는 이유 코드를 남기고 원본은 남기지 않는다.** 실패 이유(`nonce_mismatch`, `bad_aaguid` 등)별로 개수를 세면 앱 버그인지 공격인지 구분하는 데 도움이 된다. attestation 원본이나 clientData 전체는 개인 정보가 들어갈 수 있으므로 기본 로그에 넣지 않는다.

## 점검 목록

- 시뮬레이터가 아닌 실기기에서 시험했는가
- entitlement 환경과 서버의 `aaguid` 기준이 같은가
- challenge를 서버에서 발급하고, 만료 시간을 두고, 한 번만 쓰게 했는가
- 서버가 `clientDataHash`를 직접 계산하는가
- keyID 비교에 공개 키의 X9.62 비압축 점(65바이트) 해시를 쓰는가
- 같은 공개 키의 중복 등록을 막는가
- 서버 등록이 성공한 뒤에만 앱이 `keyID`를 저장하는가
- `invalidKey`, `unknown_key`에서 새 키를 만드는 경로가 있는가
- assertion 본문을 파싱 전 원본 바이트로 검증하는가
- challenge 소비와 counter 갱신을 한 트랜잭션으로 묶었는가
- 지원하지 않는 기기와 검증 실패에 대한 정책이 있는가

## 정리

{: .note }
서버는 attestation에서 **인증서 체인 → nonce → keyID → RP ID → counter 0 → aaguid → credentialId → extensions** 순서로 확인하고, 통과하면 공개 키와 counter를 저장한다. assertion에서는 **원본 본문 해시 → nonce → 서명 → RP ID → counter 증가 → challenge**를 확인하고, challenge 소비와 counter 저장을 한 번에 처리한다. Apple 예제로 attestation 검증 전체를, 가짜 키로 assertion 검증과 재전송 방지를 확인했다. 실기기 데이터로는 확인하지 않았다.

## 주요 API

| API | 역할 |
| --- | --- |
| `DCAppAttestService.shared` | App Attest 서비스 싱글턴 |
| `isSupported` | 현재 기기·환경에서 사용할 수 있는지 |
| `generateKey() async throws -> String` | Secure Enclave에 키를 만들고 keyID를 돌려준다 |
| `attestKey(_:clientDataHash:) async throws -> Data` | Apple 서버를 거쳐 키 증명(attestation)을 받는다. 키당 한 번 |
| `generateAssertion(_:clientDataHash:) async throws -> Data` | 요청 데이터 해시에 서명한 assertion. 요청마다 |
| `DCError.Code` | `.featureUnsupported`, `.invalidKey`, `.invalidInput`, `.serverUnavailable`, `.unknownSystemFailure` |
| `SHA256.hash(data:)` | CryptoKit. `clientDataHash` 계산 |
| `com.apple.developer.devicecheck.appattest-environment` | entitlement. `development` 또는 `production` |

## 실습 소스

Apple 루트 인증서와 Apple 예제 attestation은 저장소에 넣지 않았다. `fetch_apple_files.py`가 Apple 사이트에서 직접 내려받는다.

- [appattest_verify.py]({{ '/assets/examples/ios/app-attest/appattest_verify.py' | relative_url }}): attestation·assertion 검증 로직
- [server.py]({{ '/assets/examples/ios/app-attest/server.py' | relative_url }}): FastAPI 서버, SQLite 저장, 요청 제한
- [synthetic.py]({{ '/assets/examples/ios/app-attest/synthetic.py' | relative_url }}): 테스트용 가짜 CA·attestation·assertion
- [test_verify.py]({{ '/assets/examples/ios/app-attest/test_verify.py' | relative_url }}), [test_server.py]({{ '/assets/examples/ios/app-attest/test_server.py' | relative_url }}): pytest 테스트 24개
- [walkthrough.py]({{ '/assets/examples/ios/app-attest/walkthrough.py' | relative_url }}): Apple 예제를 단계별로 출력
- [demo_client.py]({{ '/assets/examples/ios/app-attest/demo_client.py' | relative_url }}): curl 실습용 가짜 클라이언트
- [fetch_apple_files.py]({{ '/assets/examples/ios/app-attest/fetch_apple_files.py' | relative_url }}): Apple 루트 CA와 예제 내려받기
- [requirements.txt]({{ '/assets/examples/ios/app-attest/requirements.txt' | relative_url }}), [pytest.ini]({{ '/assets/examples/ios/app-attest/pytest.ini' | relative_url }})

## 이어서 읽기

- [X.509 인증서]({{ '/pki/x509/' | relative_url }})
- [Keychain]({{ '/ios/keychain/' | relative_url }})
- [비동기 단위 테스트와 UI 테스트]({{ '/ios/unit-test/' | relative_url }})

## 참고

- [Apple: Establishing your app's integrity](https://developer.apple.com/documentation/devicecheck/establishing-your-app-s-integrity)
- [Apple: Validating apps that connect to your server](https://developer.apple.com/documentation/devicecheck/validating-apps-that-connect-to-your-server)
- [Apple: Attestation Object Validation Guide](https://developer.apple.com/documentation/devicecheck/attestation-object-validation-guide)
- [Apple: Assessing fraud risk](https://developer.apple.com/documentation/devicecheck/assessing-fraud-risk)
- [Apple: Preparing to use the app attest service](https://developer.apple.com/documentation/devicecheck/preparing-to-use-the-app-attest-service)
- [Apple: DCAppAttestService](https://developer.apple.com/documentation/devicecheck/dcappattestservice)
- [Apple: Apple App Attestation Root CA](https://www.apple.com/certificateauthority/Apple_App_Attestation_Root_CA.pem)
- [WWDC21: Mitigate fraud with App Attest and DeviceCheck](https://developer.apple.com/videos/play/wwdc2021/10244/)
- [Apple Developer Forums: App Attest Validation Guide sample appears internally inconsistent](https://developer.apple.com/forums/thread/842509)
- [Apple Developer Forums: Unable to validate app attest assertion signature](https://developer.apple.com/forums/thread/803133)
- [W3C: Web Authentication, Authenticator Data](https://www.w3.org/TR/webauthn/#sec-authenticator-data)
- [cryptography: X.509 verification](https://cryptography.io/en/latest/x509/verification/)
