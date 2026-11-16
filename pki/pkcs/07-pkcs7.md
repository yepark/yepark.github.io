---
title: "PKCS #7: 서명·암호 메시지와 CMS"
description: "PKCS #7과 CMS RFC 5652의 SignedData, EnvelopedData, attached·detached 서명 구조를 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 7
permalink: /pki/pkcs/pkcs7/
last_modified_date: 2026-11-16
tags: [PKI, PKCS7, CMS, RFC5652]
---

# PKCS #7: 서명·암호 메시지와 CMS

PKCS #7은 데이터를 서명하거나 암호화해 교환하는 문법을 정의했다. RFC 2315가 PKCS #7 v1.5를 담고 있으며, 이후 **CMS(Cryptographic Message Syntax), RFC 5652**로 발전했다.

## ContentInfo라는 바깥 상자

CMS는 내용 종류를 OID로 표시하고 실제 데이터를 함께 넣는다.

```asn1
ContentInfo ::= SEQUENCE {
    contentType ContentType,
    content     [0] EXPLICIT ANY DEFINED BY contentType
}
```

`contentType`에 따라 안쪽 구조를 다르게 해석한다.

| 내용 종류 | 목적 |
| --- | --- |
| `data` | 일반 바이트 데이터 |
| `signedData` | 전자서명과 인증서 포함 |
| `envelopedData` | 수신자별 암호화 키와 암호문 포함 |
| `digestedData` | 메시지 다이제스트 포함 |
| `encryptedData` | 대칭 키 암호문 포함, 수신자 키 정보 없음 |
| `authenticatedData` | MAC으로 무결성과 인증 제공 |

## SignedData 흐름

1. 서명할 콘텐츠의 해시를 계산한다.
2. 콘텐츠 타입, 메시지 다이제스트, 서명 시각 같은 signed attributes를 구성할 수 있다.
3. 서명자는 개인 키로 서명한다.
4. 결과에 서명자 인증서와 알고리즘 식별자를 함께 넣을 수 있다.
5. 수신자는 콘텐츠, 속성, 서명, 인증서 체인을 검증한다.

서명 값이 맞아도 인증서가 신뢰되지 않거나 용도·유효 기간·폐지 검증에 실패하면 서명자를 신뢰할 수 없다.

## EnvelopedData 흐름

1. 콘텐츠 암호화용 무작위 대칭 키를 만든다.
2. 콘텐츠는 대칭 암호로 한 번 암호화한다.
3. 각 수신자에게 맞는 키 전송 또는 키 합의 방식으로 대칭 키를 보호한다.
4. 수신자 정보와 암호문을 묶는다.

수신자가 여러 명이어도 큰 콘텐츠를 여러 번 암호화하지 않고, 콘텐츠 키만 수신자별로 감싼다.

## attached와 detached 서명

- attached: 서명 구조 안에 원문이 함께 있음
- detached: 서명 구조에는 서명 정보만 있고 원문은 별도 전달

detached 서명은 검증할 때 정확히 같은 바이트 원문이 필요하다. 텍스트 개행이나 JSON 키 순서가 바뀌어도 서명이 실패할 수 있다.

## PKCS #7 패딩과 PKCS #7 메시지는 다르다

`PKCS7Padding`이라는 이름은 블록 암호의 바이트 채움 규칙을 가리키는 경우가 많다. PKCS #7/CMS 메시지 컨테이너 전체와 패딩은 같은 개념이 아니다. 자세한 패딩 규칙은 [블록 암호의 패딩 이해하기]({{ '/pki/padding/' | relative_url }})에서 설명한다.

## 현재 구현 원칙

- 새 구현은 PKCS #7 v1.5보다 CMS RFC 5652와 사용하는 프로파일을 확인한다.
- 알고리즘 OID뿐 아니라 파라미터를 검증한다.
- signed attributes가 있으면 규격의 DER 인코딩 대상을 정확히 서명·검증한다.
- 암호문 인증이 필요한 경우 프로토콜이 정한 인증 방식과 순서를 따른다.
- S/MIME, 펌웨어 서명 등 상위 프로토콜의 추가 규칙을 함께 확인한다.

## 관련 RFC

- [RFC 2315: PKCS #7 v1.5](https://www.rfc-editor.org/rfc/rfc2315.html)
- [RFC 5652: Cryptographic Message Syntax](https://www.rfc-editor.org/rfc/rfc5652.html)
