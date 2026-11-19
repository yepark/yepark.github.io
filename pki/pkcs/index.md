---
title: PKCS 표준
description: "PKCS #1부터 #12까지 각 공개 키 암호 규격의 목적, 관련 RFC, 현재 사용 여부와 보안 주의사항을 정리합니다."
parent: "PKI & 암호"
nav_order: 6
has_children: true
has_toc: false
permalink: /pki/pkcs/
last_modified_date: 2026-11-20
---

# PKCS #1부터 #12까지

PKCS(Public-Key Cryptography Standards)는 RSA Laboratories가 공개 키 암호의 실제 사용과 상호 운용을 위해 만든 규격 모음이다. 번호가 연속된 하나의 프로토콜은 아니며, 각 번호가 서로 다른 문제를 다룬다.

일부 규격은 RFC로 발행됐고, 일부는 다른 표준에 흡수되거나 폐기됐다. 따라서 `PKCS #숫자`만 보고 최신 규격이라고 생각하면 안 된다.

{% include series-list.html %}


## 번호보다 규격의 역할을 먼저 찾기

| 번호 | 지금 읽을 문서 또는 체계 | 관계 |
| --- | --- | --- |
| #1 | RFC 8017 | RSA 규격 v2.2를 재발행한 Informational RFC |
| #2·#4 | PKCS #1 | 독립 규격으로 폐기·통합된 역사적 번호 |
| #3 | 원래 DH 규격, 사용 프로토콜의 키 합의 규칙 | RFC 2631·7919·7748이 같은 포맷의 ‘최신판’인 것은 아님 |
| #5 | RFC 8018 | 패스워드 기반 암호 규격 v2.1 |
| #6 | X.509 v3, 인터넷 프로파일 RFC 5280 | 옛 확장 인증서 문법을 현재 확장 모델이 대신함 |
| #7 | RFC 2315와 CMS RFC 5652 | PKCS #7에서 CMS로 발전, 동일한 문서의 별칭이 아님 |
| #8 | RFC 5208 → RFC 5958 | RFC 5958이 5208을 obsoletes하고 키 패키지 구조를 확장 |
| #9·#10 | RFC 2985·2986 | 각각 속성 정의와 CSR 문법 |
| #11 | OASIS PKCS #11 | 파일 포맷이 아닌 토큰 API이며 대응하는 현재 RFC는 없음 |
| #12 | RFC 7292, RFC 9879 | 9879는 PBMAC1 사용을 추가하고 7292·8018을 updates함 |

RFC 번호는 그 자체로 최신성이나 Internet Standard 지위를 뜻하지 않는다. 문서 첫머리의 상태, `Obsoletes`와 `Updates`, 적용 프로토콜을 함께 읽는다. `Obsoletes`는 이전 문서를 대체하는 관계이고 `Updates`는 일부 내용을 보완하는 관계다. 예를 들어 RFC 9879가 존재한다고 PKCS #12의 모든 구조를 그 문서 하나에서 찾을 수 있는 것은 아니다.

## RFC를 읽을 때 알아둘 표현

- `MUST`: 해당 규격의 절대적 요구사항
- `MUST NOT`: 반드시 하면 안 되는 요구사항
- `SHOULD`: 예외의 영향을 이해하고 신중히 판단해야 하는 권고
- `MAY`: 구현이 선택할 수 있는 기능
- ASN.1: 인증서와 키 같은 데이터 구조를 정의하는 표기법
- DER: ASN.1 값을 바이트로 유일하게 인코딩하는 규칙
- OID: 알고리즘이나 속성의 종류를 식별하는 번호

{: .warning }
암호 규격의 ASN.1 구조를 직접 구현하는 것은 학습과 제품 개발이 다르다. 제품에서는 검증된 라이브러리를 사용하고, 규격 버전·알고리즘 파라미터·오류 처리까지 상호 운용 테스트로 확인해야 한다.

규범 키워드의 의미는 [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html)와 [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174.html)에 정의돼 있다. 각 문서가 이 해석 규칙을 적용하는지도 확인한다.
