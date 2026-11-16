---
title: PKCS 표준
description: "PKCS #1부터 #12까지 각 공개 키 암호 규격의 목적, 관련 RFC, 현재 사용 여부와 보안 주의사항을 정리합니다."
parent: "PKI & 암호"
nav_order: 6
has_children: true
permalink: /pki/pkcs/
last_modified_date: 2026-11-16
---

# PKCS #1부터 #12까지

PKCS(Public-Key Cryptography Standards)는 RSA Laboratories가 공개 키 암호의 실제 사용과 상호 운용을 위해 만든 규격 모음이다. 번호가 연속된 하나의 프로토콜은 아니며, 각 번호가 서로 다른 문제를 다룬다.

일부 규격은 RFC로 발행됐고, 일부는 다른 표준에 흡수되거나 폐기됐다. 따라서 `PKCS #숫자`만 보고 최신 규격이라고 생각하면 안 된다.

## 전체 지도

| 번호 | 주제 | 현재 이해할 핵심 |
| --- | --- | --- |
| [#1]({{ '/pki/pkcs/pkcs1/' | relative_url }}) | RSA 암호와 서명 | RFC 8017, OAEP와 PSS |
| [#2]({{ '/pki/pkcs/pkcs2/' | relative_url }}) | RSA 메시지 다이제스트 | 폐기, PKCS #1에 흡수 |
| [#3]({{ '/pki/pkcs/pkcs3/' | relative_url }}) | Diffie-Hellman 키 합의 | 역사적 규격, 최신 프로토콜과 그룹 사용 |
| [#4]({{ '/pki/pkcs/pkcs4/' | relative_url }}) | RSA 키 문법 | 폐기, PKCS #1에 흡수 |
| [#5]({{ '/pki/pkcs/pkcs5/' | relative_url }}) | 패스워드 기반 암호 | RFC 8018, PBKDF2·PBES2 |
| [#6]({{ '/pki/pkcs/pkcs6/' | relative_url }}) | 확장 인증서 문법 | 폐기, X.509 v3 확장으로 대체 |
| [#7]({{ '/pki/pkcs/pkcs7/' | relative_url }}) | 서명·암호 메시지 | RFC 2315, 현재는 CMS RFC 5652 |
| [#8]({{ '/pki/pkcs/pkcs8/' | relative_url }}) | 개인 키 컨테이너 | RFC 5208, 후속 RFC 5958 |
| [#9]({{ '/pki/pkcs/pkcs9/' | relative_url }}) | 선택 속성 타입 | RFC 2985 |
| [#10]({{ '/pki/pkcs/pkcs10/' | relative_url }}) | 인증서 서명 요청 | RFC 2986, CSR |
| [#11]({{ '/pki/pkcs/pkcs11/' | relative_url }}) | 암호 토큰 API | Cryptoki, HSM·스마트카드 |
| [#12]({{ '/pki/pkcs/pkcs12/' | relative_url }}) | 키·인증서 묶음 파일 | RFC 7292, `.p12`·`.pfx` |

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
