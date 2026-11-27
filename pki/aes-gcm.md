---
title: "대칭 암호와 AES-GCM"
description: "대칭 키 암호와 AES, 블록 암호 운용 모드를 설명하고, 암호화와 변조 검사를 함께 하는 인증 암호 AES-GCM의 키·nonce·부가 데이터·인증 태그를 Python으로 확인합니다. nonce를 재사용하면 평문이 드러나는 것도 직접 재현합니다."
parent: "보안"
nav_order: 15
permalink: /pki/aes-gcm/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [PKI, AES, GCM, AEAD, Symmetric]
---

# 대칭 암호와 AES-GCM
{: .no_toc }

{% include article-toc.md %}

RSA나 ECC 같은 공개 키 암호는 키를 나누는 문제를 풀어 주지만 느리고, 한 번에 암호화할 수 있는 길이도 짧다([RSA]({{ '/pki/rsa/' | relative_url }}) 글의 190바이트 제한). 실제 데이터는 거의 전부 **대칭 키 암호**로 암호화한다. HTTPS도, 디스크 암호화도, 메신저의 종단 간 암호화도 마지막에는 대칭 암호가 데이터를 감싼다.

## 대칭 키 암호

**대칭 키 암호**는 암호화와 복호화에 **같은 키**를 쓰는 방식이다. 빠르고 길이 제한이 없지만, 그 키를 상대에게 어떻게 안전하게 전달하느냐가 문제다. 그래서 실제 프로토콜은 공개 키 암호로 대칭 키를 합의하거나 전달하고([Diffie-Hellman]({{ '/pki/pkcs3/' | relative_url }}), [ML-KEM]({{ '/pki/pqc-kyber/' | relative_url }})), 데이터는 대칭 키로 암호화한다.

**AES(Advanced Encryption Standard)**는 현재 표준 대칭 암호다. 16바이트 블록 하나를 128·192·256비트 키로 바꾸는 **블록 암호**이며, 대부분의 CPU가 AES 전용 명령어를 갖고 있어 매우 빠르다. 국내 표준인 [ARIA]({{ '/pki/aria/' | relative_url }})도 같은 종류의 블록 암호다.

## 블록 하나로는 부족하다: 운용 모드

AES는 16바이트 하나만 처리한다. 긴 데이터를 암호화하려면 블록들을 어떻게 이어 처리할지 정해야 하는데, 이것이 **운용 모드(mode of operation)**다.

| 모드 | 특징 | 변조 검사 |
| --- | --- | --- |
| ECB | 블록마다 따로 암호화. 같은 평문 블록은 같은 암호문 → 패턴이 드러남 | 없음. **사용 금지** |
| CBC | 앞 블록 결과를 다음 블록에 섞음. [패딩]({{ '/pki/padding/' | relative_url }}) 필요 | 없음. 따로 MAC 필요 |
| CTR | 카운터를 암호화해 만든 키스트림을 XOR. 패딩 불필요 | 없음 |
| **GCM** | CTR 암호화 + 인증 태그 | **있음** (AEAD) |
| ChaCha20-Poly1305 | AES 대신 ChaCha20 스트림 암호 + 태그 | **있음** (AEAD) |

ECB·CBC·CTR은 **기밀성**(내용을 못 읽게)만 준다. 공격자가 암호문을 바꿔치기해도 복호화는 되고 엉뚱한 평문이 나올 뿐이다. 그래서 지금은 암호화와 변조 검사를 함께 하는 **AEAD(Authenticated Encryption with Associated Data, 인증 암호)**를 쓰는 것이 기본이다. AES-GCM과 ChaCha20-Poly1305가 대표적이고, TLS 1.3은 이 둘만 허용한다.

## AES-GCM의 입력과 출력

| 입력·출력 | 뜻 | 비밀인가 |
| --- | --- | --- |
| 키 | 16 또는 32바이트 | **비밀** |
| nonce (IV) | 12바이트. 같은 키로 **절대 두 번 쓰면 안 되는** 값 | 아님. 암호문과 함께 보낸다 |
| 평문 | 암호화할 데이터 | 비밀 |
| 부가 데이터(AAD) | 암호화하지 않지만 변조는 막고 싶은 데이터. 헤더, 사용자 ID 등 | 아님 |
| 암호문 | 평문과 같은 길이 | |
| 인증 태그 | 16바이트. 암호문과 부가 데이터가 바뀌지 않았다는 증거 | 아님 |

## Python으로 확인하기

`cryptography` 패키지(50.0.2)로 실행했다.

```python
import os
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

key = AESGCM.generate_key(bit_length=256)
aes = AESGCM(key)

plaintext = "계좌 비밀번호: 1234".encode()
header = b"user-id=42"            # 암호화하지 않지만 변조는 막고 싶은 값
nonce = os.urandom(12)            # 같은 키로 절대 재사용하면 안 된다

ct = aes.encrypt(nonce, plaintext, header)
print("평문", len(plaintext), "바이트 → 암호문+태그", len(ct), "바이트")
print("복호화:", aes.decrypt(nonce, ct, header).decode())

bad = bytearray(ct); bad[0] ^= 1          # 암호문 1비트 변조
try:
    aes.decrypt(nonce, bytes(bad), header)
except InvalidTag:
    print("암호문 변조 → InvalidTag")

try:
    aes.decrypt(nonce, ct, b"user-id=43")  # 부가 데이터 변조
except InvalidTag:
    print("부가 데이터 변조 → InvalidTag")
```

