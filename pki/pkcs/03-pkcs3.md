---
title: "PKCS #3: Diffie-Hellman 키 합의"
description: "PKCS #3 Diffie-Hellman 키 합의 원리, 중간자 공격, KDF와 현재 권장되는 후속 RFC를 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 3
permalink: /pki/pkcs/pkcs3/
last_modified_date: 2026-11-16
tags: [PKI, PKCS3, Diffie-Hellman]
---

# PKCS #3: Diffie-Hellman 키 합의

PKCS #3는 유한체 Diffie-Hellman 키 합의의 초기 규격이다. 두 당사자가 공개 통신망에서 값을 교환해 같은 공유 비밀을 계산하는 방법을 다룬다.

## 암호화가 아니라 키 합의다

Alice와 Bob이 공개 파라미터 `p`, `g`를 공유한다고 하자.

```text
Alice: 비밀 a, 공개값 A = g^a mod p
Bob:   비밀 b, 공개값 B = g^b mod p

Alice가 계산: B^a mod p
Bob이 계산:   A^b mod p
결과: g^(ab) mod p
```

도청자는 `p`, `g`, `A`, `B`를 보지만 충분히 큰 안전한 그룹에서는 공유 비밀을 계산하기 어렵다.

## 인증이 없으면 중간자 공격을 막지 못한다

기본 Diffie-Hellman은 상대가 누구인지 증명하지 않는다. 공격자가 Alice와 Bob 사이에서 각각 별도 키 합의를 하면 둘은 공격자와 키를 공유하면서 서로와 직접 연결됐다고 착각할 수 있다.

따라서 실제 프로토콜은 인증서 서명, 사전 공유 키, 인증된 키 교환 같은 방식으로 교환 내용을 인증해야 한다.

## 공유 비밀을 바로 암호 키로 쓰지 않는다

DH 결과는 정해진 KDF에 넣어 암호화 키, 인증 키, nonce 관련 값을 분리해 만든다. 원시 공유 비밀을 그대로 AES 키로 자르는 방식은 프로토콜 규격과 보안 증명을 깨뜨릴 수 있다.

## 현재 어떻게 이해해야 할까

PKCS #3 자체는 역사적 규격이다. 새 프로토콜에서는 직접 `p`와 `g`를 임의 선택하지 않고, 최신 프로토콜이 정한 검증된 그룹과 키 파생 절차를 사용한다.

- TLS의 유한체 일회성 DH 그룹: RFC 7919
- X25519와 X448: RFC 7748
- CMS에서의 DH 키 합의: RFC 2631 및 후속 알고리즘 규격

일회성 키를 사용하는 DHE/ECDHE는 장기 개인 키가 나중에 유출돼도 과거 세션 키가 바로 복구되지 않는 순방향 비밀성을 제공할 수 있다.

## 구현 원칙

- 그룹 파라미터와 상대 공개 키를 검증한다.
- 개인 지수를 안전한 난수로 만든다.
- 공유 비밀을 승인된 KDF에 넣는다.
- 키 합의와 상대 인증을 별개로 확인한다.
- 프로토콜 라이브러리의 고수준 API를 사용한다.

## 관련 RFC

- [RFC 2631: Diffie-Hellman Key Agreement Method](https://www.rfc-editor.org/rfc/rfc2631.html)
- [RFC 7919: Negotiated Finite Field Diffie-Hellman Ephemeral Parameters for TLS](https://www.rfc-editor.org/rfc/rfc7919.html)
- [RFC 7748: Elliptic Curves for Security](https://www.rfc-editor.org/rfc/rfc7748.html)
