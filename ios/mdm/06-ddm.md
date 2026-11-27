---
title: "DDM: 선언형 기기 관리"
description: "명령을 하나씩 보내는 대신 원하는 상태를 선언하고 기기가 스스로 적용·보고하는 Apple DDM(Declarative Device Management)의 구조를 설명합니다. 구성·자산·활성화·관리 선언, 동기화 토큰과 엔드포인트, 상태 채널, 소프트웨어 업데이트 강제, 기존 MDM에서 옮기는 순서를 JSON 예제로 다룹니다."
parent: Apple MDM
grand_parent: iOS
nav_order: 6
permalink: /ios/mdm/ddm/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, MDM, DDM, Declarative-Device-Management, Software-Update]
---

# DDM: 선언형 기기 관리
{: .no_toc }

{% include article-toc.md %}

기존 MDM으로 "모든 iPad의 OS를 26.2로 올리고, 다 올라갔는지 확인하라"는 일을 한다고 해 보자. 서버는 기기마다 OS 버전을 묻고, 업데이트 명령을 보내고, 다운로드가 끝났는지 다시 묻고, 설치 예약 명령을 보내고, 설치됐는지 또 묻는다. 기기 1만 대면 수만 번의 왕복이고, 그 사이 기기가 꺼지거나 잠기면 상태가 꼬인다.

**DDM(Declarative Device Management, 선언형 기기 관리)**은 이 방식을 뒤집는다. 서버는 "이 기기는 12월 15일 18시까지 OS 26.2여야 한다"는 **원하는 상태를 선언**만 한다. 기기는 그 선언을 받아 **스스로** 다운로드하고, 사용자에게 알리고, 기한에 맞춰 설치한다. 그리고 상태가 바뀔 때마다 **기기가 먼저** 서버에 보고한다. 서버는 묻지 않아도 된다.

| | 기존 MDM | DDM |
| --- | --- | --- |
| 서버가 보내는 것 | "지금 이걸 해라"(명령) | "이 상태여야 한다"(선언) |
| 실행 판단 | 서버가 조건을 보고 명령을 보낼지 정함 | 기기가 조건을 보고 스스로 적용 |
| 상태 파악 | 서버가 주기적으로 물어봄(폴링) | 기기가 바뀔 때 보고함 |
| 기기가 오프라인일 때 | 명령이 대기열에 쌓임 | 기기가 이미 가진 선언대로 계속 동작 |

SwiftUI의 선언형 UI와 생각이 같다. [SwiftUI]({{ '/swiftui/declarative-view/' | relative_url }})에서 "상태가 이러면 화면은 이렇다"를 적어 두면 프레임워크가 화면을 맞추듯, DDM에서는 "기기는 이래야 한다"를 적어 두면 운영체제가 기기를 맞춘다.

## 지원 현황

