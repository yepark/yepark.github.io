---
title: "MDM 프로파일과 정책 프로파일"
description: "기기를 MDM 서버에 묶는 com.apple.mdm 페이로드의 키(ServerURL, Topic, AccessRights 비트, ServerCapabilities, 피닝)와 바꿀 수 없는 값, 그리고 암호 정책·제한 프로파일의 키와 감독·사용자 등록 조건을 Apple 공식 스키마로 검사한 Python 예제로 설명합니다."
parent: Apple MDM
grand_parent: iOS
nav_order: 8
permalink: /ios/mdm/mdm-policy-profiles/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, MDM, Configuration-Profile, Passcode, Restrictions]
---

# MDM 프로파일과 정책 프로파일
{: .no_toc }

{% include article-toc.md %}

회사 iPhone에 설치되는 프로파일은 두 가지 역할로 나뉜다.

- **MDM 프로파일**: "이 기기는 이 서버가 관리한다"는 계약서다. 기기를 서버에 묶는다.
- **정책 프로파일**: "암호는 6자리 이상", "회사 문서는 개인 앱으로 못 보낸다" 같은 규칙집이다.

계약서가 먼저 있어야 규칙집을 보낼 수 있고, 계약서를 찢으면 그 계약으로 받은 규칙집도 함께 사라진다. 이 글은 이 두 가지를 키 하나하나까지 살펴본다. 프로파일의 일반 구조, 공통 키, 설치·제거 명령, 서명은 [3편]({{ '/ios/mdm/profiles/' | relative_url }})에서 다뤘으므로 여기서는 반복하지 않는다.

