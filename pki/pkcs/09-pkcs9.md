---
title: "PKCS #9: 인증서·CMS·PKCS #12의 속성"
description: "RFC 2985의 contentType, messageDigest, extensionRequest, friendlyName 등 PKCS #9 속성을 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 9
permalink: /pki/pkcs/pkcs9/
last_modified_date: 2026-11-17
tags: [PKI, PKCS9, Attributes, RFC2985]
---

# PKCS #9: 인증서·CMS·PKCS #12의 속성
{: .no_toc }

{% include article-toc.md %}

## 속성 이름 대신 번호를 사용하는 이유

서로 다른 프로그램이 ‘서명 시각’이나 ‘콘텐츠 해시’라는 항목을 같은 의미로 읽으려면 공통 식별자가 필요하다. OID는 이런 항목을 구분하는 숫자 경로다.

`Attribute`는 속성 종류와 그 값의 묶음이다. 화면용 별칭, 서명으로 보호된 속성, 발급을 희망하는 확장 요청은 신뢰 수준이 다르다. 값이 들어 있다는 이유만으로 권한이나 신원이 확인됐다고 판단하지 않는다.

PKCS #9은 다른 PKCS 규격에서 공통으로 사용하는 속성 타입과 OID를 정의한다. 현재 핵심 문서는 **RFC 2985**다.

## 속성의 기본 모양

```asn1
Attribute ::= SEQUENCE {
    type    OBJECT IDENTIFIER,
    values  SET OF AttributeValue
}
```

`type` OID가 값의 의미와 ASN.1 타입을 결정한다. 같은 OID라도 임의의 문자열로 해석해서는 안 된다.

## 자주 만나는 속성

| 속성 | OID 끝 번호 | 주로 쓰이는 곳 |
| --- | --- | --- |
| `emailAddress` | `.1` | 이름·인증서 관련 레거시 속성 |
| `contentType` | `.3` | CMS signed attributes |
| `messageDigest` | `.4` | CMS에서 콘텐츠 해시 연결 |
| `signingTime` | `.5` | 서명자가 주장하는 서명 시각 |
| `extensionRequest` | `.14` | PKCS #10 CSR에서 요청할 X.509 확장 |
| `friendlyName` | `.20` | PKCS #12 항목의 표시 이름 |
| `localKeyId` | `.21` | PKCS #12의 키와 인증서 연결 보조 |

전체 OID의 공통 뿌리는 `1.2.840.113549.1.9`다.

## CMS의 signed attributes

CMS에서 signed attributes가 존재하면 메시지 다이제스트와 콘텐츠 타입 등을 속성 집합에 넣고, 규격이 정한 DER 인코딩을 서명한다. 속성의 정렬이나 태그 처리를 임의로 바꾸면 검증이 실패한다.

`signingTime`은 서명자가 넣은 주장일 뿐 신뢰할 수 있는 시각 증명이 아니다. 신뢰할 수 있는 시각이 필요하면 서명된 타임스탬프 프로토콜과 검증 정책이 필요하다.

## CSR의 extensionRequest

CSR은 `extensionRequest` 속성 안에 Subject Alternative Name, Key Usage 같은 희망 확장을 담을 수 있다. 하지만 CA가 요청을 그대로 발급해야 한다는 뜻은 아니다. CA는 인증 정책에 따라 무시, 변경, 거절할 수 있다.

## PKCS #12의 friendlyName과 localKeyId

- `friendlyName`: 사람이 볼 별칭
- `localKeyId`: 같은 묶음 안에서 개인 키와 해당 인증서를 연결하는 데 사용하는 식별값

둘 다 암호학적으로 소유권을 증명하는 값은 아니다. 키와 인증서가 실제 짝인지 공개 키를 비교해 검증해야 한다.

## 구현 원칙

- OID별 정확한 값 타입과 개수 제한을 검증한다.
- 알 수 없는 속성을 무조건 문자열로 출력하지 않는다.
- 서명 대상 속성은 규격의 인코딩 규칙을 따른다.
- 표시용 속성을 신뢰·권한 판단에 사용하지 않는다.
- 중복 속성 처리 규칙을 상위 프로토콜과 함께 확인한다.

## 관련 RFC

- [RFC 2985: PKCS #9 Selected Object Classes and Attribute Types](https://www.rfc-editor.org/rfc/rfc2985.html)
