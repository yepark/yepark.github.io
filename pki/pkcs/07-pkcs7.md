---
title: "PKCS #7: 서명·암호 메시지와 CMS"
description: "PKCS #7과 CMS RFC 5652의 SignedData, EnvelopedData, attached·detached 서명 구조를 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 7
permalink: /pki/pkcs/pkcs7/
date: 2026-11-17
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
last_modified_date: 2026-11-17
tags: [PKI, PKCS7, CMS, RFC5652]
---

# PKCS #7: 서명·암호 메시지와 CMS
{: .no_toc }

{% include article-toc.md %}

PKCS #7은 데이터를 서명하거나 암호화해 교환하는 문법을 정의했다. RFC 2315가 PKCS #7 v1.5를 담고 있으며, 이후 **CMS(Cryptographic Message Syntax), RFC 5652**로 발전했다.

## 원문과 보호 정보를 한 상자에 담기

전자서명을 검증하려면 서명 값만 아니라 어떤 알고리즘과 공개 키로 검증할지도 알아야 한다. 암호문을 열려면 콘텐츠 키를 어떻게 보호했는지도 필요하다. CMS는 이런 정보를 전달할 구조를 정의한다.

`SignedData`와 `EnvelopedData`를 먼저 구분하자. 하나는 서명 정보를, 다른 하나는 수신자가 열 수 있도록 보호한 암호 메시지를 중심으로 담는다. 구조를 파싱하는 데 성공한 것과 서명·신뢰 검증에 성공한 것은 별개다.

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

`PKCS7Padding`이라는 이름은 블록 암호의 바이트 채움 규칙을 가리키는 경우가 많다. PKCS #7/CMS 메시지 컨테이너 전체와 패딩은 같은 개념이 아니다. 자세한 패딩 규칙은 [블록 암호의 패딩과 무결성]({{ '/pki/padding/' | relative_url }})에서 설명한다.

## 현재 구현 원칙

- 새 구현은 PKCS #7 v1.5보다 CMS RFC 5652와 사용하는 프로파일을 확인한다.
- 알고리즘 OID뿐 아니라 파라미터를 검증한다.
- signed attributes가 있으면 규격의 DER 인코딩 대상을 정확히 서명·검증한다.
- 암호문 인증이 필요한 경우 프로토콜이 정한 인증 방식과 순서를 따른다.
- S/MIME, 펌웨어 서명 등 상위 프로토콜의 추가 규칙을 함께 확인한다.

## 검증 실패를 세 층으로 나누기

CMS 파일 검증은 한 번의 참·거짓으로 끝내기보다 다음 경계를 나누어 이해하면 원인을 찾기 쉽다.

| 단계 | 확인할 내용 | 실패 사례 |
| --- | --- | --- |
| 구조 해석 | ContentInfo와 내부 필드가 올바른가 | 길이나 태그가 잘못된 입력 |
| 암호학적 검증 | 원문·속성·서명이 일치하는가 | detached 원문의 줄바꿈 변경 |
| 신뢰·용도 판단 | 서명 키를 해당 목적으로 신뢰하는가 | 알 수 없는 발급자 또는 허용되지 않은 용도 |

인증서를 파일 안에 포함하는 이유는 검증에 필요한 공개 키 정보를 전달하기 위해서다. 포함됐다는 이유만으로 그 인증서가 신뢰 저장소의 루트가 되지는 않는다. 공격자도 자신이 만든 인증서를 파일에 넣을 수 있다.

## signed attributes가 있을 때의 두 연결

콘텐츠 바이트의 해시는 `messageDigest` 속성과 연결되고, 서명은 규격이 정한 속성 집합의 인코딩과 연결된다. 검증기는 서명만 맞추고 콘텐츠 해시 비교를 빼먹어서는 안 된다. ‘서명된 속성이 맞음’과 ‘이 콘텐츠가 그 속성에 대응함’을 모두 확인해야 한다.

이 흐름은 [RFC 5652 §5.4–5.6](https://www.rfc-editor.org/rfc/rfc5652.html#section-5.4)을 순서대로 읽으면 연결된다. 인증서 경로의 신뢰 판단은 서명 수학 연산과 다른 단계로 설계한다.

## 관련 RFC

- [RFC 2315: PKCS #7 v1.5](https://www.rfc-editor.org/rfc/rfc2315.html)
- [RFC 5652: Cryptographic Message Syntax](https://www.rfc-editor.org/rfc/rfc5652.html)