{: .note }
이 글의 키 이름, 타입, 범위, 지원 OS 버전, 감독 여부는 Apple이 공개한 스키마 저장소 [apple/device-management](https://github.com/apple/device-management)의 `release` 브랜치(커밋 `9e7fdbe`, 2026-10-26, README 기준 iOS 27.2에 대응)의 YAML 파일을 직접 읽어 확인했다. 예제 프로파일은 실제 기기에 설치해 보지 않았다. 기기 동작에 대한 설명은 Apple 문서에 적힌 내용이다.

## 먼저 결과부터: 프로파일 네 개

이 글의 예제 스크립트는 프로파일 네 개와 DDM 선언 하나를 만든다.

| 파일 | 역할 | 감독 필요 |
| --- | --- | --- |
| `enroll.mobileconfig` | MDM 프로파일 (서버 CA + 기기 ID 인증서 + `com.apple.mdm`) | 아니오 |
| `passcode.mobileconfig` | 암호 정책 | 아니오 |
| `dlp.mobileconfig` | 데이터 유출 방지 제한 | 아니오 |
| `supervised.mobileconfig` | 회사 기기 전용 제한 | 일부 키가 감독 필요 |
| `passcode.settings.json` | 같은 암호 정책의 DDM 선언 | 아니오 |

Mac에서 실행하면 이렇게 나온다.

```text
$ python3 make_policy_profiles.py
AccessRights = 8191
wrote dlp.mobileconfig           1209 B
wrote enroll.mobileconfig        3035 B
wrote passcode.mobileconfig      1286 B
wrote passcode.settings.json     399 B
wrote supervised.mobileconfig    1201 B
out/enroll.mobileconfig: OK
out/passcode.mobileconfig: OK
out/dlp.mobileconfig: OK
out/supervised.mobileconfig: OK
```

마지막 네 줄은 macOS의 `plutil -lint`가 plist 형식을 검사한 결과다. 형식 검사만으로는 키 이름 오타를 잡지 못하므로, 스크립트에 Apple 스키마로 키를 검사하는 기능도 넣었다. 검사 결과는 각 절에서 보여 준다.

## MDM 프로파일: 기기와 서버의 계약서

### 무엇을 하나

`com.apple.mdm` 페이로드는 기기에게 세 가지를 알려 준다.

1. **어디로 가는가**: 명령을 받을 서버 주소(`ServerURL`)
2. **누가 깨우는가**: APNs 푸시 토픽(`Topic`)
3. **나는 누구인가**: 서버에 자신을 증명할 기기 ID 인증서(`IdentityCertificateUUID`)

**페이로드(payload)**는 프로파일 안에 들어가는 설정 한 덩어리다. 택배 상자(프로파일) 안의 물건 하나라고 생각하면 된다. MDM 프로파일 상자에는 보통 인증서 페이로드와 `com.apple.mdm` 페이로드가 함께 들어간다.

스키마의 페이로드 정보를 보면 iOS에서 이 페이로드는 `multiple: false`다. 기기 하나에 MDM 페이로드는 하나만 설치할 수 있다는 뜻이다. 한 기기를 두 MDM 서버가 동시에 관리할 수 없는 이유가 여기 있다.

### 예제 프로파일

스크립트가 만든 `enroll.mobileconfig`를 `plutil -p`로 펼친 결과다.

```text
$ plutil -p out/enroll.mobileconfig
{
  "PayloadContent" => [
    0 => {
      "PayloadCertificateFileName" => "mdm-ca.cer"
      "PayloadContent" => {length = 22, bytes = 0x3c44...}
      "PayloadIdentifier" => "com.example.mdm.ca"
      "PayloadType" => "com.apple.security.root"
      "PayloadUUID" => "1707CE9B-FF74-55FA-AE04-D1B939FC68FC"
      "PayloadVersion" => 1
    }
    1 => {
      "PayloadContent" => {
        "Challenge" => "<one-time challenge>"
        "Key Type" => "RSA"
        "Keysize" => 2048
        "Subject" => [ [ [ "CN", "device-identity" ] ] ]
        "URL" => "https://mdm.example.com/scep"
      }
      "PayloadIdentifier" => "com.example.mdm.identity"
      "PayloadType" => "com.apple.security.scep"
      "PayloadUUID" => "54D22D19-6F4B-51B0-9C6B-AF13713EB96C"
      "PayloadVersion" => 1
    }
    2 => {
      "AccessRights" => 8191
      "CheckInURL" => "https://mdm.example.com/mdm/checkin"
      "CheckInURLPinningCertificateUUIDs" => [
        0 => "1707CE9B-FF74-55FA-AE04-D1B939FC68FC"
      ]
      "CheckOutWhenRemoved" => 1
      "IdentityCertificateUUID" => "54D22D19-6F4B-51B0-9C6B-AF13713EB96C"
      "PayloadIdentifier" => "com.example.mdm.payload"
      "PayloadType" => "com.apple.mdm"
      "PayloadUUID" => "4D22AEAF-B4C4-54A5-AFFB-1DC035C8FA06"
      "PayloadVersion" => 1
      "ServerCapabilities" => [
        0 => "com.apple.mdm.per-user-connections"
        1 => "com.apple.mdm.bootstraptoken"
      ]
      "ServerURL" => "https://mdm.example.com/mdm/connect"
      "ServerURLPinningCertificateUUIDs" => [
        0 => "1707CE9B-FF74-55FA-AE04-D1B939FC68FC"
      ]
      "SignMessage" => 1
      "Topic" => "com.apple.mgmt.External.0000...0000"
    }
  ]
  "PayloadDisplayName" => "Example MDM 등록"
  "PayloadIdentifier" => "com.example.mdm"
  ...
}
```

(긴 줄 몇 개는 화면에 맞게 줄였다.) 화살표처럼 이어지는 UUID를 따라가 보자.

- `IdentityCertificateUUID`의 값은 SCEP 페이로드(1번)의 `PayloadUUID`와 같다. "기기 ID는 이 SCEP로 받은 인증서를 쓴다"는 뜻이다.
- 두 피닝 배열의 값은 루트 인증서 페이로드(0번)의 `PayloadUUID`와 같다. "서버 인증서는 이 CA로만 믿는다"는 뜻이다.

{: .warning }
0번 페이로드의 `PayloadContent`는 자리 표시용 바이트(`<DER of MDM server CA>`)다. 실제로는 MDM 서버 TLS 인증서를 발급한 CA 인증서의 DER 바이트를 넣는다. 이 파일을 그대로 기기에 설치하면 안 된다.

### 키 하나하나

Apple 스키마 `mdm/profiles/com.apple.mdm.yaml`에 정의된 iOS 키를 정리했다. "필수"는 스키마의 `presence: required`다.

| 키 | 타입 | 필수 | 뜻 |
| --- | --- | --- | --- |
| `ServerURL` | 문자열 | 예 | 기기가 명령을 받으러 오는 주소. `https://`로 시작해야 하고 포트를 붙여도 된다 |
| `CheckInURL` | 문자열 | 아니오 | 설치·토큰 갱신·탈퇴를 알리는 주소. 없으면 `ServerURL`을 쓴다 |
| `Topic` | 문자열 | 예 | APNs 푸시 토픽. `com.apple.mgmt.`로 시작해야 하고, 푸시 인증서 subject의 토픽과 같아야 한다 |
| `IdentityCertificateUUID` | 문자열 | 예 | 기기 ID로 쓸 인증서 페이로드의 UUID. SCEP 페이로드를 가리켜도 된다 |
| `AccessRights` | 정수 | 아니오 | 서버에 허락할 권한의 비트 합 (아래 표) |
| `SignMessage` | 불리언 | 아니오 | `true`면 기기가 보내는 모든 메시지에 `Mdm-Signature` HTTP 헤더를 붙인다. 기본 `false` |
| `CheckOutWhenRemoved` | 불리언 | 아니오 | `true`면 프로파일이 지워질 때 `CheckInURL`로 `CheckOut` 메시지를 보내려고 시도한다. 기본 `false` |
| `ServerCapabilities` | 문자열 배열 | 아니오 | 서버가 지원하는 기능 목록 (아래 표) |
| `UseDevelopmentAPNS` | 불리언 | 아니오 | `true`면 개발용 APNs 서버를 쓴다. Apple Push Certificates Portal 인증서는 운영용만 발급하므로 `false`로 둔다 |
| `ServerURLPinningCertificateUUIDs` | 문자열 배열 | 아니오 | `.../connect/` 주소의 서버 인증서를 검증할 때 쓸 인증서 페이로드 UUID들. iOS 13.4+ |
| `CheckInURLPinningCertificateUUIDs` | 문자열 배열 | 아니오 | `.../checkin/` 주소용 같은 기능. iOS 13.4+ |
| `PinningRevocationCheckRequired` | 불리언 | 아니오 | `true`면 인증서 폐기 확인에서 확실한 "정상" 응답을 받지 못하면 연결을 실패시킨다. `false`(기본)면 폐기 확인 서버에 닿지 못해도 치명적 오류로 보지 않는다. iOS 13.4+ |
| `AssignedManagedAppleID` | 문자열 | 아니오 | 계정 기반 등록에서 인증한 사용자의 관리형 Apple 계정. 계정 기반 등록에는 필수. iOS 15+ |
| `EnrollmentMode` | 문자열 | 아니오 | 계정 기반 등록의 종류. `BYOD` 또는 `ADDE`. 계정 기반 등록에는 필수. iOS 15+ |
| `RequiredAppIDForMDM` | 정수 | 아니오 | 계정 기반 등록에서 사용자 승인 없이 설치할 수 있는 앱의 App Store ID. iOS 15.1+ |
| `ManagedAppleID` | 문자열 | 아니오 | 예전 프로파일 방식 사용자 등록용. iOS 17에서 deprecated, **iOS 18에서 제거** |

**피닝(pinning)**은 "이 CA가 발급한 인증서만 믿겠다"고 미리 못 박아 두는 것이다. 단골 가게 주인 얼굴을 외워 두고, 다른 사람이 같은 간판을 달아도 속지 않는 것과 같다. 자세한 원리는 [TLS 인증서 검증과 피닝]({{ '/pki/ssl-pinning/' | relative_url }})에서 다뤘다.

### AccessRights: 서버에 어디까지 허락할까

`AccessRights`는 권한마다 비트 하나를 배정하고, 허락할 권한의 값을 모두 더한(정확히는 비트 OR) 정수다. 전등 스위치 13개가 한 줄로 있고, 켠 스위치를 숫자 하나로 적는다고 생각하면 된다.

| 비트 | 허락하는 것 | 이 권한이 필요한 명령 예 |
| --- | --- | --- |
| 1 | 설치된 구성 프로파일 조회 | `ProfileList` |
| 2 | 구성 프로파일 설치·제거 | `InstallProfile`, `RemoveProfile` |
| 4 | 기기 잠금, 암호 제거 | `DeviceLock`, `ClearPasscode` |
| 8 | 기기 초기화 | `EraseDevice` |
| 16 | 기기 정보 조회 (용량, 일련번호) | |
| 32 | 네트워크 정보 조회 (전화·SIM 번호, MAC 주소) | |
| 64 | 프로비저닝 프로파일 조회 | |
| 128 | 프로비저닝 프로파일 설치·제거 | |
| 256 | 설치된 앱 조회 | `InstalledApplicationList` |
| 512 | 제한 관련 조회 | `Restrictions` |
| 1024 | 보안 관련 조회 | `SecurityInfo` |
| 2048 | 설정 변경 | `Settings` |
| 4096 | 앱 관리 | `InstallApplication` |

오른쪽 열은 `mdm/commands`의 각 명령 YAML에 적힌 `accessrights` 값(예: `ProfileList`는 `AllowInspection`, `InstallProfile`은 `AllowInstallationRemoval`, `SecurityInfo`는 `AllowQuerySecurity`)을 보고 짝지었다. `DeviceInformation`은 `Special`로 적혀 있어 한 비트에 짝짓지 않았다.

13개를 모두 더하면 `1 + 2 + 4 + ... + 4096 = 8191`이다. 스크립트도 `sum(ACCESS.values())`로 계산해 `AccessRights = 8191`을 출력했다.

스키마가 정한 규칙은 네 가지다.

- `0`으로 두지 않는다.
- `2`(설치·제거)를 켜면 `1`(조회)도 켠다.
- `128`을 켜면 `64`도 켠다.
- 프로파일을 업데이트할 때 **권한을 추가하면 오류**이고 업데이트가 거부된다.

{: .question }
처음에 `AccessRights`를 최소로 잡았다가 나중에 초기화(8) 권한이 필요해지면 어떻게 될까? 스키마에 따르면 업데이트로 권한을 추가할 수 없다. 그러니 처음 등록할 때 필요한 권한을 정해 두어야 한다.

사용자 등록에서는 이 키가 `mode: ignored`다. 기기가 이 값을 보지 않는다. 사용자 등록에서 서버가 할 수 있는 일은 운영체제가 따로 정한다([2편]({{ '/ios/mdm/enrollment/' | relative_url }}#4-사용자-등록-개인-기기byod)).

### ServerCapabilities: 서버가 할 줄 아는 것

스키마에 정의된 값은 세 개뿐이다.

| 값 | 뜻 |
| --- | --- |
| `com.apple.mdm.per-user-connections` | 서버가 기기 연결과 사용자 연결을 모두 지원한다. Shared iPad나 macOS를 관리할 때는 반드시 있어야 한다 |
| `com.apple.mdm.bootstraptoken` | 서버가 부트스트랩 토큰 보관(escrow)을 지원한다. 이 값이 있어야 기기가 부트스트랩 토큰을 만들어 서버에 보낸다. iOS 26+, macOS 11+, visionOS 26+ |
| `com.apple.mdm.token` | 서버가 `Get-Token` 체크인 메시지를 지원한다 |

DDM을 쓸 수 있다는 표시는 이 목록에 없다. DDM은 `DeclarativeManagement` 명령으로 켠다([6편]({{ '/ios/mdm/ddm/' | relative_url }})).

{: .warning }
업데이트 때 `com.apple.mdm.per-user-connections`를 넣거나 빼면 오류이고 업데이트가 거부된다. 나중에 Shared iPad를 관리할 계획이 있다면 처음부터 넣어 둔다.

### 업데이트할 때 바꿀 수 없는 값

MDM 프로파일도 같은 `PayloadIdentifier`로 다시 보내면 교체된다. 기기 ID 인증서를 갱신할 때 이렇게 한다([7편]({{ '/ios/mdm/operations/' | relative_url }})). 그런데 스키마에는 "업데이트 때 바뀌면 오류이고 거부된다"는 메모가 붙은 키가 있다.

| 키 | 업데이트 때 규칙 |
| --- | --- |
| `ServerURL`, `CheckInURL`, `Topic` | 값을 바꿀 수 없다 |
| `AssignedManagedAppleID`, `EnrollmentMode`, `RequiredAppIDForMDM` | 값을 바꿀 수 없다 |
| `AccessRights` | 권한을 추가할 수 없다 |
| `ServerCapabilities` | `per-user-connections`를 넣거나 뺄 수 없다 |

즉 서버 주소나 푸시 토픽을 바꾸려면 프로파일 업데이트로는 안 되고 기기를 다시 등록해야 한다.

{: .tip }
**실무에서는** `ServerURL`에 회사 도메인 아래의 전용 호스트 이름(예: `mdm.example.com`)을 쓰고, 그 뒤의 실제 서버나 클라우드 업체가 바뀌어도 DNS만 옮기는 편이 낫다고 본다. 주소 자체를 바꾸면 모든 기기를 다시 등록해야 하기 때문이다.

### 기기 ID 페이로드: SCEP, ACME, PKCS #12

`IdentityCertificateUUID`가 가리킬 수 있는 인증서 페이로드는 세 종류다. 스키마에서 확인한 필수 키와 지원 버전이다.

| 페이로드 | `PayloadType` | iOS | 필수 키 | 개인 키를 만드는 곳 |
| --- | --- | --- | --- | --- |
| SCEP | `com.apple.security.scep` | 4.0+ | `PayloadContent` 사전 안의 `URL` | 기기 |
| ACME | `com.apple.security.acme` | 16.0+ | `DirectoryURL`, `ClientIdentifier`, `KeySize`, `KeyType`, `HardwareBound`, `Subject` | 기기 |
| PKCS #12 | `com.apple.security.pkcs12` | 4.0+ | `PayloadContent` (데이터) | 서버 |

SCEP는 키 값들을 `PayloadContent` 사전 안에 넣고, ACME는 페이로드에 바로 넣는다는 점이 다르다. 예제는 [2편]({{ '/ios/mdm/enrollment/' | relative_url }})과 같은 SCEP를 썼다. PKCS #12는 서버가 만든 개인 키가 파일에 담겨 전송되므로, 기기가 키를 직접 만드는 SCEP나 ACME를 쓰는 것이 낫다는 점은 [3편]({{ '/ios/mdm/profiles/' | relative_url }}#서명과-민감-정보)에서 설명했다.

### 스키마로 검사한 결과

스크립트에 스키마 폴더를 넘기면 쓴 키마다 타입, iOS 도입 버전, 감독 필요 여부(`sup`), 사용자 등록에서의 처리(`UE`), deprecated 버전(`dep`)을 출력한다.

```text
$ python3 make_policy_profiles.py ~/device-management
...
## enroll.mobileconfig
- com.apple.security.root (iOS 4.0, multiple=True)
  PayloadCertificateFileName  <string>  iOS 4.0  sup=False UE=allowed dep=-
  PayloadContent              <data>    iOS 4.0  sup=False UE=allowed dep=-
- com.apple.security.scep (iOS 4.0, multiple=True)
  PayloadContent         <dictionary>   iOS 4.0  sup=False UE=allowed dep=-
- com.apple.mdm (iOS 4.0, multiple=False)
  ServerURL                   <string>  iOS 4.0  sup=False UE=allowed dep=-
  CheckInURL                  <string>  iOS 4.0  sup=False UE=allowed dep=-
  Topic                       <string>  iOS 4.0  sup=False UE=allowed dep=-
  IdentityCertificateUUID     <string>  iOS 4.0  sup=False UE=allowed dep=-
  AccessRights                <integer> iOS 4.0  sup=False UE=ignored dep=-
  CheckOutWhenRemoved         <boolean> iOS 4.0  sup=False UE=allowed dep=-
  SignMessage                 <boolean> iOS 4.0  sup=False UE=allowed dep=-
  ServerCapabilities          <array>   iOS 4.0  sup=False UE=allowed dep=-
  ServerURLPinningCertificateUUIDs  <array>  iOS 13.4 sup=False UE=allowed dep=-
  CheckInURLPinningCertificateUUIDs <array>  iOS 13.4 sup=False UE=allowed dep=-
```

(실제 출력은 열 너비가 일정한 한 줄이다. 화면에 맞게 공백을 줄였다.) `AccessRights`만 `UE=ignored`인 것이 앞의 설명과 맞는다.

{: .note }
스키마는 키마다 `supportedOS`를 따로 적지 않으면 페이로드 전체의 값을 물려받는다고 설명한다(`docs/schema.md`). 그래서 `ServerURL`처럼 따로 적지 않은 키는 페이로드의 iOS 4.0이 그대로 나온다. 검사 코드의 `ios_of()`가 이 규칙대로 두 값을 합친다.

### MDM 프로파일을 지우면

Apple Platform Deployment 가이드의 "Intro to device management" 페이지는 이렇게 설명한다.

> When a user removes an enrollment profile, all configurations, their settings, and managed apps based on that enrollment profile are removed with it.

같은 페이지에 "Removing the enrollment profile also removes associated configurations and legacy configuration profiles."라는 문장도 있다. 즉 계약서(MDM 프로파일)를 찢으면 그 계약으로 받은 정책 프로파일, DDM 구성, 관리형 앱이 함께 사라진다. `CheckOutWhenRemoved`가 `true`면 기기가 이때 서버에 `CheckOut`을 보내려고 **시도**하므로, 서버는 그 기기를 "관리 해제됨"으로 표시할 수 있다. "시도"이므로 네트워크가 끊겨 있으면 서버가 이 메시지를 받지 못할 수 있다.

ADE로 등록한 기기는 사용자가 등록 프로파일을 지울 수 있게 할지, 관리 서비스만 지울 수 있게 할지 고를 수 있다고 같은 페이지에 적혀 있다. 이 선택이 [2편]({{ '/ios/mdm/enrollment/' | relative_url }}#dep-api)의 `is_mdm_removable`이다.

### 등록 방식에 따라 무엇이 달라지나

`com.apple.mdm` 페이로드 자체는 어느 등록 방식이든 같다. 스키마에서 확인한 차이는 이렇다.

| | 프로파일 수동 등록 | ADE | 계정 기반 기기 등록 | 사용자 등록 (BYOD) |
| --- | --- | --- | --- | --- |
| `AccessRights` | 적용 | 적용 | 적용 | 무시됨 |
| `EnrollmentMode` | 쓰지 않음 | 쓰지 않음 | `ADDE` | `BYOD` |
| `AssignedManagedAppleID` | 쓰지 않음 | 쓰지 않음 | 필수 | 필수 |
| `RequiredAppIDForMDM` | 무시됨 | 무시됨 | 사용 가능 | 사용 가능 |
| 감독 모드 | 아니오 | 예 ([4편]({{ '/ios/mdm/commands/' | relative_url }})) | 아니오 | 아니오 |

`ADDE`는 Account-Driven Device Enrollment(계정 기반 기기 등록)의 줄임말이다. 감독 여부는 등록 방식이 정하고, 감독 여부가 다음 절의 제한 키 중 어떤 것이 적용되는지를 정한다.

## 정책 프로파일 1: 암호 정책

### 키와 범위

`com.apple.mobiledevice.passwordpolicy` 페이로드의 iOS 키다. 범위와 기본값은 스키마의 `range`, `default` 값이다.

| 키 | 타입 | 범위 | 기본값 | 뜻 |
| --- | --- | --- | --- | --- |
| `forcePIN` | 불리언 | | `false` | 암호 설정을 강제한다 |
| `allowSimple` | 불리언 | | `true` | `false`면 단순 암호(같은 문자 반복, `123`·`CBA`처럼 증가·감소)를 막는다 |
| `minLength` | 정수 | 0~16 | 0 | 최소 길이 |
| `requireAlphanumeric` | 불리언 | | `false` | 숫자만이 아니라 영문자도 요구한다 |
| `minComplexChars` | 정수 | 0~4 | 0 | 숫자·영문자가 아닌 문자(`&`, `%` 등)의 최소 개수 |
| `maxFailedAttempts` | 정수 | 2~11 | 11 | 이 횟수를 넘게 틀리면 iOS 기기의 모든 데이터와 설정을 안전하게 지운다 |
| `maxInactivity` | 정수 | 0~15 | | 자동 잠금까지의 최대 분. 사용자는 이 값 이하로만 고를 수 있다 |
| `maxGracePeriod` | 정수 | | 0 | 잠긴 뒤 암호 없이 풀 수 있는 최대 분. 0은 즉시 암호 요구 |
| `maxPINAgeInDays` | 정수 | 1~730 | | 이 날수가 지나면 암호를 바꿔야 잠금이 풀린다 |
| `pinHistory` | 정수 | 1~50 | | 최근 N개의 암호와 같은 암호를 쓸 수 없다 |

`maxFailedAttempts`에는 알아 둘 점이 있다. 6번 틀린 뒤부터 다시 입력하기까지 대기 시간이 생기고 점점 늘어난다. 그래서 값을 6 이하로 두면 대기 시간 없이 바로 초기화된다고 스키마에 적혀 있다.

{: .warning }
`maxFailedAttempts`는 "잠금"이 아니라 iOS에서는 **초기화**다. 어린 자녀가 기기를 만지거나 주머니 속에서 눌리는 일이 있는 환경이라면 너무 작은 값은 데이터 손실로 이어진다.

### 예제와 검사 결과

예제는 6자리 이상, 단순 암호 금지, 10번 실패 시 초기화, 자동 잠금 최대 5분, 유예 1분, 최근 3개 재사용 금지로 잡았다.

```python
PASSCODE = {
    "forcePIN": True, "allowSimple": False,
    "minLength": 6, "maxFailedAttempts": 10,
    "maxInactivity": 5, "maxGracePeriod": 1,
    "pinHistory": 3,
}
```

```text
## passcode.mobileconfig
- com.apple.mobiledevice.passwordpolicy (iOS 4.0, multiple=True)
  forcePIN           <boolean>  iOS 4.0  sup=False UE=ignored dep=27.0
  allowSimple        <boolean>  iOS 4.0  sup=False UE=ignored dep=27.0
  minLength          <integer>  iOS 4.0  sup=False UE=ignored dep=27.0
  maxFailedAttempts  <integer>  iOS 4.0  sup=False UE=ignored dep=27.0
  maxInactivity      <integer>  iOS 4.0  sup=False UE=ignored dep=27.0
  maxGracePeriod     <integer>  iOS 4.0  sup=False UE=ignored dep=27.0
  pinHistory         <integer>  iOS 4.0  sup=False UE=ignored dep=27.0
```

두 가지가 눈에 띈다.

1. **`dep=27.0`**: 이 페이로드 전체가 iOS 27.0에서 deprecated로 표시돼 있다. 저장소의 `CHANGES.md`에도 "Deprecated: mdm/profiles/com.apple.mobiledevice.passwordpolicy.yaml [iOS 27.0, macOS 27.0, visionOS 27.0, watchOS 27.0]"으로 적혀 있다. deprecated는 "아직 동작하지만 앞으로 쓰지 말라"는 표시이고, 제거(removed)와는 다르다.
2. **`UE=ignored`**: 사용자 등록 기기에서는 키 값을 무시한다. 대신 스키마 메모에 따르면 이 페이로드가 있기만 하면 `allowSimple`은 `false`, `forcePIN`은 `true`, `minLength`는 6으로 강제되고, `maxInactivity`가 있으면 값은 무시하되 설정의 "안 함" 선택지를 없앤다.

이 페이로드는 Shared iPad에서는 `forbidden`(설치 불가)이다.

## 정책 프로파일 2: 제한

### 제한 키를 목적별로 묶어 보기

`com.apple.applicationaccess`(제한) 페이로드에는 키가 많다. 스키마를 세어 보면 iOS에서 쓸 수 있는 키가 172개이고, 그중 117개가 감독 기기 전용, 37개가 deprecated다. 자주 쓰는 키를 목적별로 골랐다. 모든 키의 기본값은 "허용"(`allow...`는 `true`, `force...`·`require...`는 `false`)이다.

**데이터 유출 방지**: 회사 데이터가 개인 쪽으로 새지 않게 한다.

| 키 | iOS | 감독 | 사용자 등록 | 끄거나 켜면 |
| --- | --- | --- | --- | --- |
| `allowOpenFromManagedToUnmanaged` | 7.0+ | 아니오 | 가능 | `false`: 관리형 앱·계정의 문서는 관리형 앱·계정에서만 열린다 |
| `allowOpenFromUnmanagedToManaged` | 7.0+ | 아니오 | 가능 | `false`: 비관리 앱의 문서는 비관리 앱에서만 열린다 |
| `requireManagedPasteboard` | 15.0+ | 아니오 | 가능 | `true`: 위 두 제한이 복사·붙여넣기에도 적용된다 |
| `forceAirDropUnmanaged` | 9.0+ | 아니오 | 가능 | `true`: AirDrop을 비관리 대상으로 본다 |
| `allowAirDrop` | 7.0+ | **예** | 불가 | `false`: AirDrop을 끈다 |
| `allowScreenShot` | 3.1+ | 아니오 | 가능 | `false`: 스크린샷과 화면 녹화를 막고, 교실 앱의 화면 보기도 막는다 |
| `allowManagedAppsCloudSync` | 8.0+ | 아니오 | 가능 | `false`: 관리형 앱의 iCloud 동기화를 막는다 |
| `allowCloudBackup` | 5.0+ | 아니오* | 불가 | `false`: iCloud 백업을 끈다 |
| `allowCloudDocumentSync` | 5.0+ | **예** (iOS 13+) | 불가 | `false`: iCloud 문서·키값 동기화를 끈다 |
| `forceEncryptedBackup` | 4.0+ | 아니오 | 가능 | `true`: 모든 백업을 암호화한다 |

**관리형 앱(managed app)**은 MDM이 설치한 앱이다([5편]({{ '/ios/mdm/apps/' | relative_url }})). `allowOpenFromManagedToUnmanaged`는 회사 서류함과 개인 서류함 사이에 벽을 세우는 것과 같다. 회사 메일의 첨부 파일을 개인 클라우드 앱으로 넘기지 못한다.

**기기 기능**: 회사 기기에서 쓰지 않을 기능을 끈다.

| 키 | iOS | 감독 | 사용자 등록 | 끄면 |
| --- | --- | --- | --- | --- |
| `allowCamera` | 4.0+ | 아니오* | 불가 | 카메라를 끄고 홈 화면에서 아이콘을 없앤다 |
| `allowAppInstallation` | 4.0+ | **예** | 불가 | App Store를 없애고 앱 설치·업데이트를 막는다. Configurator·Xcode 설치와 다른 마켓플레이스 앱도 포함 |
| `allowUIAppInstallation` | 9.0+ | **예** | 불가 | App Store만 없앤다. 다른 경로 설치는 남는다. iOS 10부터 MDM 명령은 이 제한을 무시하고 설치할 수 있다 |
| `allowAppRemoval` | 4.2.1+ | **예** | 불가 | 앱 삭제를 막는다 |
| `allowAccountModification` | 7.0+ | **예** | 불가 | Apple 계정, 메일·연락처·캘린더 계정 변경을 막는다 |
| `allowSafari` | 4.0+ | **예** (iOS 13+) | 불가 | Safari와 웹 클립을 막는다 |
| `allowAssistant` | 5.0+ | 아니오 | 가능 | Siri를 끈다. **iOS 26.4에서 deprecated**, DDM `com.apple.configuration.siri.settings`를 쓰라고 적혀 있다 |

**보안**: 기기 자체를 지킨다.

| 키 | iOS | 감독 | 사용자 등록 | 값을 바꾸면 |
| --- | --- | --- | --- | --- |
| `allowEraseContentAndSettings` | 8.0+ | **예** | 불가 | `false`: 설정의 "모든 콘텐츠 및 설정 지우기"를 막는다 |
| `allowPasscodeModification` | 9.0+ | **예** | 불가 | `false`: 암호 추가·변경·제거를 막는다. Shared iPad에서는 무시 |
| `allowFingerprintForUnlock` | 7.0+ | 아니오* | 불가 | `false`: Touch ID·Face ID·Optic ID로 잠금 해제를 막는다 |
| `allowFingerprintModification` | 8.3+ | **예** | 불가 | `false`: Touch ID·Face ID 변경을 막는다 |
| `allowUSBRestrictedMode` | 11.4.1+ | **예** | 불가 | `false`: 잠긴 상태에서도 USB 액세서리가 **항상 연결된다** |
| `allowUntrustedTLSPrompt` | 5.0+ | 아니오 | 불가 | `false`: 신뢰할 수 없는 HTTPS 인증서를 묻지 않고 거부한다 |
| `allowEnterpriseAppTrust` | 9.0+ | 아니오 | 불가 | `false`: 설정의 "엔터프라이즈 개발자 신뢰" 버튼을 없앤다. 이미 준 신뢰는 취소하지 않는다 |
| `allowVPNCreation` | 11.0+ | **예** | 불가 | `false`: 관리형 앱만 VPN 구성을 만들 수 있다 |
| `allowHostPairing` | 7.0+ | **예** | 불가 | `false`: 감독 호스트 외의 컴퓨터와 페어링을 막는다 |

\* 표시한 키(`allowCamera`, `allowCloudBackup`, `allowFingerprintForUnlock`)는 지금은 감독 없이도 적용되지만, 스키마 설명에 "Support for this restriction on unsupervised devices is deprecated."라고 적혀 있다. 비감독 기기에서의 지원이 앞으로 없어질 수 있다는 뜻이다.

{: .warning }
`allowUSBRestrictedMode`는 이름과 반대로 움직이는 것처럼 보인다. 기본값 `true`가 "USB 제한 모드를 허용한다", 즉 잠긴 기기가 USB 액세서리를 막는 보안 기능이 켜진 상태다. `false`로 바꾸면 이 보호를 **끄는** 것이다. "제한 프로파일이니 다 `false`로" 하면 보안이 오히려 약해진다.

### 여러 제한 프로파일은 어떻게 합쳐지나

제한 페이로드는 스키마에서 `multiple: true`다. 여러 개를 설치할 수 있다. 그런데 "여러 개가 충돌하면 가장 엄격한 값이 이긴다"는 설명은 이번에 확인한 Apple 자료(스키마 YAML, Platform Deployment 가이드의 제한 페이지)에서 찾지 못했다. 스키마의 메모는 오히려 이렇게 경고한다.

> The system allows multiple Restrictions payloads. However, don't attempt to manage the same restriction in different payloads. Doing so results in unexpected behavior.

같은 제한 키를 서로 다른 페이로드에서 관리하지 말라는 것이다. Platform Deployment 가이드의 제한 페이지에서도 합치는 방법이 적힌 곳은 "Allow external intelligence workspace IDs" 한 줄뿐이었고, 그 키는 "intersect"(교집합)로 합친다고 적혀 있다.

그래서 예제 스크립트는 두 제한 프로파일(`dlp`, `supervised`)이 같은 키를 쓰지 않는지 검사한다(`extra_rules()`). 겹치면 오류로 출력한다.

### 예제와 검사 결과

감독 없이도 적용되는 키는 `dlp`에, 회사 기기 전용 키는 `supervised`에 나눠 담았다.

```text
## dlp.mobileconfig
- com.apple.applicationaccess (iOS 4.0, multiple=True)
  allowOpenFromManagedToUnmanaged <boolean> iOS 7.0  sup=False UE=allowed   dep=-
  requireManagedPasteboard        <boolean> iOS 15.0 sup=False UE=allowed   dep=-
  forceAirDropUnmanaged           <boolean> iOS 9.0  sup=False UE=allowed   dep=-
  allowManagedAppsCloudSync       <boolean> iOS 8.0  sup=False UE=allowed   dep=-
  allowUntrustedTLSPrompt         <boolean> iOS 5.0  sup=False UE=forbidden dep=-

## supervised.mobileconfig
- com.apple.applicationaccess (iOS 4.0, multiple=True)
  allowAirDrop                    <boolean> iOS 7.0  sup=True  UE=forbidden dep=-
  allowEraseContentAndSettings    <boolean> iOS 8.0  sup=True  UE=forbidden dep=-
  allowAccountModification        <boolean> iOS 7.0  sup=True  UE=forbidden dep=-
  allowEnterpriseAppTrust         <boolean> iOS 9.0  sup=False UE=forbidden dep=-
  allowCloudBackup                <boolean> iOS 5.0  sup=False UE=forbidden dep=-
```

검사 결과 덕분에 하나를 바로잡을 수 있다. `dlp`에 넣은 `allowUntrustedTLSPrompt`는 감독은 필요 없지만 사용자 등록에서는 `forbidden`이다. 개인 기기에도 `dlp` 프로파일을 보낼 계획이라면 이 키를 다른 프로파일로 옮겨야 한다.

### 사용자 등록에서 쓸 수 있는 제한

사용자 등록(개인 기기)에서는 대부분의 제한 키가 `forbidden`이다. 스키마를 세어 보면 iOS 키 172개 중 사용자 등록에서 `forbidden`이 아닌 키는 26개뿐이다. 이 글에 나온 키 중에서는 이것들이다.

- `allowOpenFromManagedToUnmanaged`, `allowOpenFromUnmanagedToManaged`, `requireManagedPasteboard`
- `forceAirDropUnmanaged`, `allowManagedAppsCloudSync`
- `allowScreenShot`, `forceEncryptedBackup`, `allowAssistant`

모두 "업무 데이터의 흐름"을 다루는 키다. Platform Deployment 가이드의 사용자 등록 페이지가 "Because the user owns the device, you can apply only a limited set of payloads and restrictions"라고 설명하는 그 "제한된 집합"을 스키마로 확인한 셈이다.

### 기기는 실수를 알려 주지 않는다

[3편]({{ '/ios/mdm/profiles/' | relative_url }})에서 말했듯 키 이름이 틀리면 기기는 대부분 조용히 무시한다. 그래서 스크립트에 일부러 틀린 값을 넣어 검사기가 잡는지 확인했다.

```python
bad = {
    "com.apple.applicationaccess":
        {"allowScreenshot": False},  # 대소문자 오타
    "com.apple.mobiledevice.passwordpolicy":
        {"minLength": 20,            # 범위 0~16
         "maxInactivity": "5"},      # 정수여야 함
}
```

```text
## 틀린 예제 검사
  com.apple.applicationaccess: 스키마에 없는 키 allowScreenshot
  com.apple.mobiledevice.passwordpolicy.minLength=20: 범위 {'min': 0, 'max': 16}
  com.apple.mobiledevice.passwordpolicy.maxInactivity: <integer> 아님
```

`allowScreenShot`의 `S` 하나가 소문자인 것을 사람 눈으로 찾기는 어렵다. 세 가지 모두 `plutil -lint`는 통과하는 파일이다.

## DDM으로 같은 정책 쓰기

[6편]({{ '/ios/mdm/ddm/' | relative_url }})의 DDM에는 암호 정책 구성 `com.apple.configuration.passcode.settings`가 있다. 스키마 기준 iOS 15.0부터 쓸 수 있고, 감독·기기·사용자·로컬 등록 모두에서 허용된다. 스크립트는 위의 암호 정책을 이 선언으로 옮겨 적는다.

```json
{
  "Type": "com.apple.configuration.passcode.settings",
  "Identifier": "com.example.passcode",
  "Payload": {
    "RequirePasscode": true,
    "MinimumLength": 6,
    "MaximumFailedAttempts": 10,
    "MaximumInactivityInMinutes": 5,
    "MaximumGracePeriodInMinutes": 1,
    "PasscodeReuseLimit": 3,
    "RequireComplexPasscode": true
  },
  "ServerToken": "9FD292C3-9DE3-5A7E-B4C5-18029434B451"
}
```

| 프로파일 키 | DDM 키 |
| --- | --- |
| `forcePIN` | `RequirePasscode` |
| `allowSimple: false` | `RequireComplexPasscode: true` |
| `minLength` | `MinimumLength` |
| `maxFailedAttempts` | `MaximumFailedAttempts` |
| `maxInactivity` | `MaximumInactivityInMinutes` |
| `maxGracePeriod` | `MaximumGracePeriodInMinutes` |
| `pinHistory` | `PasscodeReuseLimit` |
| `requireAlphanumeric` | `RequireAlphanumericPasscode` (iOS 16.2+) |
| `maxPINAgeInDays` | `MaximumPasscodeAgeInDays` (iOS 16.2+) |

두 스키마의 설명을 비교하면 `allowSimple`의 "단순 암호"(반복·증가·감소 문자)와 `RequireComplexPasscode`의 "복잡한 암호"는 같은 조건을 반대로 표현한 것이다.

DDM 쪽의 큰 차이는 **합치는 규칙이 키마다 적혀 있다**는 점이다. 검사 결과에 그대로 나온다.

```text
## com.apple.configuration.passcode.settings (iOS 15.0, apply=combined)
  RequirePasscode              combine=boolean-or
  MinimumLength                combine=number-max
  MaximumFailedAttempts        combine=number-min
  MaximumInactivityInMinutes   combine=number-min
  MaximumGracePeriodInMinutes  combine=number-min
  PasscodeReuseLimit           combine=number-min
  RequireComplexPasscode       combine=boolean-or

오류: 없음
```

`apply: combined`는 같은 종류의 선언이 여러 개면 합쳐서 적용한다는 뜻이다. 최소 길이는 큰 값(`number-max`), 실패 횟수와 잠금 시간은 작은 값(`number-min`), 불리언은 하나라도 `true`면 `true`(`boolean-or`)다. 결과적으로 이 키들은 더 엄격한 쪽으로 합쳐진다. 프로파일 방식에서는 이런 규칙을 찾지 못했던 것과 대비된다.

Apple의 방향은 스키마에 이렇게 나타나 있다.

- 암호 정책 프로파일 페이로드 전체가 iOS 27.0에서 deprecated다.
- 제한 키 중 Siri(`allowAssistant` 등)는 iOS 26.4에서 deprecated이고 DDM `siri.settings`를, 앱 허용·차단 목록(`allowListedAppBundleIDs`, `blockedAppBundleIDs`)은 iOS 27.0에서 deprecated이고 DDM `app.settings`를 쓰라고 적혀 있다.

## 실무에서는

여기부터는 Apple 문서가 아니라 글쓴이의 판단이다. 이유를 함께 적는다.

{: .tip }
**목적별로 프로파일을 나눈다.** 예제처럼 암호, 데이터 유출 방지, 회사 기기 제한을 따로 둔다. 이유는 세 가지다. (1) 하나를 고쳐도 다른 정책은 다시 설치되지 않는다. (2) 개인 기기에는 `passcode`와 `dlp`만, 회사 기기에는 셋 다 보내는 식으로 대상별로 조합할 수 있다. (3) 같은 제한 키를 두 페이로드에서 관리하지 말라는 Apple의 경고를 지키기 쉽다. 키마다 "주인 프로파일"이 하나씩 정해지기 때문이다.

{: .tip }
**`PayloadIdentifier`는 고정하고, `PayloadUUID`는 내용에서 만든다.** 식별자가 같아야 교체로 처리된다([3편]({{ '/ios/mdm/profiles/' | relative_url }})). 예제의 `stable_uuid()`는 식별자와 내용의 SHA-256 해시로 UUIDv5를 만든다. 같은 내용이면 몇 번을 다시 만들어도 같은 UUID가, 값이 하나라도 바뀌면 새 UUID가 나온다. 서버가 "이 기기에 설치된 UUID"와 비교만 해도 다시 보낼지 판단할 수 있다.

직접 확인한 결과다.

```text
6 com.example.policy.passcode.payload 0CAD59C8-D0FC-5CED-93F1-C5FF9AE20572
6 com.example.policy.passcode.payload 0CAD59C8-D0FC-5CED-93F1-C5FF9AE20572
8 com.example.policy.passcode.payload 7BEE1489-2800-557B-8DA1-FCE19E5B5BF8
```

`minLength`가 6일 때 두 번 만든 UUID는 같고, 8로 바꾸자 달라졌다.

{: .tip }
**제한은 천천히 넓힌다.** 먼저 감독된 테스트 기기 몇 대에 보내고, 다음으로 IT 팀처럼 작은 그룹, 그다음 전체로 넓힌다. `allowAccountModification: false`나 `allowAppInstallation: false`처럼 사용자가 하던 일을 막는 키는 문의가 몰리기 쉽고, `maxFailedAttempts`처럼 데이터를 지우는 키는 되돌릴 수 없기 때문이다. 문제가 생기면 그 목적의 프로파일 하나만 `RemoveProfile`로 거둬들인다.

{: .tip }
**테스트 기기는 감독 상태로 하나, 비감독으로 하나, 사용자 등록으로 하나 둔다.** 같은 제한 프로파일이 세 종류 기기에서 다르게 적용되기 때문이다. 이 글의 표는 스키마를 읽은 것이고, 이 글을 쓰면서 실제 기기로 확인하지는 않았다. 새 OS가 나오면 deprecated 표시가 바뀌므로 스키마 저장소의 `CHANGES.md`도 함께 본다.

{: .tip }
**설치 뒤에는 명령으로 확인한다.** 보낸 것과 기기에 있는 것이 같은지는 [4편]({{ '/ios/mdm/commands/' | relative_url }})의 조회 명령으로 본다.

| 명령 | 확인할 것 (스키마의 응답 키) |
| --- | --- |
| `ProfileList` | 설치된 프로파일마다 `PayloadIdentifier`, `PayloadUUID`, `IsManaged`, `PayloadRemovalDisallowed`. 서버가 기대한 UUID와 비교한다 |
| `SecurityInfo` | `PasscodePresent`(암호 있음), `PasscodeCompliant`(기기의 모든 요구 사항 충족), `PasscodeCompliantWithProfiles`(프로파일 요구 사항 충족), `ManagementStatus.IsUserEnrollment` |
| `Restrictions` | 지금 적용 중인 제한 |

`ProfileList`에는 `AccessRights`의 1번 비트가, `SecurityInfo`에는 1024번 비트가 필요하다. 앞에서 권한을 최소로 잡았다면 감사(audit) 명령이 거부될 수 있다는 뜻이다. 사용자 등록에서는 `PasscodePresent`와 `PasscodeCompliantWithProfiles`가 `forbidden`으로 표시돼 있어, `PasscodeCompliant`를 본다.

## 정리

- MDM 프로파일의 `com.apple.mdm` 페이로드는 서버 주소(`ServerURL`), 푸시 토픽(`Topic`), 기기 ID(`IdentityCertificateUUID`) 세 가지가 필수이고, 기기에 하나만 설치된다.
- `AccessRights`는 13개 권한의 비트 합(전부 8191)이다. 업데이트로 권한을 추가할 수 없고, 사용자 등록에서는 무시된다.
- `ServerURL`, `CheckInURL`, `Topic` 등은 업데이트로 바꿀 수 없다. 바꾸려면 다시 등록해야 한다.
- MDM 프로파일을 지우면 그 등록으로 받은 구성, 설정, 관리형 앱이 함께 지워진다.
- 암호 정책 페이로드는 범위가 정해진 정수 키가 많고, iOS 27.0에서 deprecated다. 사용자 등록에서는 키 값 대신 6자리 이상의 복잡한 암호만 강제된다.
- 제한 키 172개 중 117개는 감독 전용이고, 사용자 등록에서 쓸 수 있는 것은 26개다. 같은 제한 키를 여러 페이로드에서 관리하지 않는다.
- DDM 암호 구성은 키마다 합치는 규칙(`number-max`, `number-min`, `boolean-or`)이 정해져 있다.
- 목적별로 프로파일을 나누고, 식별자는 고정하고, 스키마로 키를 검사하고, `ProfileList`·`SecurityInfo`로 결과를 확인한다.

## 다음 편 예고

다음 편에서는 기기와 앱 라이선스, 관리형 Apple 계정을 한곳에서 다루는 Apple Business Manager와 Apple School Manager를 살펴본다.

## 실습 소스

- [make_policy_profiles.py]({{ '/assets/examples/ios/mdm/make_policy_profiles.py' | relative_url }}): MDM 프로파일, 암호·제한 프로파일, DDM 암호 선언을 만들고 `plutil -lint`로 검사한다. Apple 스키마 폴더를 인자로 주면 PyYAML로 키 이름·타입·범위·지원 OS·감독 여부를 검사한다

검사까지 실행하려면 스키마 저장소를 받고 PyYAML을 설치한다.

```bash
git clone --depth 1 https://github.com/apple/device-management
python3 -m venv venv && venv/bin/pip install pyyaml
venv/bin/python make_policy_profiles.py device-management
```

이 글의 출력은 macOS의 Python 3.9.6(만들기)과 Python 3.12.16 + PyYAML 6.0.4(검사)로 실행한 결과다.

## 참고

- [apple/device-management (GitHub)](https://github.com/apple/device-management): `mdm/profiles/com.apple.mdm.yaml`, `com.apple.mobiledevice.passwordpolicy.yaml`, `com.apple.applicationaccess.yaml`, `declarative/declarations/configurations/passcode.settings.yaml`, `mdm/commands/profile.list.yaml`, `information.security.yaml`
- [Apple Developer: MDM](https://developer.apple.com/documentation/devicemanagement/mdm)
- [Apple Developer: Passcode](https://developer.apple.com/documentation/devicemanagement/passcode)
- [Apple Developer: Restrictions](https://developer.apple.com/documentation/devicemanagement/restrictions)
- [Apple Platform Deployment: Intro to device management](https://support.apple.com/guide/deployment/intro-to-device-management-depc0aadd3fe/web)
- [Apple Platform Deployment: Restrictions for iPhone and iPad](https://support.apple.com/guide/deployment/restrictions-for-iphone-and-ipad-dep0f7dd3d8/web)
- [Apple Platform Deployment: Passcode payload settings](https://support.apple.com/guide/deployment/passcode-payload-settings-dep4d6a472a/web)
- [Apple Platform Deployment: User Enrollment and device management](https://support.apple.com/guide/deployment/user-enrollment-and-device-management-dep23db2037d/web)
