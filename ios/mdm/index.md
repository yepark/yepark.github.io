---
title: "Apple MDM"
parent: iOS
nav_order: 30
has_children: true
has_toc: false
permalink: /ios/mdm/
last_modified_date: 2026-11-27
---

# Apple MDM

회사가 직원에게 iPhone 100대를 나눠 준다고 하자. 사내 Wi-Fi와 VPN을 설정하고, 업무 앱을 깔고, 화면 잠금 암호를 강제하고, 잃어버린 기기는 원격으로 잠가야 한다. 한 대씩 손으로 할 수는 없다.

**MDM(Mobile Device Management)**은 서버가 원격으로 기기에 설정을 넣고, 앱을 설치하고, 상태를 조회하고, 잠금·초기화 같은 명령을 내리는 기기 관리 방식이다. Apple은 iPhone, iPad, Mac, Apple TV, Apple Vision Pro에 MDM 프로토콜을 운영체제 기능으로 내장하고 있어서, 기기에 별도 관리 앱을 깔지 않아도 MDM 서버의 지시를 받는다.

이 연재는 MDM 서버를 직접 만들거나 운영하는 개발자의 관점에서, 기기가 처음 켜지는 순간의 자동 등록(ADE, 예전 이름 DEP)부터 최신 방식인 선언형 기기 관리(DDM)까지 차례로 다룬다.

{% include series-list.html heading="연재 목차" %}

## 전체 그림

| 단계 | 다루는 글 | 핵심 질문 |
| --- | --- | --- |
| 구조 | 1편 | 서버, APNs, 기기는 어떻게 대화하나 |
| 등록 | 2편 | 기기는 어떻게 MDM 서버에 처음 연결되나 (ADE/DEP, 사용자 등록) |
| 설정 | 3편 | Wi-Fi, 인증서, 제한은 어떻게 넣나 (구성 프로파일) |
| 명령 | 4편 | 조회·잠금·초기화는 어떻게 하나, 감독 모드는 무엇을 더 허용하나 |
| 앱 | 5편 | 앱 라이선스와 설치, 앱 설정은 어떻게 하나 |
| DDM | 6편 | 명령 대신 "원하는 상태"를 선언하면 무엇이 달라지나 |
| 운영 | 7편 | 인증서·토큰 갱신, 보안, 장애 대응 |

## 먼저 알아 둘 용어

| 용어 | 뜻 |
| --- | --- |
| ABM / ASM | Apple Business Manager / Apple School Manager. 기관이 소유한 기기, 앱 라이선스, 관리형 계정을 관리하는 Apple의 웹 포털 |
| ADE (DEP) | Automated Device Enrollment. 구입한 기기가 처음 켜질 때 자동으로 기관의 MDM 서버에 등록되게 하는 기능. 예전 이름은 Device Enrollment Program |
| APNs | Apple Push Notification service. MDM 서버가 기기를 깨울 때 쓰는 Apple의 푸시 서비스 |
| 구성 프로파일 | Wi-Fi, VPN, 인증서, 제한 같은 설정을 담은 XML 파일(`.mobileconfig`) |
| 감독(Supervised) 모드 | 기관 소유 기기에 더 강한 관리 권한을 주는 상태 |
| DDM | Declarative Device Management. 서버가 명령을 하나씩 보내는 대신 "원하는 상태"를 선언하고, 기기가 스스로 맞추고 상태를 보고하는 방식 |
| 관리형 Apple 계정 | 기관이 만들고 소유하는 Apple 계정(예전 이름 관리형 Apple ID) |

## 함께 읽기

- [TLS 인증서 검증과 피닝]({{ '/pki/ssl-pinning/' | relative_url }}): MDM은 모든 통신에 TLS와 클라이언트 인증서를 쓴다
- [PKCS #12]({{ '/pki/pkcs12/' | relative_url }}), [PKCS #7]({{ '/pki/pkcs7/' | relative_url }}): 프로파일 서명과 인증서 배포에 쓰이는 형식
- [App Attest]({{ '/ios/app-attest/' | relative_url }}): 앱 쪽에서 기기 무결성을 증명하는 다른 방법
