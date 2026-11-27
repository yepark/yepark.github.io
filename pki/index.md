---
title: "PKI & 암호"
nav_order: 7
has_children: true
permalink: /pki/
---

# PKI & 암호

인증서, RSA, 블록 암호처럼 보안 기능을 만들 때 알아야 하는 것들

**PKI(Public Key Infrastructure, 공개 키 기반 구조)**는 "이 공개 키가 정말 그 사람(서버)의 것인가"를 믿을 수 있게 해 주는 체계다. 인증기관(CA)이 공개 키와 주인의 이름을 묶은 인증서에 서명하고, 사용자는 그 서명을 따라 올라가 신뢰할 수 있는 루트 인증서까지 확인한다. HTTPS, 전자서명, 앱 코드 서명이 모두 이 구조 위에서 동작한다.

**PKCS(Public-Key Cryptography Standards)**는 RSA사가 1990년대에 만든 공개 키 암호 표준 묶음이다. #1부터 #15까지 번호가 붙어 있고, 번호는 순서나 난이도가 아니라 각각 다른 규격을 가리키는 이름이다. 지금도 쓰이는 규격 대부분은 IETF의 RFC 문서로 옮겨져 관리된다.

