---
title: "PKCS #4: 폐기된 RSA 키 문법"
description: "폐기된 PKCS #4 RSA 키 문법과 PKCS #1·PKCS #8·PEM 키 파일 형식의 차이를 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 4
permalink: /pki/pkcs/pkcs4/
date: 2026-11-17
last_modified_at: 2026-11-20
seo:
  type: BlogPosting
last_modified_date: 2026-11-20
tags: [PKI, PKCS4, RSA, ASN1]
---

# PKCS #4: 폐기된 RSA 키 문법
{: .no_toc }

{% include article-toc.md %}

PKCS #4는 RSA 키의 표현 문법을 별도로 정의하던 초기 규격이다. 이후 **PKCS #1에 흡수돼 폐기**됐다.

## 키 값과 파일 포맷 구분하기

RSA 키는 여러 큰 정수로 구성된다. 이 값들을 파일에 넣어 다른 프로그램이 읽으려면 필드 순서와 타입을 정한 문법이 필요하다.

ASN.1은 구조를 설명하는 언어이고 DER은 그 구조를 바이트로 바꾸는 규칙이다. PEM은 그 바이트를 텍스트로 옮기는 바깥 표현이다. 같은 `.pem` 파일도 안쪽 구조가 다를 수 있으므로 머리글과 실제 파싱 결과를 함께 확인한다.

## RSA 공개 키의 핵심 값

```asn1
RSAPublicKey ::= SEQUENCE {
    modulus         INTEGER, -- n
    publicExponent  INTEGER  -- e
}
```

- `n`: 보통 두 큰 소수의 곱으로 만든 모듈러스. RFC 8017은 여러 소수를 쓰는 multi-prime RSA도 정의한다.
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

## 파일을 읽는 순서를 한 단계씩 나누기

`BEGIN PRIVATE KEY`로 시작하는 RSA 키 파일을 받았다고 하자. 먼저 PEM의 Base64를 해석하면 바이트가 나온다. 그 바이트를 DER 규칙으로 읽어 PKCS #8 바깥 구조를 얻고, 알고리즘 식별자가 RSA인지 확인한 뒤 안쪽 개인 키를 PKCS #1 문법으로 읽는다.

```text
PEM 텍스트
  → Base64 해제
  → PKCS #8 바깥 구조
  → RSA 알고리즘 식별
  → PKCS #1 RSA 개인 키 필드
```

확장자를 바꾸거나 머리글의 `RSA` 단어만 지워서는 이 변환이 일어나지 않는다. 구조 자체를 다시 인코딩해야 한다. 외형이 비슷한 텍스트라도 프로그램이 기대하는 안쪽 구조가 다르면 가져오기에 실패하는 이유다.

## 현재 규격에서 확인할 위치

RSA 키의 ASN.1 문법은 [RFC 8017 부록 A.1](https://www.rfc-editor.org/rfc/rfc8017.html#appendix-A.1)에서 확인한다. 키를 담는 바깥 컨테이너는 [PKCS #8]({{ '/pki/pkcs/pkcs8/' | relative_url }})의 책임이다. 폐기된 PKCS #4라는 이름과 현재 파일이 실제로 사용하는 구조를 분리해서 기록하면 오래된 시스템을 분석할 때 혼동을 줄일 수 있다.

PKCS #4 자체의 새로운 RFC를 뜻하는 목록이 아니다. 아래는 현재 RSA 키 구조와 컨테이너를 확인할 문서다.

## 관련 RFC

- [RFC 8017: PKCS #1 v2.2](https://www.rfc-editor.org/rfc/rfc8017.html)
- [RFC 5958: Asymmetric Key Packages](https://www.rfc-editor.org/rfc/rfc5958.html)
