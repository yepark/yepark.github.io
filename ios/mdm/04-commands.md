---
title: "MDM 명령과 감독 모드"
description: "MDM 명령의 요청·응답 형식과 조회·보안·잠금·초기화·분실 모드 명령, 명령 대기열과 NotNow 처리, 감독(Supervised) 모드가 추가로 허용하는 관리 기능과 활성화 잠금 처리를 설명합니다."
parent: Apple MDM
grand_parent: iOS
nav_order: 4
permalink: /ios/mdm/commands/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, MDM, Supervision, Lost-Mode, Activation-Lock]
---

# MDM 명령과 감독 모드
{: .no_toc }

{% include article-toc.md %}

구성 프로파일이 "설정을 넣는" 수단이라면, **MDM 명령**은 기기에 "지금 이 일을 해라" 또는 "이 정보를 알려 달라"고 요청하는 수단이다. 기기 정보 조회, 앱 설치, 화면 잠금, 원격 초기화가 모두 명령이다. 이 글에서는 명령의 형식과 주요 명령, 그리고 명령의 범위를 넓혀 주는 **감독 모드**를 다룬다.

## 명령의 형식

[1편]({{ '/ios/mdm/architecture/' | relative_url }})에서 본 것처럼 명령은 기기가 `ServerURL`에 접속했을 때 응답으로 전달된다. 명령은 `CommandUUID`와 `Command` 사전으로 이루어진 plist다.

```xml
<dict>
  <key>CommandUUID</key>
  <string>0001-DEVINFO</string>
  <key>Command</key>
  <dict>
    <key>RequestType</key>
    <string>DeviceInformation</string>
    <key>Queries</key>
    <array>
      <string>DeviceName</string>
      <string>OSVersion</string>
      <string>SerialNumber</string>
      <string>IsSupervised</string>
      <string>BatteryLevel</string>
    </array>
  </dict>
</dict>
```

기기의 응답은 이런 모양이다(값은 예시).

```xml
<dict>
  <key>UDID</key>
  <string>00008110-000A1B2C3D4E801E</string>
  <key>CommandUUID</key>
  <string>0001-DEVINFO</string>
  <key>Status</key>
  <string>Acknowledged</string>
  <key>QueryResponses</key>
  <dict>
    <key>DeviceName</key>
    <string>영업팀 iPad 07</string>
    <key>IsSupervised</key>
    <true/>
    <key>OSVersion</key>
    <string>26.1</string>
    ...
  </dict>
</dict>
```

`CommandUUID`는 서버가 정하는 값이고, 응답을 원래 명령과 짝짓는 유일한 단서다. 서버는 이 값을 기준으로 "보냄 → 응답 받음 → 결과 저장" 상태를 관리한다.

## 주요 명령

### 조회

| 명령 | 돌려주는 것 |
| --- | --- |
| `DeviceInformation` | 이름, 모델, OS 버전, 일련번호, 감독 여부, 저장 공간, 배터리 등 (`Queries`로 고름) |
| `SecurityInfo` | 암호 설정 여부, 하드웨어 암호화, 방화벽(macOS), 관리 해제 가능 여부 |
| `InstalledApplicationList` | 설치된 앱 목록 (BYOD에서는 관리형 앱만) |
| `ProfileList` | 설치된 프로파일 |
| `CertificateList` | 설치된 인증서 |
| `Restrictions` | 현재 적용 중인 제한 |

### 보안·복구

| 명령 | 하는 일 | 조건 |
| --- | --- | --- |
| `DeviceLock` | 즉시 화면 잠금. 잠금 화면에 메시지·전화번호 표시 가능 | |
| `ClearPasscode` | 화면 잠금 암호 제거 | 등록 때 받은 `UnlockToken` 필요 |
| `EraseDevice` | 원격 초기화 | BYOD 불가 |
| `EnableLostMode` / `DisableLostMode` | 분실 모드. 기기를 잠그고 메시지 표시 | 감독 |
| `DeviceLocation` | 분실 모드 중 위치 조회 | 감독, 분실 모드 |
| `RestartDevice` / `ShutDownDevice` | 재시작·종료 | 감독 |

`ClearPasscode`에 필요한 `UnlockToken`은 기기가 `TokenUpdate` 체크인 때 한 번 보내 준다. 서버가 이 값을 저장해 두지 않으면 나중에 사용자가 암호를 잊었을 때 원격으로 풀어 줄 수 없다. 민감한 값이므로 암호화해 저장한다.

### 설정·앱

| 명령 | 하는 일 |
| --- | --- |
| `InstallProfile` / `RemoveProfile` | 구성 프로파일 설치·제거 ([3편]({{ '/ios/mdm/profiles/' | relative_url }})) |
| `InstallApplication` / `RemoveApplication` | 앱 설치·삭제 ([5편]({{ '/ios/mdm/apps/' | relative_url }})) |
| `Settings` | 기기 이름, 데이터 로밍, 개인용 핫스팟 등 개별 설정 변경 |
| `DeviceConfigured` | ADE 등록 중 `await_device_configured`로 멈춰 둔 설정 지원을 계속 진행시킴 |
| `DeclarativeManagement` | DDM 활성화 ([6편]({{ '/ios/mdm/ddm/' | relative_url }})) |

## 명령 대기열 설계

서버 입장에서 명령은 "보내면 끝"이 아니다. 기기가 꺼져 있을 수도, 잠겨 있을 수도, 응답 도중 연결이 끊길 수도 있다.

