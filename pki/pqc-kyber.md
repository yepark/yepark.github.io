---
title: "PQC와 ML-KEM(Kyber)"
description: "양자 컴퓨터 위협에 대응하는 격자 기반 키 교환 알고리즘 ML-KEM(CRYSTALS-Kyber)의 동작 원리, NIST 표준화 배경, RSA·ECDH와의 차이를 설명합니다."
parent: "PKI & 암호"
nav_order: 7
permalink: /pki/pqc-kyber/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [PKI, PQC, Kyber, ML-KEM, NIST, 격자암호]
---

# PQC와 ML-KEM(Kyber)
{: .no_toc }

{% include article-toc.md %}

현재 인터넷 보안의 핵심인 RSA와 ECDH는 같은 약점을 공유한다. 큰 수의 소인수분해나 타원 곡선 이산 로그 문제가 어렵다는 가정 위에 성립한다. 고전 컴퓨터로는 이 문제를 현실적인 시간 안에 풀 수 없지만, 충분히 큰 양자 컴퓨터는 쇼어 알고리즘으로 다항 시간에 풀 수 있다.

**PQC(Post-Quantum Cryptography, 양자 내성 암호)**는 양자 컴퓨터가 존재하더라도 안전한 알고리즘을 설계하는 분야다. NIST는 2016년부터 PQC 표준화를 진행해 2024년 세 가지 알고리즘을 최종 표준으로 발표했고, 그 중 키 교환과 암호화를 담당하는 알고리즘이 **ML-KEM**이다. 원래 이름은 **CRYSTALS-Kyber**다.

## 양자 컴퓨터가 위협이 되는 이유

쇼어 알고리즘은 1994년에 발표됐다. 양자 컴퓨터가 충분한 큐비트를 갖추면 RSA-2048을 몇 시간 안에 풀 수 있다는 이론적 근거다. 2024년 현재 이 규모의 양자 컴퓨터는 존재하지 않지만, 준비하지 않는 것은 위험하다.

**"지금 수집해서 나중에 복호화"(Harvest Now, Decrypt Later)** 전략이 현실적인 위협이다. 공격자가 오늘 암호화된 트래픽을 대량으로 저장해 두고, 양자 컴퓨터가 실용화되는 시점에 과거 데이터를 복호화할 수 있다. 비밀이 10년 이상 유지되어야 하는 데이터는 지금 당장 PQC로 보호해야 한다.

## NIST PQC 표준화 결과

NIST가 2024년 확정한 세 가지 표준은 각각 역할이 다르다.

| 표준 이름 | 원래 이름 | 역할 | 기반 수학 |
| --- | --- | --- | --- |
| ML-KEM (FIPS 203) | CRYSTALS-Kyber | 키 캡슐화(KEM) | 모듈 격자 (Module-LWE) |
| ML-DSA (FIPS 204) | CRYSTALS-Dilithium | 전자서명 | 모듈 격자 |
| SLH-DSA (FIPS 205) | SPHINCS+ | 전자서명 | 해시 함수 |

ML-KEM은 키 교환과 암호화에, ML-DSA와 SLH-DSA는 전자서명에 쓰인다. 이 글은 ML-KEM에 집중한다.

## 격자 암호의 직관적 이해

ML-KEM의 안전성은 **LWE(Learning With Errors)** 문제에 기반한다. 직관적으로 설명하면 이렇다.

정확한 선형 방정식 시스템은 풀기 쉽다.

```text
3x + 5y = 23
7x + 2y = 32
→ x, y를 쉽게 구할 수 있다.
```

여기에 **작은 무작위 오차**를 더하면 풀기가 급격히 어려워진다.

```text
3x + 5y + 오차₁ ≈ 23
7x + 2y + 오차₂ ≈ 32
→ 오차의 범위만 알고 x, y는 모른다면 답을 찾기 매우 어렵다.
```

오차가 있는 상태에서 원래 비밀(x, y)을 복구하는 것이 LWE 문제다. 이 문제는 고전 컴퓨터와 양자 컴퓨터 모두 효율적으로 풀기 어렵다는 것이 현재까지의 분석 결과다.