```text
평문 25 바이트 → 암호문+태그 41 바이트
복호화: 계좌 비밀번호: 1234
암호문 변조 → InvalidTag
부가 데이터 변조 → InvalidTag
```

- 출력이 평문보다 16바이트 긴 것은 인증 태그가 붙었기 때문이다.
- 암호문을 1비트만 바꿔도, 암호화하지 않은 부가 데이터의 사용자 ID만 바꿔도 복호화 자체가 실패한다. 변조된 평문을 받는 일이 없다.
- 복호화 함수가 예외를 던지면 **결과를 절대 쓰지 않는다.** 일부 라이브러리는 스트리밍 복호화 중 태그 검증 전에 평문 조각을 내주는데, 검증이 끝나기 전의 평문은 믿지 않는다.

`user-id`를 부가 데이터로 넣는 이유는, 공격자가 A 사용자의 암호문을 B 사용자의 레코드로 옮겨 붙이는 공격을 막기 위해서다. 암호문은 멀쩡해도 부가 데이터가 달라 복호화에 실패한다.

## nonce를 재사용하면

GCM 내부의 CTR 모드는 키와 nonce로 만든 키스트림을 평문에 XOR한다. 같은 키와 nonce로 두 평문을 암호화하면 **같은 키스트림**이 쓰이므로, 두 암호문을 XOR하면 키스트림이 지워지고 두 평문의 XOR만 남는다.

```python
p1, p2 = b"attack at dawn!!", b"retreat at noon!"
n = os.urandom(12)
c1 = aes.encrypt(n, p1, None)[:16]
c2 = aes.encrypt(n, p2, None)[:16]
x = bytes(a ^ b for a, b in zip(c1, c2))
print("c1^c2 == p1^p2:", x == bytes(a ^ b for a, b in zip(p1, p2)))
print("p1을 아는 공격자가 복원한 p2:", bytes(a ^ b for a, b in zip(x, p1)).decode())
```

```text
c1^c2 == p1^p2: True
p1을 아는 공격자가 복원한 p2: retreat at noon!
```

키를 몰라도, 한쪽 평문을 알거나 추측할 수 있으면(HTTP 헤더처럼 형식이 정해진 데이터는 쉽게 추측된다) 다른 쪽 평문이 그대로 드러난다. GCM에서는 여기에 더해 인증 태그를 위조할 수 있는 정보까지 새어 나간다. **nonce 재사용은 GCM에서 가장 치명적인 실수다.**

nonce를 안전하게 만드는 방법은 둘이다.

- 매번 12바이트 난수를 쓴다. 같은 키로 약 2³²(약 43억)번 암호화하기 전에 키를 바꾼다.
- 키마다 1씩 늘어나는 카운터를 쓴다. 카운터 상태를 잃어버리거나(재시작, 백업 복원) 여러 서버가 같은 키를 나눠 쓰면 중복될 수 있으니 주의한다.

## 실무 원칙

- 새로 만든다면 AES-256-GCM이나 ChaCha20-Poly1305를 쓴다. ECB는 쓰지 않고, CBC는 레거시 호환에만 쓴다.
- 키는 CSPRNG로 만들고([PKCS #14]({{ '/pki/pkcs13-15/' | relative_url }})), 비밀번호에서 만들 때는 KDF를 거친다([PKCS #5]({{ '/pki/pkcs5/' | relative_url }})).
- nonce는 절대 재사용하지 않는다.
- 저장 형식에 `버전 | 키 ID | nonce | 암호문 | 태그`를 함께 남겨 키 교체에 대비한다.
- iOS에서는 CryptoKit의 `AES.GCM.seal(_:using:)`과 `ChaChaPoly`를 쓴다. 키는 Keychain이나 Secure Enclave에 보관한다.

## 정리

- 실제 데이터는 대칭 키 암호로 암호화하고, 대칭 키는 공개 키 암호로 나눈다.
- AES는 블록 암호이며, 긴 데이터에는 운용 모드가 필요하다. ECB는 금지, CBC·CTR은 변조 검사가 없다.
- AES-GCM은 암호화와 변조 검사를 함께 하는 AEAD이며, 부가 데이터로 문맥까지 묶을 수 있다.
- 같은 키로 nonce를 재사용하면 평문이 드러난다는 것을 직접 확인했다.

## 실습 소스

- [aes_gcm.py]({{ '/assets/examples/pki/aes_gcm.py' | relative_url }}): `pip install cryptography` 후 실행

## 참고

- [NIST SP 800-38D: GCM](https://csrc.nist.gov/pubs/sp/800/38/d/final)
- [RFC 5116: An Interface and Algorithms for Authenticated Encryption](https://www.rfc-editor.org/rfc/rfc5116.html)
- [RFC 8439: ChaCha20 and Poly1305](https://www.rfc-editor.org/rfc/rfc8439.html)
- [cryptography: AEAD](https://cryptography.io/en/latest/hazmat/primitives/aead/)
- [Apple: CryptoKit AES.GCM](https://developer.apple.com/documentation/cryptokit/aes/gcm)