DDM은 iOS 15(사용자 등록 기기만)에서 처음 나왔고, iOS 16·macOS 13부터 모든 등록 방식에서 쓸 수 있다. 이후 매년 선언 종류가 늘고 있다. Apple은 WWDC에서 소프트웨어 업데이트처럼 DDM으로 옮긴 기능에 대해 기존 MDM 명령과 제한 키를 단계적으로 중단하겠다고 안내했다. 새로 만드는 MDM 서버라면 DDM을 기본으로 설계하고, 기존 명령은 DDM이 아직 다루지 않는 기능에만 쓰는 것이 현재의 방향이다. 기능별 지원 OS 버전은 해마다 바뀌므로 구현 전에 Apple 문서와 [apple/device-management](https://github.com/apple/device-management) 저장소의 스키마로 확인한다.

## 선언의 네 종류

모든 선언은 같은 바깥 모양을 가진 JSON이다.

```json
{
  "Type": "com.apple.configuration.passcode.settings",
  "Identifier": "com.example.passcode",
  "ServerToken": "119138a226732c70",
  "Payload": {
    "RequirePasscode": true,
    "MinimumLength": 6,
    "MaximumFailedAttempts": 10
  }
}
```

| 키 | 뜻 |
| --- | --- |
| `Type` | 선언 종류 |
| `Identifier` | 서버가 정하는 고유 이름. 다른 선언이 이 이름으로 참조한다 |
| `ServerToken` | 내용이 바뀔 때마다 바뀌는 값. 기기는 이 값이 달라졌을 때만 다시 받아 간다 |
| `Payload` | 실제 설정 |

선언은 역할에 따라 네 종류로 나뉜다.

| 종류 | `Type` 접두사 | 역할 | 예 |
| --- | --- | --- | --- |
| 구성(Configuration) | `com.apple.configuration.` | 기기에 적용할 정책 | 암호 정책, 소프트웨어 업데이트, 계정, 레거시 프로파일 |
| 자산(Asset) | `com.apple.asset.` | 구성이 참조하는 데이터 | 인증서·자격 증명, 사용자 정보, 데이터 파일 |
| 활성화(Activation) | `com.apple.activation.` | 어떤 구성을 **언제** 적용할지 묶는 것 | "iPad이면 이 구성들을 켠다" |
| 관리(Management) | `com.apple.management.` | 서버·조직 정보 | 서버 기능, 조직 정보, 속성 |

중요한 점은 **구성은 혼자서는 적용되지 않는다**는 것이다. 구성은 활성화가 참조해야 켜진다. 구성(무엇을)과 활성화(언제)를 분리해, 같은 구성을 여러 조건에 재사용할 수 있게 했다.

### 활성화와 조건

```json
{
  "Type": "com.apple.activation.simple",
  "Identifier": "com.example.activation.ipad",
  "ServerToken": "7f366f4ba9f10bf8",
  "Payload": {
    "StandardConfigurations": [
      "com.example.passcode",
      "com.example.os-update",
      "com.example.status"
    ],
    "Predicate": "@status(device.model.family) == 'iPad'"
  }
}
```

`StandardConfigurations`에 나열한 구성들이 이 활성화로 켜진다. `Predicate`는 조건식이며, `@status(...)`로 기기의 상태 항목을 읽어 판단한다. 조건을 판단하는 것은 **기기**다. 서버가 기기 종류를 먼저 조회해 골라 보낼 필요가 없다. 기기의 상태가 바뀌어 조건이 참이 되거나 거짓이 되면 기기가 알아서 구성을 켜고 끈다.

### 소프트웨어 업데이트 강제

DDM이 가장 큰 차이를 만드는 곳이 OS 업데이트다.

```json
{
  "Type": "com.apple.configuration.softwareupdate.enforcement.specific",
  "Identifier": "com.example.os-update",
  "ServerToken": "79a3a259a5ef1564",
  "Payload": {
    "TargetOSVersion": "26.2",
    "TargetLocalDateTime": "2026-12-15T18:00:00",
    "DetailsURL": "https://it.example.com/os-update"
  }
}
```

기기는 이 선언을 받으면 해당 버전을 미리 내려받고, 기한이 다가오면 사용자에게 알림을 띄우며, 기한(기기의 현지 시각 기준)이 되면 설치를 진행한다. `DetailsURL`은 알림에서 사용자가 누를 사내 안내 페이지다. 기존 MDM의 `ScheduleOSUpdate` 명령과 업데이트 지연 제한은 이 방식으로 대체되고 있다.

### 레거시 프로파일 구성

모든 설정이 DDM 선언으로 나와 있지는 않다. `com.apple.configuration.legacy` 구성은 기존 [구성 프로파일]({{ '/ios/mdm/profiles/' | relative_url }})의 URL을 가리켜, 기기가 그 프로파일을 내려받아 설치하게 한다. 기존 프로파일을 버리지 않고도 활성화 조건과 상태 보고 같은 DDM의 장점을 쓸 수 있어 이전 단계에서 유용하다.

## 동기화: 기기가 선언을 가져가는 방법

DDM도 기존 MDM 연결 위에서 시작한다.

1. 서버가 기존 MDM 명령 `DeclarativeManagement`를 보내 DDM을 켠다.
2. 이후 기기는 **체크인 엔드포인트**에 `MessageType`을 `DeclarativeManagement`로, `Endpoint`를 아래 값 중 하나로 정해 요청한다.

| Endpoint | 기기가 묻는 것 | 서버가 돌려주는 것 |
| --- | --- | --- |
| `tokens` | "바뀐 게 있나?" | 동기화 토큰 |
| `declaration-items` | "지금 선언 목록은?" | 선언별 `Identifier`와 `ServerToken` 목록 |
| `declaration/<종류>/<Identifier>` | "이 선언 내용을 달라" | 선언 JSON 하나 |
| `status` | (기기가 상태를 보냄) | 받았다는 응답 |

토큰 응답과 목록 응답은 이런 모양이다.

```json
{
  "SyncTokens": {
    "DeclarationsToken": "3b4b7db24416943b",
    "Timestamp": "2026-11-27T09:00:00Z"
  }
}
```

```json
{
  "Declarations": {
    "Activations": [
      { "Identifier": "com.example.activation.ipad", "ServerToken": "7f366f4ba9f10bf8" }
    ],
    "Configurations": [
      { "Identifier": "com.example.passcode", "ServerToken": "119138a226732c70" },
      { "Identifier": "com.example.os-update", "ServerToken": "79a3a259a5ef1564" },
      { "Identifier": "com.example.status", "ServerToken": "95fd04e9d78a88fb" }
    ],
    "Assets": [],
    "Management": []
  },
  "DeclarationsToken": "3b4b7db24416943b"
}
```

기기는 `DeclarationsToken`이 지난번과 같으면 아무것도 하지 않는다. 다르면 목록을 받아, `ServerToken`이 바뀐 선언만 새로 가져온다. 목록에서 사라진 선언은 기기에서 제거한다.

서버 쪽에서 선언을 바꾼 뒤 기기에 알리려면 `DeclarativeManagement` 명령을 다시 보내거나, 동기화 토큰을 담아 푸시를 유발한다. 위 예제의 `ServerToken`은 선언 내용의 해시로 만들었다. 내용이 같으면 같은 값이 나와 불필요한 재전송을 막을 수 있다.

## 상태 채널: 묻지 않아도 알려 준다

기존 MDM에서는 서버가 `DeviceInformation` 같은 명령으로 상태를 물어야 했다. DDM에서는 서버가 **구독할 상태 항목**을 선언해 두면, 기기가 그 값이 바뀔 때마다 `status` 엔드포인트로 보고한다.

```json
{
  "Type": "com.apple.configuration.management.status-subscriptions",
  "Identifier": "com.example.status",
  "Payload": {
    "StatusItems": [
      { "Name": "device.operating-system.version" },
      { "Name": "softwareupdate.install-state" },
      { "Name": "passcode.is-compliant" }
    ]
  }
}
```

기기는 구독한 항목이 바뀌면 상태 보고를 보낸다. 보고에는 상태 값과 함께 각 선언이 **유효한지, 적용됐는지, 오류가 났는지**가 들어 있다. 예를 들어 암호 정책을 만족하지 않는 기기는 `passcode.is-compliant`가 `false`로 보고되고, 서버는 그 기기를 규정 미준수로 표시해 사내 시스템 접근을 막는 식으로 활용한다.

## 기존 MDM에서 옮기는 순서

1. **DDM 켜기**: 등록 직후 `DeclarativeManagement` 명령을 보낸다. DDM을 지원하지 않는 OS 버전의 기기는 기존 방식으로 둔다.
2. **상태 구독부터**: 폴링하던 정보(OS 버전, 암호 준수 등)를 상태 구독으로 옮긴다. 서버 부하가 가장 먼저 줄어든다.
3. **소프트웨어 업데이트**: 기존 업데이트 명령을 업데이트 강제 선언으로 바꾼다. Apple이 중단을 예고한 영역이라 우선순위가 높다.
4. **나머지 설정**: 같은 기능의 DDM 선언이 있으면 옮기고, 없으면 레거시 프로파일 구성으로 감싸 활성화 조건을 붙인다.
5. **명령은 남는 곳에만**: 잠금, 초기화, 분실 모드처럼 "지금 한 번 하는" 행동은 계속 MDM 명령으로 한다. DDM은 지속돼야 하는 상태를 위한 것이다.

## 정리

- DDM은 명령 대신 원하는 상태를 선언하고, 기기가 스스로 적용하고 바뀐 상태를 먼저 보고하는 방식이다.
- 선언은 구성(무엇을), 자산(구성이 쓰는 데이터), 활성화(언제), 관리(서버 정보) 네 종류이며, 구성은 활성화가 참조해야 켜진다.
- 활성화의 `Predicate`는 기기가 판단하므로 서버가 기기를 미리 골라 보낼 필요가 없다.
- 기기는 동기화 토큰과 `ServerToken`을 비교해 바뀐 선언만 가져간다.
- 상태 구독으로 서버의 폴링을 없앨 수 있다.
- OS 업데이트는 DDM 업데이트 강제 선언으로 옮기는 것이 현재 Apple의 방향이다. 잠금·초기화 같은 일회성 행동은 계속 MDM 명령으로 한다.

## 실습 소스

- [make_declarations.py]({{ '/assets/examples/ios/mdm/make_declarations.py' | relative_url }}): 위 선언, 목록, 동기화 토큰 JSON을 만든다

## 참고

- [Apple Developer: Declarative Device Management](https://developer.apple.com/documentation/devicemanagement/leveraging-the-declarative-management-data-model-to-scale-devices)
- [apple/device-management (GitHub)](https://github.com/apple/device-management): 선언·페이로드 스키마의 공식 YAML
- [WWDC23: Explore advances in declarative device management](https://developer.apple.com/videos/play/wwdc2023/10041/)
- [WWDC21: Meet declarative device management](https://developer.apple.com/videos/play/wwdc2021/10131/)
