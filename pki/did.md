---
title: "DID: 탈중앙 신원 증명"
description: "W3C DID 표준의 구조와 DID Document, Verifiable Credential의 발급·검증 흐름, PKI 인증서와의 차이를 설명합니다."
parent: "PKI & 암호"
nav_order: 8
permalink: /pki/did/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [PKI, DID, SSI, Verifiable-Credential, W3C, 블록체인]
---

# DID: 탈중앙 신원 증명
{: .no_toc }

{% include article-toc.md %}

인증서는 "이 공개 키는 github.com의 것이다"라고 CA(인증 기관)가 보증하는 구조다. 신뢰가 CA에 집중된다. CA가 실수하거나 침해를 당하면 그 CA를 신뢰하는 모든 연결이 위험해진다.

**DID(Decentralized Identifier, 탈중앙 식별자)**는 CA 없이 스스로 신원을 증명하는 방법을 정의한다. 2022년 W3C 권고안으로 확정됐고, 모바일 운전면허증, 학위 증명, 의료 기록 등 다양한 디지털 신원 분야에 적용되고 있다.

## 왜 CA 중심 구조에 한계가 생겼나

기존 PKI 인증서는 웹 서버 신원 확인에 최적화되어 있다. 사람이나 조직의 속성(자격증, 나이, 소속)을 증명하는 데 쓰기에는 한계가 있다.

| 한계 | 내용 |
| --- | --- |
| 중앙 의존 | 특정 CA가 폐업하거나 침해되면 발급한 인증서 전체가 영향을 받는다 |
| 사용자 통제 없음 | 인증서 발급·폐기 권한이 CA에 있고 개인이 직접 관리하기 어렵다 |
| 개인정보 과노출 | 검증자가 발급자에게 조회를 요청하면 사용자가 어디에 인증서를 제출했는지 발급자가 알 수 있다 |
| 선택적 공개 불가 | 인증서 전체를 보여 줘야 한다. 나이만 증명하고 싶어도 주민번호 전체가 담긴 문서를 내야 한다 |

DID는 이 문제를 세 가지 원칙으로 해결한다. 주체가 직접 식별자를 생성하고, 제3자 등록 없이 검증 가능하며, 공개할 정보를 선택할 수 있다.

## DID의 구조

DID는 세 부분으로 이루어진 문자열이다.

```text
did:method:method-specific-id

예시:
did:web:yepark.github.io
did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK
did:ion:EiAnKD8-jfdd0MDcZUjAbRgaThBrMxPTFOxcnfJhI7Idrw
```

- `did` — 고정 접두사
- `method` — DID를 어디에 어떻게 등록하고 조회하는지 정의하는 방식 이름
- `method-specific-id` — 해당 method 안에서 유일한 식별자

`method`마다 등록 저장소와 조회 방법이 다르다. 블록체인을 쓰는 방식도 있고, 웹 서버를 쓰는 방식도 있다.

### 주요 DID Method

| Method | 저장소 | 특징 |
| --- | --- | --- |
| `did:web` | 웹 서버 | 도메인에 JSON 파일 배포. 가장 단순 |
| `did:key` | 없음 | 공개 키 자체가 DID. 등록 불필요 |
| `did:ion` | Bitcoin 블록체인 | Microsoft 개발. 오프라인 생성 가능 |
| `did:ethr` | Ethereum | 스마트 컨트랙트로 관리 |
| `did:peer` | 없음 | 두 주체 사이에서만 유효한 P2P DID |

## DID Document

DID를 조회하면 **DID Document**를 받는다. 이 문서에는 DID 주체의 공개 키, 인증 방법, 서비스 엔드포인트 등이 담겨 있다.

```json
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:web:yepark.github.io",
  "verificationMethod": [
    {
      "id": "did:web:yepark.github.io#key-1",
      "type": "JsonWebKey2020",
      "controller": "did:web:yepark.github.io",
      "publicKeyJwk": {
        "kty": "EC",
        "crv": "P-256",
        "x": "...",
        "y": "..."
      }
    }
  ],
  "authentication": [
    "did:web:yepark.github.io#key-1"
  ],
  "service": [
    {
      "id": "did:web:yepark.github.io#credential-service",
      "type": "CredentialService",
      "serviceEndpoint": "https://yepark.github.io/credentials"
    }
  ]
}
```

`verificationMethod`는 이 DID 주체가 소유한 공개 키 목록이다. `authentication`은 그 중 본인 인증에 쓸 수 있는 키를 가리킨다.

