---
title: "PKCS #8: 알고리즘 독립적인 개인 키 컨테이너"
description: "PKCS #8 개인 키 컨테이너, RFC 5208과 RFC 5958, 암호화된 PRIVATE KEY PEM 형식을 설명합니다."
parent: "PKI & 암호"
nav_order: 8
permalink: /pki/pkcs8/
redirect_from:
  - /pki/pkcs/pkcs8/
date: 2026-11-17
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
last_modified_date: 2026-11-17
tags: [PKI, PKCS8, Private-Key, RFC5958]
---

# PKCS #8: 알고리즘 독립적인 개인 키 컨테이너
{: .no_toc }

{% include article-toc.md %}

PKCS #8은 RSA, EC(타원곡선) 같은 특정 알고리즘에 종속되지 않고 개인 키와 알고리즘 정보를 담는 문법이다. RFC 5208이 PKCS #8 v1.2를 담았고, **RFC 5958이 이를 폐기하고 후속 Asymmetric Key Packages를 정의**했다.

## 키를 담는 상자의 역할

RSA와 EC는 키의 내부 모양이 다르다. 공통 컨테이너가 알고리즘 이름을 함께 담으면 프로그램은 그 정보를 보고 안쪽 키를 올바른 방식으로 해석할 수 있다.

컨테이너에 넣었다고 개인 키가 자동으로 암호화되는 것은 아니다. 파일 머리글과 암호화 알고리즘 정보를 보고 보호 여부를 확인한다. Base64 문자는 사람이 읽기 쉽게 표현한 것이며 비밀을 숨기는 기능은 없다.

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

택배 상자를 생각하면 바깥의 `privateKeyAlgorithm`은 내용물 종류를 적은 표지이고, 안쪽 `privateKey`는 실제 내용물이다. 바깥 상자가 같아도 RSA와 EC의 안쪽 구조는 다르다. 파서는 알고리즘 식별자를 읽은 뒤 해당 규격에 맞게 내부를 해석한다.

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

## 컨테이너와 키 알고리즘을 구분하는 실전 질문

‘PKCS #8 키로 서명한다’는 표현만으로는 서명 방식을 알 수 없다. PKCS #8은 키를 담는 구조다. 안쪽이 RSA라면 PSS나 v1.5 같은 서명 방식과 파라미터가 더 필요하고, EC라면 그 키와 사용 프로토콜에 맞는 알고리즘이 필요하다.

파일을 읽은 다음에는 컨테이너 파싱 성공, 키 알고리즘 식별, 허용 파라미터 검사, 필요한 연산 수행 가능 여부를 차례로 확인한다. 읽는 데 성공했어도 서비스가 허용하지 않는 키일 수 있다.

## 암호화된 바깥 구조를 여는 순서

```text
EncryptedPrivateKeyInfo
  ├─ encryptionAlgorithm: 어떻게 보호했는가
  └─ encryptedData: 보호된 개인 키 정보
        ↓ 패스워드 기반 복호화
      PrivateKeyInfo 계열 구조
        ↓ 알고리즘 식별
      RSA·EC 등 실제 개인 키
```

패스워드 오류, 지원하지 않는 보호 알고리즘, 안쪽 키 문법 오류는 개발자가 원인을 구분할 필요가 있다. 다만 상세 키 재료나 비밀을 로그에 남기지는 않는다. 호환성 분석에서는 개인 키 원문 대신 알고리즘과 비민감 파라미터, 라이브러리 버전을 기록한다.

[RFC 5958 §2](https://www.rfc-editor.org/rfc/rfc5958.html#section-2)는 비대칭 키 패키지 구조를 정의한다. 선택 공개 키 필드가 있는 버전과 기존 형식의 차이를 확인하고, 가져오는 제품이 어느 형식을 지원하는지 별도로 시험한다.

## 관련 RFC

- [RFC 5208: PKCS #8](https://www.rfc-editor.org/rfc/rfc5208.html)
- [RFC 5958: Asymmetric Key Packages](https://www.rfc-editor.org/rfc/rfc5958.html)
- [RFC 8351: PKCS #8 EncryptedPrivateKeyInfo Media Type](https://www.rfc-editor.org/rfc/rfc8351.html)
