---
layout: single
title: "[PKI] PKCS#10 subject"
date: 2021-04-10
comments: true
categories:
  - pki
tags: [CR, PKCS#10]
# 목차
toc: false
toc_sticky: false
---
## PKCS#10
- 인증서 요청 표준(Certification Request Standard)
- RFC2986 문서의 Certification request syntax에서 CertificationRequestInfo 대한 ASN.1
```
Certification request information shall have ASN.1 type
   CertificationRequestInfo:

   CertificationRequestInfo ::= SEQUENCE {
        version       INTEGER { v1(0) } (v1,...),
        subject       Name,
        subjectPKInfo SubjectPublicKeyInfo{{ PKInfoAlgorithms }},
        attributes    [0] Attributes{{ CRIAttributes }}
   }

   SubjectPublicKeyInfo { ALGORITHM : IOSet} ::= SEQUENCE {
        algorithm        AlgorithmIdentifier {{IOSet}},
        subjectPublicKey BIT STRING
   }
   PKInfoAlgorithms ALGORITHM ::= {
        ...  -- add any locally defined algorithms here -- }

   Attributes { ATTRIBUTE:IOSet } ::= SET OF Attribute{{ IOSet }}

   CRIAttributes  ATTRIBUTE  ::= {
        ... -- add any locally defined attributes here -- }

   Attribute { ATTRIBUTE:IOSet } ::= SEQUENCE {
        type   ATTRIBUTE.&id({IOSet}),
        values SET SIZE(1..MAX) OF ATTRIBUTE.&Type({IOSet}{@type})
   }
```

- 여기에서 subject에 대해 rfc 문서에 subject is the distinguished name of the certificate subject(the entity whose public key is to be certified) 라고함.  
- 전자서명인증관리체계 DN 규격에 따라 공인인증서의 경우 subject에 아래와 같은 형태로 들어가야함.
![Framework1][dn]

[dn]: https://raw.githubusercontent.com/yepark/yepark.github.io/master/assets/images/dn.png "DN 규격"

## 참고 사이트
- [rfc2986](https://tools.ietf.org/html/rfc2986)
- [전자서명인증관리체계 DN 규격](https://www.rootca.or.kr/kcac/down/TechSpec/1.3-KCAC.TS.DN.pdf)

