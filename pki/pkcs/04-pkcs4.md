---
title: "PKCS #4: 폐기된 RSA 키 문법"
description: "폐기된 PKCS #4 RSA 키 문법과 PKCS #1·PKCS #8·PEM 키 파일 형식의 차이를 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 4
permalink: /pki/pkcs/pkcs4/
last_modified_date: 2026-11-16
tags: [PKI, PKCS4, RSA, ASN1]
---

# PKCS #4: 폐기된 RSA 키 문법

PKCS #4는 RSA 키의 표현 문법을 별도로 정의하던 초기 규격이다. 이후 **PKCS #1에 흡수돼 폐기**됐다.

## RSA 공개 키의 핵심 값

```asn1
RSAPublicKey ::= SEQUENCE {
    modulus         INTEGER, -- n
    publicExponent  INTEGER  -- e
}
```

- `n`: 두 큰 소수의 곱으로 만든 모듈러스
- `e`: 공개 지수

## RSA 개인 키의 핵심 값

PKCS #1의 `RSAPrivateKey`에는 `n`, `e`, `d`뿐 아니라 `p`, `q`, `dP`, `dQ`, `qInv` 같은 CRT 계산용 값도 포함된다. 이 값은 개인 키 연산을 빠르게 하지만 모두 민감한 개인 키 재료다.

## 비슷해 보이는 키 파일 구분

```text
-----BEGIN RSA PRIVATE KEY-----
```

보통 PKCS #1의 RSA 전용 개인 키 구조를 PEM으로 감싼 것이다.

```text
-----BEGIN PRIVATE KEY-----
```

보통 PKCS #8 `PrivateKeyInfo` 또는 `OneAsymmetricKey` 구조다. RSA뿐 아니라 여러 알고리즘을 담을 수 있다.

```text
-----BEGIN PUBLIC KEY-----
```

대개 X.509의 `SubjectPublicKeyInfo` 구조로, 알고리즘 식별자와 공개 키를 함께 담는다.

PEM은 Base64와 머리글로 감싼 표현이고, 안쪽의 실제 ASN.1 구조가 PKCS #1인지 PKCS #8인지 별도로 확인해야 한다.

## 현재 무엇을 사용해야 할까

- RSA 키 구조 자체: PKCS #1, RFC 8017
- 알고리즘 독립적인 개인 키 컨테이너: PKCS #8, RFC 5208 또는 RFC 5958
- 인증서 안의 공개 키: X.509 `SubjectPublicKeyInfo`
- 키와 인증서를 함께 이동: PKCS #12, RFC 7292

## 보안 주의사항

- 개인 키 DER/PEM을 로그에 출력하지 않는다.
- 암호화되지 않은 개인 키 파일의 접근 권한을 제한한다.
- 가능하면 HSM이나 Keychain처럼 키가 밖으로 나오지 않는 저장소를 사용한다.
- 포맷 변환 뒤 알고리즘, 키 크기, 공개 키 일치 여부를 검증한다.

## 관련 RFC

- [RFC 8017: PKCS #1 v2.2](https://www.rfc-editor.org/rfc/rfc8017.html)
- [RFC 5958: Asymmetric Key Packages](https://www.rfc-editor.org/rfc/rfc5958.html)
