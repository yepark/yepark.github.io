---
title: "MDM 운영: 인증서·토큰 갱신과 보안"
description: "MDM을 운영할 때 매년 갱신해야 하는 APNs 푸시 인증서·ADE 서버 토큰·앱 콘텐츠 토큰, 기기 ID 인증서 수명, 서버 보안과 요청 검증, 장애 진단 순서, 직접 만들어 볼 수 있는 오픈소스 MDM을 정리합니다."
parent: Apple MDM
grand_parent: iOS
nav_order: 7
permalink: /ios/mdm/operations/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, MDM, APNs, Operations, Security]
---

# MDM 운영: 인증서·토큰 갱신과 보안
{: .no_toc }

{% include article-toc.md %}

MDM 장애의 상당수는 코드가 아니라 **날짜**에서 생긴다. 1년짜리 인증서와 토큰이 여럿 있고, 하나라도 만료되면 수천 대의 기기 관리가 한꺼번에 멈춘다. 이 글은 MDM을 직접 운영하거나 서버를 만드는 사람이 챙겨야 할 것들을 정리한다.

## 갱신 달력

| 대상 | 어디서 받나 | 유효 기간 | 만료되면 |
| --- | --- | --- | --- |
| APNs MDM 푸시 인증서 | Apple Push Certificates Portal | 1년 | 기기를 깨울 수 없다. 명령이 전달되지 않는다 |
| ADE 서버 토큰 (`.p7m`) | ABM의 MDM 서버 설정 | 1년 | 새 기기 배정·등록 설정 변경 불가. 이미 등록된 기기 관리는 계속됨 |
| Apps and Books 콘텐츠 토큰 | ABM의 앱 및 도서 설정 | 1년 | 앱 라이선스 배정·회수 불가 |
| 기기 ID 인증서 | 서버의 SCEP·ACME | 서버가 정함 | 기기가 서버에 인증하지 못한다 |
| 서버 TLS 인증서 | 일반 CA | 일반 TLS와 같음 | 기기가 서버에 접속하지 못한다 |

### APNs 인증서는 "갱신"만 한다

가장 위험한 것은 APNs MDM 푸시 인증서다. 인증서 안의 **토픽**이 등록된 모든 기기에 기록돼 있기 때문이다.

- **같은 Apple 계정으로, 같은 인증서를 "갱신(Renew)"** 하면 토픽이 유지된다. 기기는 아무것도 모른 채 계속 관리된다.
- 다른 계정으로 새로 만들거나 "새 인증서 생성"을 누르면 토픽이 바뀐다. 서버는 기존 기기에 푸시를 보낼 수 없고, **모든 기기를 다시 등록**해야 한다. ADE 기기라면 초기화가 필요할 수 있다.

그래서 푸시 인증서는 개인 계정이 아니라 퇴사해도 남는 **기관 공용 관리형 Apple 계정**으로 만들고, 그 계정과 만료일을 문서로 남긴다. 만료 30일 전, 7일 전에 알림을 보내도록 서버에 날짜를 저장해 둔다.

### 기기 ID 인증서 갱신

기기 ID 인증서가 만료되면 기기는 서버에 자신을 증명하지 못한다. 서버는 만료 전에 새 인증서를 발급하는 프로파일(SCEP·ACME 페이로드를 담은 등록 프로파일의 갱신본)을 `InstallProfile`로 다시 보내 교체한다. 등록 프로파일은 `PayloadIdentifier`를 같게 유지해야 "교체"로 처리된다. 기존 인증서가 만료된 뒤에는 명령을 받을 수 없으므로, 반드시 **만료 전에** 교체한다.

## 서버 보안

MDM 서버는 기관의 모든 기기를 초기화할 수 있는 권한을 가진다. 탈취되면 피해가 매우 크다.

### 요청 검증

| 검증 | 이유 |
| --- | --- |
| 기기 ID 인증서로 클라이언트 인증(mTLS) 또는 `Mdm-Signature` 헤더 서명 검증 | 다른 기기나 공격자가 그 기기인 척 명령을 받아 가거나 거짓 결과를 보내는 것을 막는다 |
| 요청의 UDID·EnrollmentID와 인증서의 대응 확인 | A 기기의 인증서로 B 기기 행세를 하는 것을 막는다 |
| ADE 등록 요청의 Apple 서명 검증 | ABM에 없는 기기가 등록 프로파일을 받아 가는 것을 막는다 |
| 일회용 SCEP challenge | 등록 프로파일을 손에 넣은 사람이 기기 인증서를 마음대로 발급받는 것을 막는다 |

### 비밀 저장

다음 값은 데이터베이스에 평문으로 두지 않는다.

- APNs 푸시 인증서의 개인 키, ADE 서버 토큰의 개인 키, 콘텐츠 토큰
- 기기의 `UnlockToken`(암호 제거에 쓰임), 활성화 잠금 우회 코드
- SCEP CA의 개인 키 (가능하면 [HSM]({{ '/pki/pkcs11/' | relative_url }})에)

### 위험한 명령에 사람 확인 두기

