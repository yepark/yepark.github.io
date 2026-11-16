---
title: "PKCS #8: 알고리즘 독립적인 개인 키 컨테이너"
description: "PKCS #8 개인 키 컨테이너, RFC 5208과 RFC 5958, 암호화된 PRIVATE KEY PEM 형식을 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 8
permalink: /pki/pkcs/pkcs8/
last_modified_date: 2026-11-16
tags: [PKI, PKCS8, Private-Key, RFC5958]
---

# PKCS #8: 알고리즘 독립적인 개인 키 컨테이너

PKCS #8은 RSA, EC 같은 특정 알고리즘에 종속되지 않고 개인 키와 알고리즘 정보를 담는 문법이다. RFC 5208이 PKCS #8 v1.2를 담았고, **RFC 5958이 이를 폐기하고 후속 Asymmetric Key Packages를 정의**했다.

## PrivateKeyInfo 구조

```asn1
PrivateKeyInfo ::= SEQUENCE {
    version                   Version,
    privateKeyAlgorithm       AlgorithmIdentifier,
    privateKey                OCTET STRING,
    attributes           [0]  IMPLICIT Attributes OPTIONAL
}
```

- `privateKeyAlgorithm`: 안쪽 키가 RSA인지 EC인지와 파라미터
- `privateKey`: 알고리즘별 개인 키 구조를 바이트로 넣은 값
- `attributes`: 선택 속성

PKCS #8이 키 알고리즘 자체를 다시 정의하는 것은 아니다. RSA라면 `privateKey` 안에 PKCS #1의 RSA 개인 키 구조가 들어갈 수 있다.

## RFC 5958의 OneAsymmetricKey

후속 규격은 `PrivateKeyInfo`를 `OneAsymmetricKey`로 확장하고 선택적인 공개 키 필드를 추가했다. 하나 이상의 키를 CMS 콘텐츠 타입으로 포장하는 방법도 정의한다.

## 암호화되지 않은 키와 암호화된 키

```text
-----BEGIN PRIVATE KEY-----
```

대개 암호화되지 않은 PKCS #8 구조다. PEM 자체는 암호 보호가 아니다.

```text
-----BEGIN ENCRYPTED PRIVATE KEY-----
```

`EncryptedPrivateKeyInfo` 구조로, 암호화 알고리즘과 암호문을 담는다. 보통 PKCS #5의 PBES2/PBKDF2 같은 패스워드 기반 보호 방식과 연결된다.

## PKCS #1과 차이

| 포맷 | 특징 |
| --- | --- |
| PKCS #1 RSA 키 | RSA 전용 키 필드 |
| PKCS #8 | 알고리즘 식별자 + 알고리즘별 개인 키를 담는 공통 상자 |
| PKCS #12 | 개인 키뿐 아니라 인증서 체인과 속성도 함께 이동 |

## 보안 원칙

- 암호화되지 않은 개인 키 파일은 비밀 데이터로 취급한다.
- 패스워드 기반 암호화의 salt, 반복 횟수, 알고리즘을 현대 정책에 맞춘다.
- 파일 권한만으로 충분하다고 가정하지 않는다.
- 가능하면 내보낼 수 없는 하드웨어 키를 사용한다.
- 포맷 변환 후 공개 키와 인증서가 실제로 짝인지 확인한다.
- 오류 로그에 키 원문이나 패스워드를 남기지 않는다.

## 관련 RFC

- [RFC 5208: PKCS #8](https://www.rfc-editor.org/rfc/rfc5208.html)
- [RFC 5958: Asymmetric Key Packages](https://www.rfc-editor.org/rfc/rfc5958.html)
- [RFC 8351: PKCS #8 EncryptedPrivateKeyInfo Media Type](https://www.rfc-editor.org/rfc/rfc8351.html)