**Module-LWE**는 LWE를 다항식 환(ring) 위에서 행렬로 확장한 변형이다. 보안성을 유지하면서 키 크기와 연산 속도를 현실적인 수준으로 줄였다.

## KEM 구조: 키 캡슐화란

ML-KEM은 **KEM(Key Encapsulation Mechanism)** 방식을 쓴다. RSA나 ECDH가 키를 직접 교환하는 것과 달리, KEM은 공유 비밀을 "캡슐에 담아" 전달한다.

```text
[수신자]
1. 공개 키(pk)와 개인 키(sk)를 생성한다.
2. pk를 송신자에게 보낸다.

[송신자]
3. pk를 사용해 캡슐화(Encapsulate)를 실행한다.
   → 공유 비밀 K와 암호문 c를 얻는다.
4. c를 수신자에게 보낸다.

[수신자]
5. sk와 c로 역캡슐화(Decapsulate)를 실행한다.
   → 같은 공유 비밀 K를 얻는다.

양쪽이 K를 가지게 됨 → K로 AES-GCM 같은 대칭 암호의 세션 키로 사용
```

송신자는 공유 비밀 K를 직접 선택하지 않는다. 캡슐화 과정에서 무작위로 생성되고, 수신자의 공개 키로 보호된 형태로 전달된다.

## ML-KEM 내부 동작

정확한 수학식보다는 각 단계가 무엇을 하는지 흐름 위주로 살펴본다.

### 키 생성 (KeyGen)

```text
1. 무작위 행렬 A를 생성한다. (공개 파라미터에서 결정론적으로 생성)
2. 비밀 벡터 s와 오차 벡터 e를 작은 범위에서 무작위로 뽑는다.
3. t = A·s + e 를 계산한다.
4. 공개 키 pk = (A, t), 개인 키 sk = s
```

A와 t는 공개해도 된다. s는 오차 e에 숨겨져 있어 t에서 역산하기 어렵다.

### 캡슐화 (Encapsulate)

```text
1. 무작위 메시지 m (32바이트)을 생성한다.
2. 추가 오차 벡터 r, e₁, e₂를 무작위로 뽑는다.
3. u = Aᵀ·r + e₁
4. v = tᵀ·r + e₂ + ⌊q/2⌋·m
5. 암호문 c = (u, v), 공유 비밀 K = H(m) (해시)
```

m이 v 안에 숨어 들어간다. 개인 키 s 없이는 꺼내기 어렵다.

### 역캡슐화 (Decapsulate)

```text
1. v - uᵀ·s 를 계산한다.
2. 오차가 작으므로 결과가 ⌊q/2⌋·m에 가까워진다.
3. 반올림으로 m을 복구한다.
4. 공유 비밀 K = H(m)
```

오차가 계산 중에 상쇄되는 구조다. 오차의 범위가 충분히 작으면 반올림이 항상 올바른 m을 복구한다.

{: .note }
실제 ML-KEM은 이 과정을 다항식 환 위에서 수행하고, NTT(Number Theoretic Transform)로 행렬 곱셈을 가속한다. 위의 설명은 직관을 위해 행렬 형태로 단순화한 것이다.

## RSA·ECDH와의 비교

| 항목 | RSA-2048 | ECDH-P256 | ML-KEM-768 |
| --- | --- | --- | --- |
| 보안 수준 | 112비트 | 128비트 | 128비트 |
| 공개 키 크기 | 256바이트 | 64바이트 | **1,184바이트** |
| 암호문 크기 | 256바이트 | 64바이트 | **1,088바이트** |
| 개인 키 크기 | 1,218바이트 | 32바이트 | **2,400바이트** |
| 양자 내성 | ❌ | ❌ | ✅ |
| 기반 가정 | 소인수분해 | 이산 로그 | Module-LWE |

키와 암호문이 RSA·ECDH에 비해 훨씬 크다. TLS 핸드셰이크 같은 곳에서 패킷 크기 증가로 이어진다. 이 오버헤드를 감수하더라도 양자 위협을 차단하는 것이 PQC 도입의 판단 기준이다.