`EraseDevice`를 여러 기기에 한꺼번에 보내는 기능은 실수 한 번으로 회사 전체 기기를 지울 수 있다. 대량 초기화·잠금에는 두 사람 승인, 대상 수 상한, 지연 실행(취소 가능 시간) 같은 장치를 둔다. 관리자 계정에는 다단계 인증을 건다.

## 장애 진단 순서

"명령이 안 간다"는 신고가 오면 아래 순서로 범위를 좁힌다.

| 순서 | 확인 | 문제라면 |
| --- | --- | --- |
| 1 | 서버가 APNs에 푸시를 보냈고 APNs가 성공 응답을 했나 | 푸시 인증서 만료, 토픽 불일치, 잘못된 토큰 |
| 2 | 기기가 `ServerURL`에 접속했나 (서버 접근 로그) | 기기 네트워크, 방화벽이 APNs 포트(TCP 5223, 443)나 서버를 막음 |
| 3 | 접속은 했는데 인증 실패인가 | 기기 ID 인증서 만료·불일치, 서버 TLS 인증서 문제 |
| 4 | 명령을 받았는데 `Error`/`NotNow`인가 | 명령 조건(감독 여부, 잠금 상태, BYOD 제한) |
| 5 | `Acknowledged`인데 결과가 안 보이나 | 비동기 작업(앱 설치, OS 업데이트)이라 별도 조회 필요 |

Mac에서는 `log stream --predicate 'subsystem == "com.apple.ManagedClient"'`로 `mdmclient`의 로그를, iPhone은 Mac의 콘솔 앱에 연결해 관련 로그를 볼 수 있다. 서버 쪽에서는 기기별로 마지막 접속 시각, 마지막 명령과 상태를 저장해 두면 1·2단계를 바로 판별할 수 있다.

## 직접 만들어 보기: 오픈소스 MDM

MDM 프로토콜을 공부하거나 사내 전용 서버를 만들 때 참고할 수 있는 오픈소스가 있다.

| 프로젝트 | 내용 |
| --- | --- |
| [NanoMDM](https://github.com/micromdm/nanomdm) | MDM 프로토콜의 핵심(체크인, 명령 대기열, 푸시)만 구현한 Go 서버. 구조를 이해하기 좋다 |
| [nanodep](https://github.com/micromdm/nanodep) | ADE(DEP) API 클라이언트와 등록 설정 도구 |
| [KMFDDM](https://github.com/jessepeterson/kmfddm) | DDM 선언 관리 서버 |
| [MicroMDM](https://github.com/micromdm/micromdm) | NanoMDM 이전 세대의 올인원 서버 |
| [apple/device-management](https://github.com/apple/device-management) | Apple이 공개한 명령·프로파일·선언 스키마 (YAML) |

실제 기기로 시험하려면 APNs MDM 푸시 인증서가 필요하다. 이 인증서는 MDM 벤더의 서명을 거쳐야 하므로, 개인 개발자는 벤더 계정이 없으면 받기 어렵다. 학습 단계에서는 Apple이 공개한 스키마로 명령·프로파일·선언을 만들고 검증하는 데까지 해 보고, 실제 기기 시험은 상용 MDM의 개발용 테넌트를 활용하는 방법이 현실적이다.

## 운영 점검표

- [ ] APNs 푸시 인증서, ADE 서버 토큰, 콘텐츠 토큰의 만료일과 담당 계정이 문서화돼 있다
- [ ] 푸시 인증서는 기관 공용 관리형 Apple 계정으로 만들었다
- [ ] 만료 30일·7일 전 알림이 있다
- [ ] 기기 ID 인증서를 만료 전에 자동 교체한다
- [ ] 기기 요청의 인증서·서명을 검증한다
- [ ] `UnlockToken`, 우회 코드, 토큰 개인 키를 암호화해 저장한다
- [ ] 대량 초기화·잠금에 승인 절차와 상한이 있다
- [ ] 기기별 마지막 접속 시각과 명령 상태를 볼 수 있다
- [ ] 새 OS 베타가 나오면 테스트 기기로 프로파일·명령·선언 동작을 먼저 확인한다

## 정리

- 1년짜리 인증서·토큰이 셋(APNs 푸시, ADE 서버 토큰, 콘텐츠 토큰) 있고, 만료되면 관리가 멈춘다.
- APNs 푸시 인증서는 반드시 같은 계정으로 갱신해야 토픽이 유지된다. 새로 만들면 모든 기기를 다시 등록해야 한다.
- 기기 ID 인증서는 만료 전에 같은 식별자의 프로파일로 교체한다.
- 서버는 기기 요청을 인증서로 검증하고, 민감한 토큰을 암호화해 저장하며, 위험한 대량 명령에 사람 확인을 둔다.
- 장애는 푸시 → 접속 → 인증 → 명령 결과 → 비동기 결과 순서로 좁힌다.

## 참고

- [Apple Push Certificates Portal](https://identity.apple.com/pushcert/)
- [Apple Platform Deployment 가이드](https://support.apple.com/guide/deployment/welcome/web)
- [Apple: 기업 네트워크에서 Apple 제품 사용하기 (필요한 호스트와 포트)](https://support.apple.com/HT210060)
- [micromdm/nanomdm](https://github.com/micromdm/nanomdm)
- [apple/device-management](https://github.com/apple/device-management)
