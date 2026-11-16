---
title: "PKCS #6: 확장 인증서 문법과 X.509 v3"
description: "폐기된 PKCS #6 확장 인증서 문법과 이를 대체한 X.509 v3 확장, critical 처리 규칙을 설명합니다."
parent: PKCS 표준
grand_parent: "PKI & 암호"
nav_order: 6
permalink: /pki/pkcs/pkcs6/
last_modified_date: 2026-11-16
tags: [PKI, PKCS6, X509]
---

# PKCS #6: 확장 인증서 문법과 X.509 v3

PKCS #6는 X.509 인증서에 추가 속성을 연결하기 위한 **Extended-Certificate Syntax**를 정의했던 초기 규격이다. 이후 X.509 v3가 인증서 확장 기능을 직접 제공하면서 폐기됐다.

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

## 관련 RFC

- [RFC 5280: Internet X.509 Public Key Infrastructure Certificate and CRL Profile](https://www.rfc-editor.org/rfc/rfc5280.html)
