---
title: "PKCS #6: 확장 인증서 문법과 X.509 v3"
description: "폐기된 PKCS #6 확장 인증서 문법과 이를 대체한 X.509 v3 확장, critical 처리 규칙을 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 6
permalink: /pki/pkcs/pkcs6/
date: 2026-11-17
last_modified_at: 2026-11-20
seo:
  type: BlogPosting
last_modified_date: 2026-11-20
tags: [PKI, PKCS6, X509]
---

# PKCS #6: 확장 인증서 문법과 X.509 v3
{: .no_toc }

{% include article-toc.md %}

PKCS #6는 X.509 인증서에 추가 속성을 연결하기 위한 **Extended-Certificate Syntax**를 정의했던 초기 규격이다. 이후 X.509 v3가 인증서 확장 기능을 직접 제공하면서 폐기됐다.

## 인증서에 용도가 필요한 이유

인증서는 공개 키와 주체 정보를 담는다. 하지만 키가 들어 있다고 모든 작업에 사용할 수 있는 것은 아니다. 서버 인증에 쓸지, 다른 인증서를 발급하는 CA 키인지 같은 제한도 표현해야 한다.

확장은 이 추가 정보를 넣는 구조다. 이 편의 목표는 폐기된 PKCS #6을 새로 구현하는 것이 아니라, 현재 인증서의 확장을 읽고 용도를 검증하는 이유를 이해하는 것이다.

## 왜 확장이 필요했을까

인증서에는 이름과 공개 키만으로 표현하기 어려운 정책 정보가 필요하다.

- 이 인증서가 CA 인증서인지
- 어떤 용도로 키를 사용할 수 있는지
- 어떤 DNS 이름에 유효한지
- 폐지 정보를 어디서 확인할지
- 발급자와 주체의 키 식별자는 무엇인지

초기 X.509 구조의 바깥에 속성을 붙이는 접근보다 인증서 자체에 표준 확장을 넣는 X.509 v3 방식이 자리 잡았다.

## 현재 사용하는 X.509 v3 확장 예

| 확장 | 역할 |
| --- | --- |
| Basic Constraints | CA 여부와 경로 길이 제한 |
| Key Usage | 서명, 키 암호화, 인증서 서명 같은 비트 단위 용도 |
| Extended Key Usage | TLS 서버, 코드 서명 같은 세부 용도 |
| Subject Alternative Name | DNS, IP, 이메일 등 대체 이름 |
| Subject/Authority Key Identifier | 주체 키와 발급자 키 식별 보조 |
| CRL Distribution Points | CRL 위치 |
| Authority Information Access | OCSP·발급자 인증서 위치 |

## critical 플래그

X.509 확장에는 `critical` 여부가 있다. 검증자가 이해하지 못하는 critical 확장을 만나면 인증서를 거부해야 한다. non-critical 확장은 이해하지 못하면 무시할 수 있다.

이 플래그는 “보안상 중요해 보이는가”가 아니라, 해당 확장을 이해하지 못한 검증자가 인증서를 안전하게 처리할 수 있는지에 관한 상호 운용 규칙이다.

## 현재 무엇을 봐야 할까

- 인터넷 PKI 인증서 프로파일: RFC 5280
- 인증서 ASN.1 구조: X.509와 관련 프로파일
- TLS 서버 이름 확인: 해당 TLS 및 서비스 식별 규격
- 특정 조직의 인증서: 그 조직의 CP/CPS와 인증서 프로파일

PKCS #6 포맷을 새로 생성하지 않는다. 오래된 파일이나 소프트웨어를 분석할 때만 역사적 구조로 만날 수 있다.

## 검증 시 주의사항

- 알 수 없는 critical 확장을 무시하지 않는다.
- Key Usage와 Extended Key Usage를 모두 확인한다.
- CA 인증서는 Basic Constraints와 인증서 서명 용도를 확인한다.
- 이름 검증을 Subject의 CN만으로 단순 처리하지 않는다.
- 파싱 성공과 신뢰 검증 성공을 구분한다.

## 서명은 맞는데 인증서 용도는 틀릴 수 있다

어떤 인증서의 CA 서명이 유효해도 그 인증서를 다른 인증서 발급에 사용할 수 있다고 결론 내리면 안 된다. 인증서가 CA 역할을 허용하는지, 해당 키 용도가 맞는지 등 추가 조건을 확인해야 한다.

예를 들어 서버 인증서에 자신의 DNS 이름이 포함됐다는 사실과 CA 권한이 있다는 사실은 다르다. 이름은 ‘누구에 대한 인증서인가’를, 용도 제한은 ‘어떤 역할에 사용할 수 있는가’를 다룬다. 확장을 단순한 표시용 정보로 읽으면 이 차이를 놓친다.

## X.509 v3를 공부하는 읽기 순서

[RFC 5280 §4.2](https://www.rfc-editor.org/rfc/rfc5280.html#section-4.2)에서 확장 구조와 개별 확장을 읽고, §6에서 경로 검증과 연결한다. critical은 ‘보안상 좋아 보이는 항목’이라는 표시가 아니라, 처리할 수 없는 확장이 있을 때 인증서를 받아들여도 되는지에 영향을 주는 규칙이다.

파싱한 확장 값을 화면에 출력하는 것과 그 제한을 실제 검증에 반영하는 것은 다른 작업이다. PKCS #6의 역사를 읽은 뒤에는 새로운 확장 컨테이너를 만들기보다 현재 플랫폼의 인증서 검증 API가 어떤 정책을 적용하는지 확인하는 쪽으로 학습을 이어간다.

## 역사적 구조와 현재 프로파일의 근거

- [RFC 5280: Internet X.509 Public Key Infrastructure Certificate and CRL Profile](https://www.rfc-editor.org/rfc/rfc5280.html)

- [RFC 2630 §10.2.1](https://www.rfc-editor.org/rfc/rfc2630.html#section-10.2.1): 옛 CMS에서 PKCS #6 extended certificate를 obsolete로 다루는 문맥. RFC 2630도 현재 CMS 구현 문서가 아닌 역사적 근거다.

RFC 5280은 PKCS #6 자체를 RFC로 옮긴 문서가 아니라 인터넷에서 X.509 인증서와 CRL을 사용하는 프로파일이다.
