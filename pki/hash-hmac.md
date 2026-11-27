---
title: "해시 함수와 HMAC"
description: "암호학적 해시 함수의 성질(고정 길이, 일방향, 충돌 저항)과 SHA-2·SHA-3, 해시만으로 변조를 막을 수 없는 이유, 비밀 키로 무결성과 출처를 확인하는 HMAC, 시간이 일정한 비교를 Python 실행 결과로 설명합니다."
parent: "보안"
nav_order: 14
permalink: /pki/hash-hmac/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [PKI, Hash, SHA-256, HMAC]
---

# 해시 함수와 HMAC
{: .no_toc }

{% include article-toc.md %}

전자서명, 비밀번호 저장, 파일 무결성 확인, 블록체인, Git 커밋 ID까지, 보안 기술의 바닥에는 거의 항상 **해시 함수**가 있다. 이 글에서는 해시가 무엇을 보장하고 무엇을 보장하지 않는지, 그리고 그 빈틈을 메우는 **HMAC**을 정리한다.

## 해시 함수란

**암호학적 해시 함수**는 길이가 제각각인 입력을 받아, 정해진 길이의 값(해시, 다이제스트)을 내놓는 함수다. 다음 성질을 가져야 한다.

| 성질 | 뜻 |
| --- | --- |
| 결정성 | 같은 입력은 언제나 같은 값 |
| 고정 길이 | 입력이 1바이트든 1GB든 결과 길이는 같다 (SHA-256은 32바이트) |
| 눈사태 효과 | 입력이 1비트만 바뀌어도 결과가 완전히 달라진다 |
| 일방향성 | 결과에서 입력을 거꾸로 알아낼 수 없다 |
| 충돌 저항성 | 같은 결과를 내는 서로 다른 두 입력을 찾을 수 없다 |

Python으로 확인해 보자.

```python
import hashlib

for text in ["이체 금액: 10000원", "이체 금액: 10001원"]:
    print(hashlib.sha256(text.encode()).hexdigest()[:32], text)

print(len(hashlib.sha256(b"a").digest()), len(hashlib.sha256(b"a" * 1_000_000).digest()), "bytes")
```

```text
5f64aacf8bcb12dac63b3e4121a9062c 이체 금액: 10000원
4ce96acafec8cc934035384e6a84b76d 이체 금액: 10001원
32 32 bytes
```

숫자 하나가 바뀌었을 뿐인데 결과는 전혀 닮지 않았다. 1바이트 입력과 1MB 입력의 결과는 둘 다 32바이트다. 그래서 해시는 큰 데이터를 대표하는 짧은 **지문**으로 쓰인다.

## 어떤 해시를 쓰나

| 알고리즘 | 결과 길이 | 상태 |
| --- | --- | --- |
| MD5 | 16바이트 | 충돌을 실제로 만들 수 있다. 보안 용도 사용 금지 |
| SHA-1 | 20바이트 | 2017년 실제 충돌(SHAttered)이 공개됨. 새 서명에 사용 금지 |
| SHA-256, SHA-384, SHA-512 (SHA-2) | 32·48·64바이트 | 현재 표준. 가장 널리 쓰인다 |
| SHA3-256 등 (SHA-3) | 32바이트 등 | SHA-2와 다른 구조의 표준. SHA-2의 대안 |

새로 만드는 시스템은 SHA-256 이상을 쓴다. MD5와 SHA-1은 보안과 무관한 용도(캐시 키, 중복 파일 찾기)에만 남아 있다.

## 해시만으로는 변조를 막지 못한다

서버가 클라이언트에 `{"to":"lee","amount":10000}`과 그 SHA-256 값을 함께 보낸다고 하자. 받는 쪽이 해시를 다시 계산해 비교하면 "전송 중에 우연히 깨졌는지"는 알 수 있다. 하지만 공격자가 중간에서 금액을 90000으로 바꾸고 **해시도 새로 계산해** 바꿔 끼우면 받는 쪽은 알아챌 수 없다. 해시 함수는 공개돼 있어 누구나 계산할 수 있기 때문이다.