| 상황 | 처리 |
| --- | --- |
| 기기가 오래 접속하지 않음 | 명령은 대기열에 남는다. 일정 기간 후 만료시킬지 정책을 정한다 |
| `NotNow` 응답 | 기기가 지금 처리할 수 없다는 뜻(예: 잠금 상태에서 데이터 보호가 필요한 명령). 대기열에 남기고, 기기가 나중에 `Idle`로 다시 오면 재전송 |
| `Error` 응답 | `ErrorChain`의 도메인·코드를 기록한다. 같은 명령을 무한 반복하지 않는다 |
| 응답 전 연결 끊김 | 기기가 명령을 실행했는지 알 수 없다. 조회 명령은 다시 보내도 되지만, 초기화 같은 명령은 결과를 확인한 뒤 결정한다 |
| 같은 종류 명령이 쌓임 | 최신 하나만 남기는 식으로 합칠 수 있는 명령은 합친다 |

명령은 기기마다 **순서대로 하나씩** 처리된다. 대량 앱 설치처럼 오래 걸리는 명령이 앞에 있으면 뒤의 긴급 명령(잠금 등)이 늦어질 수 있으므로, 우선순위를 둘지 설계 단계에서 정한다.

## 감독 모드

### 무엇이 다른가

**감독(Supervised) 모드**는 "이 기기는 기관 소유"라고 운영체제에 표시된 상태다. 감독된 기기에서는 MDM이 개인 기기에서는 허용되지 않는 강한 관리를 할 수 있다.

| 감독 모드에서만 가능한 것 (예) |
| --- |
| 사용자 확인 없이 앱 설치(무음 설치) |
| App Store, AirDrop, 앱 삭제, 계정 변경 같은 기능 제한 |
| 분실 모드와 위치 조회 |
| 원격 재시작·종료 |
| 단일 앱 모드(키오스크처럼 앱 하나만 쓰게 하기) |
| 활성화 잠금 우회 코드 관리 |
| 소프트웨어 업데이트 강제와 지연 |

설정 > 일반 > 정보 상단에 "이 iPhone은 ○○이(가) 감독 및 관리합니다"라고 표시되면 감독 상태다.

### 감독 모드로 만드는 방법

1. **ADE로 등록**: iOS 13부터 ADE로 등록한 iPhone·iPad는 자동으로 감독된다. 가장 일반적인 방법이다.
2. **Apple Configurator로 준비**: Mac에 USB로 연결해 초기화하면서 감독 상태로 만든다. 이때 기기는 초기화된다.

이미 사용 중인 기기를 데이터를 유지한 채로 감독 상태로 바꿀 수는 없다. 감독은 기기를 처음 설정할 때 정해진다.

### 활성화 잠금

**활성화 잠금(Activation Lock)**은 나의 찾기가 켜진 기기를 초기화해도 원래 Apple 계정 암호 없이는 다시 쓸 수 없게 하는 도난 방지 기능이다. 직원이 개인 Apple 계정으로 나의 찾기를 켠 채 퇴사하면, 회사 기기가 잠겨 버린다.

감독된 기기에서는 MDM 서버가 **활성화 잠금 우회 코드**를 받아 둘 수 있다. 기기가 활성화 잠금을 걸 때 서버에 우회 코드를 알려 주고, 나중에 기기를 회수했을 때 이 코드로 잠금을 풀거나 초기화 명령에 함께 보낸다. 우회 코드를 받아 두지 않았다면 ABM에서 기관 소유를 증명하는 절차를 거쳐야 한다.

## BYOD에서는 무엇이 안 되나

[사용자 등록]({{ '/ios/mdm/enrollment/' | relative_url }}#4-사용자-등록-개인-기기byod)으로 등록된 개인 기기에서는 운영체제가 명령을 제한한다. `EraseDevice`, `DeviceLock`, `ClearPasscode`, 위치 조회 같은 기기 전체를 대상으로 하는 명령은 거부되고, 조회 결과에서도 일련번호나 개인 앱이 빠진다. 서버는 등록 종류를 기록해 두고, BYOD 기기에는 보낼 수 없는 명령을 처음부터 막는 것이 좋다.

## 정리

- 명령은 `CommandUUID`와 `RequestType`을 가진 plist이고, 응답은 같은 `CommandUUID`와 `Status`로 짝지어진다.
- 조회, 보안·복구, 설정·앱 명령이 있으며, 일부는 감독 모드나 `UnlockToken` 같은 조건이 필요하다.
- 서버는 기기별 명령 대기열을 두고 `NotNow`, `Error`, 연결 끊김을 각각 다르게 처리해야 한다.
- 감독 모드는 기관 소유 기기에 무음 앱 설치, 강한 제한, 분실 모드, 업데이트 강제 같은 권한을 준다. ADE 등록이나 Apple Configurator로만 만들 수 있다.
- 감독 기기는 활성화 잠금 우회 코드를 서버에 보관해 퇴사자 기기 잠김 문제를 막는다.

## 참고

- [Apple Developer: Commands and Queries](https://developer.apple.com/documentation/devicemanagement/commands-and-queries)
- [Apple Developer: Device Information](https://developer.apple.com/documentation/devicemanagement/device-information-command)
- [Apple Platform Deployment 가이드](https://support.apple.com/guide/deployment/welcome/web): 감독, 활성화 잠금, 분실 모드 항목