ML-KEM-768은 보안 파라미터다. NIST는 128비트(ML-KEM-512), 192비트(ML-KEM-768), 256비트(ML-KEM-1024) 세 가지를 정의했다.

## 하이브리드 방식

기존 시스템과의 호환성 때문에 당분간은 ECDH와 ML-KEM을 함께 사용하는 **하이브리드 KEM**이 권장된다.

```text
공유 비밀 = KDF(ECDH 공유 비밀 || ML-KEM 공유 비밀)
```

두 공유 비밀을 KDF(Key Derivation Function)로 혼합한다. ECDH가 뚫리더라도 ML-KEM이 안전하면 보호되고, 반대도 마찬가지다.

TLS 1.3에서 이미 하이브리드 키 교환이 실험적으로 도입되고 있다. X25519MLKEM768은 X25519(ECDH)와 ML-KEM-768을 결합한 방식으로, Chrome 등 주요 브라우저가 지원을 추가하고 있다.

## Apple 플랫폼에서의 PQC

Apple은 2024년 iOS 17.4와 macOS 14.4부터 iMessage에 **PQ3 프로토콜**을 도입했다. ML-KEM 기반의 키 교환을 사용해 Harvest Now, Decrypt Later 공격에 대응한다.

또한 Apple CryptoKit에서 ML-KEM 지원이 추가됐다.

```swift
import CryptoKit

// 키 생성
let privateKey = try MLKEMPrivateKey(parameters: .MLKEM768)
let publicKey = privateKey.publicKey

// 캡슐화 (송신자)
let (sharedSecret, ciphertext) = try publicKey.encapsulate()

// 역캡슐화 (수신자)
let recoveredSecret = try privateKey.decapsulate(ciphertext: ciphertext)
```

{: .note }
API는 버전에 따라 다를 수 있다. 실제 사용 전 Apple 공식 문서와 플랫폼 가용성을 확인한다.

## 구현 시 주의할 점

**직접 구현하지 않는다.**  
격자 암호는 오차 샘플링, 반올림, NTT 연산 등 구현 오류가 보안 취약점으로 이어지기 쉽다. Apple CryptoKit, OpenSSL 3.x, BoringSSL 같은 검증된 라이브러리를 사용한다.

**키 크기 증가를 미리 반영한다.**  
TLS 핸드셰이크 버퍼, 인증서 저장 필드, 네트워크 패킷 크기를 ML-KEM의 큰 키에 맞게 조정해야 한다. 특히 UDP 기반 프로토콜은 단편화 문제가 생길 수 있다.

**전자서명은 별도로 교체한다.**  
ML-KEM은 키 교환·암호화만 담당한다. RSA나 ECDSA 기반 전자서명은 ML-DSA나 SLH-DSA로 별도 전환해야 한다.

**하이브리드로 시작한다.**  
ML-KEM만 단독으로 쓰기보다, 기존 ECDH와 하이브리드 구성으로 시작하면 PQC 구현 오류가 있더라도 ECDH가 보호막 역할을 한다.

## 정리

ML-KEM은 LWE 문제의 어려움을 근거로 키 교환을 수행하는 양자 내성 알고리즘이다. RSA·ECDH를 쇼어 알고리즘으로 풀 수 있는 양자 컴퓨터가 등장하더라도 안전하도록 설계됐다. 키와 암호문 크기가 커지는 트레이드오프가 있지만, 오늘 전송된 데이터가 미래에 복호화될 위험을 차단하려면 지금 도입을 준비해야 한다.

## 참고

- [NIST FIPS 203: ML-KEM](https://csrc.nist.gov/pubs/fips/203/final)
- [NIST Post-Quantum Cryptography Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [Apple Security Research: iMessage PQ3](https://security.apple.com/blog/imessage-pq3/)
- [Apple CryptoKit ML-KEM](https://developer.apple.com/documentation/cryptokit/mlkem)
- [Cloudflare Blog: Post-Quantum Cryptography](https://blog.cloudflare.com/post-quantum-cryptography-ga/)