[PKCS #2]({{ '/pki/pkcs2/' | relative_url }}) 글에서 본 "다운로드 페이지의 해시 값" 문제와 같다. 변조를 막으려면 **공격자는 모르고 보내는 쪽과 받는 쪽만 아는 것**이 계산에 들어가야 한다.

| 방법 | 들어가는 비밀 | 누가 검증하나 |
| --- | --- | --- |
| HMAC | 양쪽이 공유한 비밀 키 | 같은 키를 가진 쪽 |
| 전자서명 | 보내는 쪽의 개인 키 | 공개 키를 가진 누구나 |

## HMAC

**HMAC(Hash-based Message Authentication Code)**은 비밀 키와 메시지를 해시 함수에 정해진 방식으로 넣어 만든 검사값이다. 키가 없으면 올바른 값을 만들 수 없으므로, 값이 맞으면 "메시지가 바뀌지 않았고, 키를 가진 쪽이 만들었다"는 것을 확인할 수 있다.

```python
import hashlib
import hmac
import secrets

key = secrets.token_bytes(32)
msg = b'{"to":"lee","amount":10000}'
tag = hmac.new(key, msg, hashlib.sha256).hexdigest()

def verify(key, msg, tag):
    expected = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, tag)

print("원본 검증:", verify(key, msg, tag))
print("변조 검증:", verify(key, b'{"to":"lee","amount":90000}', tag))
print("다른 키:", verify(secrets.token_bytes(32), msg, tag))
```

```text
원본 검증: True
변조 검증: False
다른 키: False
```

키는 실행할 때마다 새로 만들므로 `tag` 값은 매번 다르게 나온다. 금액을 바꾸면 검증에 실패하고, 키가 다르면 원본조차 검증되지 않는다.

### 왜 hash(key + message)가 아니라 HMAC인가

"키를 앞에 붙여 해시하면 되지 않나?" 싶지만, SHA-256 같은 해시는 내부 구조 때문에 `hash(key + message)`의 결과만 알면 키를 몰라도 `hash(key + message + 추가 데이터)`를 계산할 수 있다(길이 확장 공격). HMAC은 키를 두 번, 서로 다른 방식으로 섞어 이 문제를 막도록 설계됐다. 직접 조합하지 말고 표준 HMAC을 쓴다.

### 비교는 시간이 일정한 함수로

검증할 때 `expected == tag`처럼 일반 문자열 비교를 쓰면, 첫 글자부터 비교하다 다른 글자를 만나는 순간 멈춘다. 공격자는 응답 시간의 미세한 차이로 "몇 글자까지 맞았는지" 알아내 검사값을 한 글자씩 맞혀 갈 수 있다(타이밍 공격). `hmac.compare_digest`는 내용과 상관없이 같은 시간이 걸리도록 비교한다. Swift의 CryptoKit도 `HMAC<SHA256>.isValidAuthenticationCode(_:authenticating:using:)`로 같은 기능을 제공한다.

## 어디에 쓰이나

| 용도 | 예 |
| --- | --- |
| API 요청 서명 | AWS 요청 서명(SigV4), 결제 대행사 웹훅 검증 |
| 토큰 | JWT의 `HS256` 서명 |
| 키 유도 | HKDF, PBKDF2 내부의 의사난수 함수([PKCS #5]({{ '/pki/pkcs5/' | relative_url }})) |
| TLS | 핸드셰이크 메시지 무결성, 키 유도([TLS 1.3]({{ '/pki/tls13/' | relative_url }})) |

웹훅을 받는 서버라면, 결제 대행사가 보낸 요청 본문 바이트 그대로를 공유 키로 HMAC 계산해 헤더의 값과 `compare_digest`로 비교하는 것이 기본이다. 본문을 JSON으로 파싱했다가 다시 직렬화한 바이트로 계산하면 공백·키 순서 차이로 값이 달라진다.

## 비밀번호 저장에는 HMAC도 SHA-256도 아니다

해시는 빠르게 계산되도록 설계됐다. 비밀번호를 SHA-256으로 저장하면, 유출된 해시를 GPU로 초당 수십억 개씩 대입해 볼 수 있다. 비밀번호에는 일부러 느리고 메모리를 많이 쓰게 만든 전용 함수(Argon2id, scrypt, bcrypt, PBKDF2)를 쓴다. [Spring Security]({{ '/spring/security/' | relative_url }}) 글의 `{bcrypt}` 저장값이 그 예다.

## 정리

- 해시 함수는 임의 길이 입력을 고정 길이 지문으로 바꾸며, 일방향이고 충돌을 찾기 어려워야 한다.
- MD5와 SHA-1은 보안 용도로 쓰지 않는다. SHA-256 이상을 쓴다.
- 해시는 누구나 계산할 수 있으므로 혼자서는 변조를 막지 못한다.
- HMAC은 공유 비밀 키로 무결성과 출처를 확인한다. 직접 `hash(key + msg)`를 만들지 말고 표준 HMAC과 시간이 일정한 비교를 쓴다.
- 비밀번호 저장에는 느리게 설계된 전용 함수를 쓴다.

## 실습 소스

- [hash_hmac.py]({{ '/assets/examples/pki/hash_hmac.py' | relative_url }}): Python 표준 라이브러리만 사용

## 참고

- [NIST FIPS 180-4: Secure Hash Standard](https://csrc.nist.gov/pubs/fips/180-4/upd1/final)
- [RFC 2104: HMAC](https://www.rfc-editor.org/rfc/rfc2104.html)
- [SHAttered: SHA-1 충돌](https://shattered.io/)
- [Python: hmac](https://docs.python.org/3/library/hmac.html)
