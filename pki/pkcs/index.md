---
title: PKCS 표준
description: "PKCS #1부터 #12까지 각 공개 키 암호 규격의 목적, 관련 RFC, 현재 사용 여부와 보안 주의사항을 정리합니다."
parent: "PKI & 암호"
nav_order: 6
has_children: true
has_toc: false
permalink: /pki/pkcs/
last_modified_date: 2026-11-16
---

# PKCS #1부터 #12까지

PKCS(Public-Key Cryptography Standards)는 RSA Laboratories가 공개 키 암호의 실제 사용과 상호 운용을 위해 만든 규격 모음이다. 번호가 연속된 하나의 프로토콜은 아니며, 각 번호가 서로 다른 문제를 다룬다.

일부 규격은 RFC로 발행됐고, 일부는 다른 표준에 흡수되거나 폐기됐다. 따라서 `PKCS #숫자`만 보고 최신 규격이라고 생각하면 안 된다.

{% include series-list.html %}


## RFC를 읽을 때 알아둘 표현

- `MUST`: 반드시 지켜야 상호 운용되는 요구사항
- `MUST NOT`: 반드시 하면 안 되는 요구사항
- `SHOULD`: 특별한 이유가 없다면 따라야 하는 권고
- `MAY`: 구현이 선택할 수 있는 기능
- ASN.1: 인증서와 키 같은 데이터 구조를 정의하는 표기법
- DER: ASN.1 값을 바이트로 유일하게 인코딩하는 규칙
- OID: 알고리즘이나 속성의 종류를 식별하는 번호

{: .warning }
암호 규격의 ASN.1 구조를 직접 구현하는 것은 학습과 제품 개발이 다르다. 제품에서는 검증된 라이브러리를 사용하고, 규격 버전·알고리즘 파라미터·오류 처리까지 상호 운용 테스트로 확인해야 한다.
