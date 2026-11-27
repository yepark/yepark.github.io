---
title: "PKCS #3: Diffie-Hellman 키 합의"
description: "PKCS #3 Diffie-Hellman 키 합의 원리, 중간자 공격, KDF와 관련 프로토콜 RFC를 설명합니다."
parent: "PKI & 암호"
nav_order: 3
permalink: /pki/pkcs3/
redirect_from:
  - /pki/pkcs/pkcs3/
date: 2026-11-17
last_modified_at: 2026-11-20
seo:
  type: BlogPosting
last_modified_date: 2026-11-20
tags: [PKI, PKCS3, Diffie-Hellman]
---

# PKCS #3: Diffie-Hellman 키 합의
{: .no_toc }

{% include article-toc.md %}

PKCS #3는 Diffie-Hellman(DH) 키 합의의 초기 규격이다. 여기서 DH는 큰 소수 `p`로 나눈 나머지 세계(유한체)에서 계산하는 원래 방식을 말한다. 두 당사자가 공개 통신망에서 값을 교환해 같은 공유 비밀을 계산하는 방법을 다룬다.

## 비밀 키를 그대로 보내지 않는 방법

두 사람이 통신을 암호화하려면 같은 대칭 키가 필요할 수 있다. 그 키를 평문으로 보내지 않고 각자의 비밀값과 상대의 공개값으로 같은 공유 비밀을 계산하는 것이 키 합의다.

아래의 `mod`는 나눗셈의 나머지 연산이다. 수식의 문자를 외우기보다 어떤 값이 공개되고 어떤 값은 끝까지 비밀인지 구분해 보자. 상대의 신원을 확인하는 절차가 없으면 키 합의만 성공해도 안전한 상대와 통신했다고 보장할 수 없다.

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

작은 숫자로 계산 원리만 확인해 보자. `p=23`, `g=5`, Alice의 비밀값 `a=6`, Bob의 비밀값 `b=15`라면 공개값은 각각 8과 19다. Alice는 `19^6 mod 23`, Bob은 `8^15 mod 23`을 계산하고 둘 다 2를 얻는다.

이 숫자는 학습용이며 실제 암호 통신에 사용할 수 없다. 중요한 것은 공개값을 교환해도 각자의 비밀 지수는 보내지 않았다는 점이다. 실제 구현에서는 작은 숫자 대신 프로토콜이 정한 안전한 그룹과 키 검증을 사용한다.

## 인증이 없으면 중간자 공격을 막지 못한다

기본 Diffie-Hellman은 상대가 누구인지 증명하지 않는다. 공격자가 Alice와 Bob 사이에서 각각 별도 키 합의를 하면 둘은 공격자와 키를 공유하면서 서로와 직접 연결됐다고 착각할 수 있다.

따라서 실제 프로토콜은 인증서 서명, 사전 공유 키, 인증된 키 교환 같은 방식으로 교환 내용을 인증해야 한다.

## 공유 비밀을 바로 암호 키로 쓰지 않는다

DH 결과는 정해진 KDF(Key Derivation Function, 키 유도 함수)에 넣어 암호화 키, 인증 키, nonce(한 번만 쓰는 값) 관련 값을 따로 뽑아 만든다. 원시 공유 비밀을 그대로 AES 키로 자르는 방식은 프로토콜 규격과 보안 증명을 깨뜨릴 수 있다.

## 현재 어떻게 이해해야 할까

PKCS #3 자체는 역사적 규격이다. 새 프로토콜에서는 직접 `p`와 `g`를 임의 선택하지 않고, 최신 프로토콜이 정한 검증된 그룹과 키 파생 절차를 사용한다.

이 세 문서는 PKCS #3를 그대로 재발행한 최신판이 아니다. 수학적 키 합의, 그룹 선택, 키 표현과 파생 방식의 적용 문맥이 다르다.

- TLS의 유한체 일회성 DH 그룹: RFC 7919
- X25519와 X448: RFC 7748
- CMS에서의 DH 키 합의: RFC 2631 및 후속 알고리즘 규격

연결마다 새 키 쌍을 만들어 쓰는 DHE/ECDHE(E는 Ephemeral, 일회성)는 순방향 비밀성(forward secrecy)을 제공할 수 있다. 서버의 장기 개인 키가 나중에 유출돼도, 이미 끝난 과거 통신의 세션 키까지 바로 풀리지는 않는다는 뜻이다.

## 구현 원칙

- 그룹 파라미터와 상대 공개 키를 검증한다.
- 개인 지수를 안전한 난수로 만든다.
- 공유 비밀을 승인된 KDF에 넣는다.
- 키 합의와 상대 인증을 별개로 확인한다.
- 프로토콜 라이브러리의 고수준 API를 사용한다.

## 같은 값을 얻는 계산을 직접 확인하기

다음 코드는 키 합의의 수학적 관계만 확인한다. 작은 상수와 Python 정수 연산을 사용하므로 보안 구현으로 사용할 수 없다.

```python
p, g = 23, 5
alice_secret, bob_secret = 6, 15
alice_public = pow(g, alice_secret, p)
bob_public = pow(g, bob_secret, p)
alice_shared = pow(bob_public, alice_secret, p)
bob_shared = pow(alice_public, bob_secret, p)
assert (alice_public, bob_public) == (8, 19)
assert alice_shared == bob_shared == 2
```

`pow(g, a, p)`는 `g**a`를 p로 나눈 나머지다. 공개값 8과 19를 교환했을 뿐 비밀 지수 6과 15는 보내지 않았다. 이 예제에서는 도청자도 작은 후보를 전부 시험할 수 있다. 실제 보안은 같은 식이라는 사실만 아니라 그룹 크기와 구조, 비밀값 생성, 검증과 인증까지 충족해야 성립한다.

## RFC 2631은 PKCS #3의 다른 이름이 아니다

[RFC 2631 §2.1](https://www.rfc-editor.org/rfc/rfc2631.html#section-2.1)은 공유 비밀 계산과 키 재료 파생, 공개 키 검증을 구분한다. 기존 PKCS #3와 연관된 DH 계열이라는 이유로 파라미터 문법이나 KDF를 그대로 교환 가능하다고 가정하면 안 된다.

연동 문서에서 DH를 만나면 그룹 식별, 공개 키 표현, 상대 인증, 공유 비밀을 키로 바꾸는 규칙을 각각 찾는다. 수학적으로 같은 공유 비밀을 얻었어도 KDF의 문맥 입력이나 출력 길이가 다르면 최종 암호 키는 맞지 않는다.

## 관련 RFC: 직접 대체 관계와 구분하기

- [RFC 2631: Diffie-Hellman Key Agreement Method](https://www.rfc-editor.org/rfc/rfc2631.html)
- [RFC 7919: Negotiated Finite Field Diffie-Hellman Ephemeral Parameters for TLS](https://www.rfc-editor.org/rfc/rfc7919.html)
- [RFC 7748: Elliptic Curves for Security](https://www.rfc-editor.org/rfc/rfc7748.html)