CA 인증서와 비교하면 DID Document는 주체가 직접 작성하고 갱신한다. CA의 서명 없이도 등록 저장소(블록체인, 웹 서버 등)에서 가져와 검증할 수 있다.

## did:web 직접 만들어 보기

`did:web`은 웹 서버에 JSON 파일을 올리는 방식이다. GitHub Pages를 쓴다면 별도 인프라 없이 DID를 운영할 수 있다.

`https://yepark.github.io/.well-known/did.json` 경로에 DID Document를 배포하면 DID는 `did:web:yepark.github.io`가 된다.

```bash
# EC 키 쌍 생성 (P-256)
openssl ecparam -name prime256v1 -genkey -noout -out private.pem
openssl ec -in private.pem -pubout -out public.pem

# 공개 키를 JWK 형태로 확인
openssl ec -in public.pem -pubin -text -noout
```

키를 만들어 DID Document에 `publicKeyJwk` 필드로 넣고 `.well-known/did.json`으로 배포한다. DID Resolver가 도메인을 조회하면 이 파일을 가져간다.

{: .note }
`did:web`은 도메인 소유자가 파일을 임의로 교체할 수 있으므로 신뢰 모델이 도메인 소유권에 의존한다. 불변 이력이 필요하면 블록체인 기반 method를 선택한다.

## Verifiable Credential

DID가 "나는 did:web:yepark.github.io다"를 증명하는 수단이라면, **VC(Verifiable Credential)**는 그 주체에 대한 속성을 제3자가 발급하는 증명서다.

현실 세계로 비유하면 이렇다.
- **DID** = 주민등록번호 (고유 식별자)
- **VC** = 운전면허증, 학위증, 재직증명서 (속성을 담은 증명서)
- **VP(Verifiable Presentation)** = 지갑에서 꺼내 보여 주는 행위

### VC의 구조

```json
{
  "@context": ["https://www.w3.org/2018/credentials/v1"],
  "type": ["VerifiableCredential", "UniversityDegreeCredential"],
  "issuer": "did:web:university.example",
  "issuanceDate": "2026-06-01T00:00:00Z",
  "credentialSubject": {
    "id": "did:web:yepark.github.io",
    "degree": {
      "type": "BachelorDegree",
      "name": "컴퓨터공학"
    }
  },
  "proof": {
    "type": "JsonWebSignature2020",
    "created": "2026-06-01T00:00:00Z",
    "verificationMethod": "did:web:university.example#key-1",
    "jws": "eyJhbGciOiJFUzI1NiJ9..."
  }
}
```

- `issuer` — 발급자의 DID
- `credentialSubject.id` — 이 VC가 설명하는 주체의 DID
- `proof` — 발급자가 개인 키로 서명한 증명. 발급자의 DID Document에서 공개 키를 가져와 검증한다

## 발급·보관·검증 흐름

세 역할이 등장한다.

- **Issuer (발급자)**: 대학, 병원, 정부 기관 등. VC를 발급하고 서명한다.
- **Holder (보유자)**: 개인. VC를 받아 디지털 지갑에 보관하고 필요할 때 제출한다.
- **Verifier (검증자)**: 서비스, 기업 등. 제출된 VC를 검증한다.

```text
[발급 단계]
Holder → Issuer: "학위 VC 발급 요청"
Issuer: VC 생성 + 개인 키로 서명
Issuer → Holder: 서명된 VC 전달
Holder: 디지털 지갑에 저장

[검증 단계]
Verifier → Holder: "학위 증명을 제출하세요"
Holder: 지갑에서 VC 선택 → VP(Verifiable Presentation) 생성 + 서명
Holder → Verifier: VP 제출

Verifier:
  1. VP의 Holder 서명 검증 (Holder의 DID Document에서 공개 키 조회)
  2. VC의 Issuer 서명 검증 (Issuer의 DID Document에서 공개 키 조회)
  3. 발급일, 만료일, 폐기 여부 확인
  4. credentialSubject가 Holder와 일치하는지 확인
```

검증 과정에서 Verifier는 Issuer에게 직접 연락하지 않는다. DID Document만 조회하면 된다. Issuer는 누가 VC를 어디에 제출했는지 알 수 없다.

## 선택적 공개

나이 확인이 필요한 서비스에 운전면허 VC 전체를 제출할 필요가 없다. **선택적 공개(Selective Disclosure)**를 쓰면 "나이가 19세 이상이다"라는 사실만 증명할 수 있다.

**SD-JWT(Selective Disclosure for JWT)**는 현재 가장 많이 쓰이는 방식이다. 발급자가 각 클레임을 개별 해시로 묶어 서명하고, Holder가 공개할 클레임의 원문만 선택해 제출한다. Verifier는 받은 원문의 해시가 서명된 해시와 일치하는지 확인한다.

```text
발급자가 서명한 내용:
  이름_해시, 나이_해시, 주소_해시, 면허번호_해시, ...

Holder가 제출하는 내용:
  서명된 해시 목록 + 나이 원문만 공개
  → "나이_해시 = SHA256('만 29세')" 를 검증자가 확인
```

주민번호, 주소, 면허번호는 공개하지 않고 나이 조건만 증명한다. 공개하지 않은 항목은 해시만 남아 있어 역산이 불가능하다.

## PKI 인증서와의 비교

| 항목 | X.509 인증서 | DID + VC |
| --- | --- | --- |
| 신뢰 근거 | CA의 서명 | 발급자의 DID와 서명 |
| 식별자 소유 | CA가 발급 | 주체가 직접 생성 |
| 폐기 | CRL / OCSP | 상태 목록 / 블록체인 이벤트 |
| 선택적 공개 | 불가 | SD-JWT 등으로 가능 |
| 주요 용도 | TLS 서버 인증 | 디지털 신원·자격 증명 |
| 표준 | IETF RFC 5280 | W3C DID Core, VC Data Model |

TLS 인증서를 DID로 대체하는 것이 아니다. 서버 인증은 여전히 X.509가 적합하다. DID와 VC는 사람·조직·기기의 속성 증명에 맞는 도구다.

## 실제 적용 사례

**모바일 운전면허증 (mDL)**  
ISO/IEC 18013-5 표준 기반. Apple Wallet과 Google Wallet에서 운전면허증을 디지털로 저장하고 공항·주류 구매 현장에서 제시할 수 있다. 필요한 정보만 선택 공개한다.

**EU 디지털 신원 지갑 (EUDI Wallet)**  
유럽연합이 추진 중인 범유럽 디지털 신원 체계. 학위, 처방전, 여권 등을 VC 형태로 하나의 지갑에 보관한다.

**Microsoft Entra Verified ID**  
기업 환경에서 사원증·자격증을 VC로 발급하고 파트너사가 검증하는 B2B 신원 시스템. `did:web` 방식으로 운영된다.

## 구현 시 주의할 점

**키 분실은 복구 불가다.**  
CA 인증서는 CA에 재발급을 요청하면 된다. DID의 개인 키는 주체 스스로 관리한다. 분실하면 해당 DID로 서명할 방법이 없어진다. 복구 메커니즘(멀티시그, 위임 키 등)을 처음부터 설계해야 한다.

**Method 선택이 신뢰 모델을 결정한다.**  
`did:web`은 서버 운영자를 신뢰해야 하고, 블록체인 기반 method는 체인의 가용성에 의존한다. 용도에 맞는 method를 선택한다.

**폐기를 설계한다.**  
VC가 유출됐거나 발급 조건이 바뀌었을 때 폐기할 방법이 있어야 한다. W3C는 StatusList2021 같은 상태 목록 표준을 정의한다. 폐기 엔드포인트를 Verifier가 반드시 확인하도록 명세를 잡는다.

**상호 운용성을 먼저 확인한다.**  
DID method와 VC 형식, 서명 알고리즘의 조합이 많다. 연동할 상대방이 지원하는 조합을 먼저 확인한다. DIF(Decentralized Identity Foundation)의 호환성 테스트 도구를 활용한다.

## 정리

DID는 CA 없이 주체 스스로 식별자를 생성하고 공개 키를 등록하는 표준이다. VC는 발급자가 DID 주체의 속성을 서명해 담은 증명서이며, Holder가 직접 보관하고 선택적으로 제출한다. 검증자는 발급자의 DID Document만 조회해 신뢰 체계에 참여한다. 서버 인증의 X.509 인증서를 대체하는 것이 아니라, 사람과 조직의 디지털 속성 증명에 맞는 새로운 계층을 추가하는 기술이다.

## 참고

- [W3C DID Core 1.0](https://www.w3.org/TR/did-core/)
- [W3C Verifiable Credentials Data Model 2.0](https://www.w3.org/TR/vc-data-model-2.0/)
- [SD-JWT: IETF Draft](https://datatracker.ietf.org/doc/draft-ietf-oauth-selective-disclosure-jwt/)
- [DIF: Decentralized Identity Foundation](https://identity.foundation/)
- [Microsoft Entra Verified ID](https://learn.microsoft.com/en-us/azure/active-directory/verifiable-credentials/)
