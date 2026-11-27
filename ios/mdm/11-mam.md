---
title: "MAM: 기기 대신 앱과 업무 데이터 관리하기"
description: "MDM과 MAM(Mobile Application Management)의 차이, BYOD에서 MAM이 필요한 이유, Apple의 관리형 앱·Managed Open In·관리형 붙여넣기·앱별 VPN·앱 구성과 피드백·DDM 앱 선언과 ManagedApp 프레임워크, Intune 앱 보호 정책(MAM-WE), AppConfig, Android 관리형 구성과 업무 프로필, 선택적 초기화를 공식 문서와 스키마로 정리하고 UserDefaults로 앱 구성을 읽는 Swift 예제를 실행합니다."
parent: Apple MDM
grand_parent: iOS
nav_order: 11
permalink: /ios/mdm/mam/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, MDM, MAM, Managed-Open-In, Managed-App-Configuration, Intune, AppConfig]
---

# MAM: 기기 대신 앱과 업무 데이터 관리하기
{: .no_toc }

{% include article-toc.md %}

직원이 자기 iPhone으로 회사 메일을 보고 싶다고 하자. 회사는 메일 첨부 파일이 개인 클라우드나 개인 메신저로 새어 나가는 것을 막고 싶다. 하지만 직원은 회사가 자기 휴대폰 전체를 관리하는 것이 싫다. 사진, 개인 앱, 위치는 회사가 상관할 일이 아니다.

이 둘을 같이 만족시키는 방법이 **MAM(Mobile Application Management, 모바일 앱 관리)**이다. MAM은 기기 전체가 아니라 **업무 앱과 그 안의 업무 데이터만** 관리한다.

{: .tip }
아파트에 비유하면, MDM은 건물 관리인이 집 전체 열쇠를 갖는 것이고, MAM은 회사가 집 안에 놓아 둔 **금고 하나의 열쇠만** 갖는 것이다. 금고 안의 서류는 회사 규칙을 따르고, 금고 밖의 생활은 집주인 마음이다.

| | MDM | MAM |
| --- | --- | --- |
| 관리 단위 | 기기 전체 | 앱과 앱 안의 업무 데이터 |
| 기기 등록 | 필요 | 방식에 따라 필요 없음 |
| 대표 기능 | 기기 암호 정책, Wi-Fi·VPN, 기기 잠금·초기화 | 앱 PIN, 복사·붙여넣기 제한, 다른 이름으로 저장 제한, 업무 데이터만 지우기 |
| 잘 맞는 기기 | 회사 소유 기기 | 개인 기기(BYOD) |

**BYOD(Bring Your Own Device)**는 직원이 자기 기기를 업무에 쓰는 방식이다. MDM·MAM·EMM·UEM이 서로 어떤 관계인지 큰 그림은 [10편 UEM]({{ '/ios/mdm/uem/' | relative_url }})에 정리했다. 이 글은 그중 MAM만 깊게 본다.

MAM을 구현하는 방법은 크게 두 갈래다.

1. **운영체제가 제공하는 앱 단위 관리.** Apple은 MDM에 등록된 기기에서 "관리형 앱"과 "비관리 앱" 사이에 경계를 긋는다. 기기는 등록하지만, 개인 기기라면 [사용자 등록]({{ '/ios/mdm/enrollment/' | relative_url }})으로 업무 영역만 관리한다.
2. **앱 안에 넣은 SDK로 하는 관리.** Microsoft Intune 앱 보호 정책처럼 앱에 넣은 라이브러리가 정책을 받아 스스로 지킨다. 기기 등록이 없어도 된다.

## Apple의 앱 단위 관리

[5편]({{ '/ios/mdm/apps/' | relative_url }})에서 앱 라이선스, `InstallApplication`, 관리형 앱 구성의 기본을 다뤘다. 여기서는 "관리형 앱"이라는 경계가 실제로 무엇을 막고 지우는지를 본다.

### 관리형과 비관리: 경계부터

**관리형 앱(managed app)**은 MDM이 설치했거나 MDM이 관리를 넘겨받은 앱이다. 관리형 계정(MDM이 설정한 메일 계정 등)도 같은 편에 선다. 사용자가 App Store에서 직접 받은 앱과 손으로 추가한 계정은 **비관리**다.

Apple의 모든 앱 단위 제한은 이 경계를 기준으로 동작한다. "업무 데이터"를 따로 표시하는 것이 아니라, **어느 앱·계정에서 왔는가**로 업무 데이터인지 정한다.

### 관리형 앱을 지우면 데이터도 지워진다

관리형 앱을 기기에서 없애는 길은 세 가지다.

| 상황 | 동작 | 근거 |
| --- | --- | --- |
| 서버가 `RemoveApplication` 명령을 보냄 | 앱과 앱 데이터를 함께 지움 | `RemoveApplication` 스키마 설명 |
| MDM 관리 해제(프로파일 제거) | `InstallApplication`의 `ManagementFlags`가 `1`이면 앱 삭제 | [5편]({{ '/ios/mdm/apps/' | relative_url }}) |
| 계정 기반 등록(사용자 등록 포함)의 관리 해제 | 관리형 앱을 **항상** 지움 | Apple Platform Deployment 가이드 |

반대로 사용자가 마음대로 지우지 못하게 할 수도 있다. `InstallApplication`의 `Attributes` 안에 `Removable`을 `false`로 넣으면(iOS 14부터), 그 앱이 관리형인 동안 사용자가 삭제할 수 없다. DDM 앱 선언에서는 `InstallBehavior.Install`을 `Required`로 두면 같은 효과가 난다(아래에서 다룬다).

{: .note }
지우는 대상이 **앱 단위**라는 점이 MAM의 핵심이다. 기기 전체를 초기화하지 않고 업무 앱과 그 데이터만 걷어 낼 수 있다.

### Managed Open In: 업무 문서가 개인 앱으로 가지 않게

**Managed Open In**은 관리형 앱·계정과 비관리 앱·계정 사이에서 문서가 오가는 방향을 정하는 기능이다. 공유 시트의 "다른 앱에서 열기"를 생각하면 된다. 회사 메일 첨부 파일을 개인 클라우드 앱으로 여는 길을 막는다.

설정은 [구성 프로파일]({{ '/ios/mdm/profiles/' | relative_url }})의 제한(`com.apple.applicationaccess`) 페이로드에 들어간다. 아래 키와 버전은 Apple의 공식 스키마 저장소 [apple/device-management](https://github.com/apple/device-management)의 `mdm/profiles/com.apple.applicationaccess.yaml`에서 확인한 값이다.

| 키 | 기본값 | iOS | 뜻 |
| --- | --- | --- | --- |
| `allowOpenFromManagedToUnmanaged` | `true` | 7.0 | `false`면 관리형 앱·계정의 문서는 다른 관리형 앱·계정에서만 열린다 |
| `allowOpenFromUnmanagedToManaged` | `true` | 7.0 | `false`면 비관리 앱·계정의 문서는 다른 비관리 앱·계정에서만 열린다 |
| `requireManagedPasteboard` | `false` | 15.0 | `true`면 위 두 제한이 복사·붙여넣기에도 적용된다 |
| `forceAirDropUnmanaged` | `false` | 9.0 | `true`면 AirDrop을 비관리 목적지로 본다 |
| `allowManagedToWriteUnmanagedContacts` | `false` | 12.0 | `true`면 관리형 앱이 비관리 연락처 계정에 쓸 수 있다 |
| `allowUnmanagedToReadManagedContacts` | `false` | 12.0 | `true`면 비관리 앱이 관리형 연락처 계정을 읽을 수 있다 |
| `allowManagedAppsCloudSync` | `true` | 8.0 | `false`면 관리형 앱의 iCloud 동기화를 막는다 |

연락처 두 키는 `allowOpenFromManagedToUnmanaged`가 `true`이면 효과가 없다고 스키마에 적혀 있다. 즉 Open In을 먼저 막아야 연락처 예외를 의미 있게 쓸 수 있다.

업무 데이터가 개인 쪽으로 나가는 것만 막는 가장 작은 제한 프로파일 조각은 이렇다.

```xml
<dict>
  <key>PayloadType</key>
  <string>com.apple.applicationaccess</string>
  <key>allowOpenFromManagedToUnmanaged</key>
  <false/>
  <key>requireManagedPasteboard</key>
  <true/>
  <key>forceAirDropUnmanaged</key>
  <true/>
</dict>
```

Apple Platform Deployment 가이드는 이 제한에 대해 다음 내용을 더 적고 있다.

- 관리형 앱에 들어 있는 **확장(extension)**도 같은 Managed Open In 설정을 따른다.
- **타사 키보드 확장**에도 적용된다. 비관리 키보드가 관리형 앱 위에 뜨지 않게 할 수 있다.
- **관리형 도메인**에서 Safari로 받은 파일은 관리형 문서로 취급된다.
- 관리형 붙여넣기는 관리형과 비관리 목적지 사이의 붙여넣기를 제어하며, iOS 16·iPadOS 16.1부터는 관리형 도메인도 포함한다.

{: .warning }
Apple 문서가 설명하는 제한 대상은 문서 열기, 공유 확장, 붙여넣기, AirDrop, 키보드 확장 같은 **운영체제가 중개하는 통로**다. 관리형 앱이 자기 코드로 데이터를 외부 서버에 올리는 경로는 이 목록에 없다. 그 부분은 앱 자체가 책임져야 한다.

### 앱별 VPN

**앱별 VPN(per-app VPN)**은 VPN을 기기 전체가 아니라 지정한 앱의 트래픽에만 쓰는 기능이다. 개인 기기에서 개인 앱 트래픽까지 회사 VPN으로 보내지 않아도 된다.

연결 방법은 두 단계다.

1. App-Layer VPN 페이로드(`com.apple.vpn.managed.applayer`)를 설치한다. 일반 VPN 페이로드와 같은 필드에 `VPNUUID`가 더해진 형태이고, `VPNUUID`는 필수다.
2. 앱을 설치할 때 `InstallApplication`의 `Attributes.VPNUUID`에 같은 UUID를 넣는다. DDM 앱 선언의 `Attributes`에도 `VPNUUID`가 있다.

같은 `Attributes`에는 `ContentFilterUUID`, `DNSProxyUUID`(iOS 16부터), `RelayUUID`(iOS 17부터)도 있어서 앱별 콘텐츠 필터, DNS 프록시, 네트워크 릴레이도 같은 방식으로 앱에 묶는다.

### 앱 구성과 피드백: 서버와 앱이 주고받는 사전

[5편]({{ '/ios/mdm/apps/' | relative_url }})에서 본 것처럼 MDM은 앱의 `UserDefaults` 안 `com.apple.configuration.managed` 키에 사전을 넣고, 앱은 `com.apple.feedback.managed` 키에 사전을 써서 서버에 상태를 알린다. 이 방식은 2013년 Apple 샘플 코드 ManagedAppConfig(iOS 7)에 처음 나왔다.

서버 쪽에서 쓰는 명령은 이렇다.

| 명령 | 방향 | 하는 일 |
| --- | --- | --- |
| `InstallApplication`의 `Configuration` | 서버 → 앱 | 설치할 때 첫 구성 전달 |
| `Settings` 명령의 `ApplicationConfiguration` 항목 | 서버 → 앱 | 설치 후 구성 변경. `Configuration`을 빼고 보내면 기존 구성을 지운다 |
| `ManagedApplicationConfiguration` | 앱 → 서버 | 지금 앱에 들어가 있는 구성 조회 |
| `ManagedApplicationFeedback` | 앱 → 서버 | 앱이 쓴 피드백 조회. `DeleteFeedback`이 `true`면 읽은 뒤 지운다 |

{: .note }
스키마에 따르면 `ApplicationConfiguration` 설정, `InstallApplication`, `RemoveApplication`은 **DDM이 관리하는 앱에는 실패**하고, `ManagedApplicationFeedback` 응답에는 DDM이 관리하는 앱이 빠진다. 한 앱을 기존 명령과 DDM 두 가지로 동시에 관리하지 않는다.

### DDM 앱 선언과 ManagedApp 프레임워크

[DDM]({{ '/ios/mdm/ddm/' | relative_url }})에는 앱 관리 전용 구성 선언 `com.apple.configuration.app.managed`가 있다. iOS 17.2부터 감독·기기·사용자 등록 모두에서 쓸 수 있다.

```json
{
  "Type": "com.apple.configuration.app.managed",
  "Identifier": "app-crm",
  "ServerToken": "v1",
  "Payload": {
    "AppStoreID": "1234567890",
    "InstallBehavior": {
      "Install": "Required",
      "License": { "Assignment": "Device" }
    },
    "Attributes": { "VPNUUID": "vpn-sales" },
    "AppConfig": {
      "DataAssetReference": "asset-crm-config",
      "Passwords": [
        {
          "Identifier": "api-password",
          "AssetReference": "asset-crm-password"
        }
      ]
    }
  }
}
```

| 키 | 뜻 |
| --- | --- |
| `InstallBehavior.Install` | `Optional`이면 사용자가 설치·삭제할 수 있고, `Required`면 시스템이 설치하고 사용자가 지울 수 없다 |
| `AppConfig` (iOS 18.4부터) | 앱 구성 데이터와 비밀 값을 자산(asset) 선언으로 참조한다 |
| `AppConfig.DataAssetReference` | 구성 property list를 담은 `com.apple.asset.data` 자산. 1MB 이하 |
| `AppConfig.Passwords` / `Identities` / `Certificates` | 암호·인증서 ID·인증서를 담은 자격 증명 자산과, 앱이 꺼낼 때 쓸 식별자 |
| `LegacyAppConfigAssetReference` (iOS 18.4부터) | 예전 `UserDefaults` 방식으로 구성을 넣을 때 쓰는 자산 |

가장 큰 변화는 **비밀 값**이다. [5편]({{ '/ios/mdm/apps/' | relative_url }})에서 본 `UserDefaults` 방식은 평문이라 암호나 토큰을 넣으면 안 됐다. DDM의 `AppConfig`는 암호, 인증서 ID(identity), 인증서를 자격 증명 자산으로 따로 보낸다. 앱은 iOS 18.4에 나온 **ManagedApp 프레임워크**로 이것을 받는다.

ManagedApp 문서에 나온 동작은 이렇다.

- 앱이 `Decodable` 구성 타입을 만들고, `ManagedAppConfigurationProvider`의 `configurations(_:)`로 구성을 받는다. 관리자가 구성을 바꾸면 `for await` 반복이 새 값을 내준다. 디코딩에 실패하면 `nil`을 내준다.
- 디코딩 오류가 `ManagedAppConfigurationDecodingError`를 따르면, 기기가 서버에 "잘못된 구성" 상태를 보고하고 오류 코드와 메시지를 기기 이벤트 로그에 남긴다.
- 비밀 값은 `ManagedAppPasswordsProvider`, `ManagedAppIdentitiesProvider`, `ManagedAppCertificatesProvider`로 식별자를 써서 꺼낸다.
- 기기는 구성을 요청한 앱의 **코드 서명이 설치된 관리형 앱과 같은지 확인한 뒤에만** 구성을 준다. 확장(extension)은 `ExtensionConfigs`로 따로 구성할 수 있다.

{: .tip }
옛 `UserDefaults` 방식이 "현관 앞 우편함에 쪽지 넣기"라면, ManagedApp은 "신분증을 확인하고 건네는 등기 우편"이다. 받는 앱이 진짜인지 확인하고, 비밀 값은 따로 봉투에 담는다.

Apple 문서는 이전 기간을 위한 길도 적어 둔다. 같은 데이터 자산을 `DataAssetReference`와 `LegacyAppConfigAssetReference`에 함께 걸면, 옛 버전 앱은 `UserDefaults`로, 새 버전 앱은 ManagedApp으로 같은 구성을 읽는다. 새 버전 앱은 두 방식을 모두 지원하는 것이 권장되고, 둘 다 있으면 ManagedApp 구성이 우선한다.

### 사용자 등록: 업무 데이터는 따로 암호화된 영역에

개인 기기를 [사용자 등록]({{ '/ios/mdm/enrollment/' | relative_url }})으로 관리하면 위의 앱 단위 기능 위에 저장소 분리가 더해진다. Apple Platform Deployment 가이드의 설명은 이렇다.

- 사용자 등록은 업무 데이터를 **별도의, 암호로 보호된 APFS 볼륨**에 저장한다.
- 계정 기반 등록에서 운영체제는 등록할 때 **별도의 암호화 키**를 만들고, 그 키로 관리형 데이터(관리형 앱의 데이터 컨테이너 등)를 분리한다.
- 사용자나 서버가 등록을 해제하면 운영체제가 **그 키를 파기**한다. 관리형 앱은 등록 해제 때 항상 지워진다.

**APFS 볼륨**은 하나의 저장 장치 안에 나뉜 독립된 저장 공간이다. 키를 파기하면 그 안의 데이터는 더 이상 읽을 수 없게 된다. 개인 데이터는 다른 키로 보호되므로 건드리지 않는다.

## SDK 기반 MAM: 기기 등록 없이 앱만

Apple의 방식은 결국 기기를 어떤 형태로든 MDM에 **등록**해야 한다. 등록 자체를 원하지 않는 직원이나, 협력사 직원처럼 회사가 등록을 요구하기 어려운 경우가 있다. 이때 쓰는 것이 앱 안에 넣은 SDK로 하는 MAM이다. 대표적인 예가 Microsoft Intune이다.

### Intune 앱 보호 정책

Intune의 **앱 보호 정책(App Protection Policy, APP)**은 업무 데이터가 관리되는 앱 안에 머물도록 하는 규칙이다. Microsoft 문서는 이 정책을 **MDM과 독립적으로** 쓸 수 있고, 기기를 등록하든 안 하든 회사 데이터를 보호할 수 있다고 적는다. 이 등록 없는 사용을 흔히 MAM-WE(MAM Without Enrollment)라고 부른다.

정책이 걸리는 기기는 세 종류다.

| 기기 상태 | 문서의 설명 |
| --- | --- |
| Intune에 등록 | 주로 회사 소유 |
| 다른 회사 MDM에 등록 | 주로 회사 소유 |
| 어떤 MDM에도 등록 안 됨 | 주로 직원 개인 기기 |

정책이 적용되는 앱은 **Intune App SDK를 넣었거나 Intune App Wrapping Tool로 감싼 앱**뿐이다. 사용자는 Microsoft Entra 계정으로 앱에 로그인해야 하고, Intune 라이선스가 있어야 하며, 정책이 지정된 보안 그룹에 속해야 한다. 정책은 기기가 아니라 **사용자 ID**를 기준으로 따라간다.

iOS 앱 보호 정책의 주요 설정을 문서에서 골라 보면 이렇다.

| 분류 | 설정 | 하는 일 |
| --- | --- | --- |
| 데이터 이동 | Send Org data to other apps | 업무 데이터를 받을 수 있는 앱을 정한다(모든 앱, 없음, 정책 관리 앱 등) |
| 데이터 이동 | Receive data from other apps | 이 앱으로 데이터를 보낼 수 있는 앱을 정한다 |
| 데이터 이동 | Save copies of org data | "다른 이름으로 저장"을 막고, 허용할 저장소(OneDrive, SharePoint 등)만 고른다 |
| 데이터 이동 | Restrict cut, copy and paste between other apps | 잘라내기·복사·붙여넣기를 막거나 정책 관리 앱끼리만 허용한다 |
| 데이터 이동 | Third party keyboards | 관리되는 앱 안에서 타사 키보드를 막는다 |
| 기능 | Printing Org data, Screen capture | 업무 데이터 인쇄와 화면 캡처를 막는다 |
| 암호화 | Encrypt Org data | 업무 데이터 암호화를 요구한다 |
| 접근 | PIN for access | 업무 맥락에서 앱을 열 때 앱 PIN을 요구한다 |
| 접근 | Recheck the access requirements after | 몇 분 동안 쓰지 않으면 PIN을 다시 묻는다(기본 30분) |

**조건부 실행(Conditional launch)**은 앱을 열 때 조건을 검사하고, 맞지 않으면 경고(Warn), 접근 차단(Block access), 데이터 삭제(Wipe data) 가운데 하나를 하는 기능이다.

| 조건 | 예시 동작 |
| --- | --- |
| Max PIN attempts (기본 5회) | PIN 재설정 또는 데이터 삭제 |
| Offline grace period | 기본 1440분(24시간) 오프라인이면 접근 차단, 기본 90일이면 데이터 삭제 |
| Jailbroken/rooted devices | 탈옥 기기에서 업무 데이터 접근 차단 또는 삭제 |
| Min OS version, Min app version, Min SDK version | 버전 미달 시 경고, 차단, 삭제 |
| Disabled account | Entra ID에서 비활성화된 사용자면 차단 또는 삭제 |

### 업무 맥락과 개인 맥락

Outlook이나 OneDrive처럼 회사 계정과 개인 계정을 함께 쓰는 앱이 있다. Intune SDK의 **다중 ID(multi-identity)** 지원은 정책을 회사 계정 쪽에만 적용하고, 개인 계정의 데이터는 건드리지 않는다. Microsoft 문서의 예로, Word에서 새 문서를 만들면 개인 맥락이고, 회사 OneDrive에 저장하는 순간 업무 맥락이 되어 정책이 붙는다.

Apple의 관리형 앱이 "**앱 단위**"로 경계를 긋는다면, Intune SDK는 "**앱 안의 계정 단위**"까지 경계를 긋는 셈이다.

### 등록 없이 쓸 때의 한계

Microsoft 문서는 MDM에 등록하지 않은 BYOD 기기에서의 한계를 이렇게 적는다.

- 앱을 기기에 배포하지 않는다. 사용자가 스토어에서 직접 받는다.
- 인증서 프로파일이 설치되지 않는다.
- 회사 Wi-Fi와 VPN 설정이 들어가지 않는다.

그리고 iOS 공유 확장(share extension)은 기기를 관리하지 않으면 앱 보호 정책이 제어할 수 없다. 그래서 Intune은 업무 데이터를 앱 밖으로 공유하기 **전에 암호화**해서, 비관리 앱이 열어도 읽을 수 없게 한다.

{: .warning }
Microsoft 문서에 따르면 Intune 앱 보호 정책의 데이터 보호 설정은 **Apple의 Managed Open In을 제어하지 않는다.** 등록된 기기에서 두 가지를 함께 쓴다면 MDM 제한 프로파일과 앱 보호 정책을 각각 설정해야 한다.

## AppConfig: 회사마다 다르지 않은 앱 구성

앱 개발사 입장에서 보면, 고객사마다 쓰는 MDM 제품이 다르다. 제품마다 앱 구성 방식이 다르면 개발사는 SDK를 여러 개 넣어야 한다.

**AppConfig Community**는 스스로를 "모바일 운영체제의 **기본 기능**을 중심으로 도구와 모범 사례를 제공하는 커뮤니티"라고 소개한다. 홈페이지는 앱 개발사에게 주는 이점으로 "독점 SDK의 필요를 줄이는 것"을 든다. iOS 안내 페이지의 내용은 이렇다.

- 앱은 `NSUserDefaults`의 `com.apple.configuration.managed` 사전을 읽는다. 새 규격이 아니라 Apple의 기본 방식을 그대로 쓴다.
- 앱이 지원하는 키와 값을 **XML 정의 파일(spec file)**로 문서화한다. AppConfig가 스키마 파일(.xsd)과 생성 도구를 제공하고, 여러 EMM 콘솔이 이 파일을 읽어 설정 화면을 자동으로 만든다.
- 암호나 인증서 같은 민감한 정보는 이 방식으로 보내면 안 된다. iOS가 이 구성 값을 암호화해 주지 않기 때문이다.

{: .tip }
AppConfig는 "모든 가전제품 콘센트 모양을 맞추자"는 약속과 비슷하다. 전기(구성 값)는 원래 벽에서 나오고(운영체제 기능), 약속은 플러그 모양(키 이름과 정의 파일 형식)만 맞춘다.

Apple의 ManagedApp 문서도 구성 명세를 만들 때 표나 `appconfig.org` 스키마를 쓸 수 있다고 적는다.

## Android에서는

Android 공식 개발자 문서에 나온 대응 기능만 짧게 정리한다.

**관리형 구성(managed configurations)**은 IT 관리자가 원격으로 앱 설정을 넣는 기능이다. 예전 이름은 앱 제한(application restrictions)이다. iOS의 `com.apple.configuration.managed`에 해당한다.

- 앱은 `res/xml/app_restrictions.xml`에 설정 항목을 정의하고, 매니페스트에 `android.content.APP_RESTRICTIONS` 메타데이터로 그 파일을 알린다. EMM은 Google Play API로 이 정의를 읽어 관리 화면을 만든다.
- 앱은 시작하거나 다시 열릴 때(`onResume()`) `RestrictionsManager.getApplicationRestrictions()`로 현재 값을 읽는다.
- 실행 중 변경은 `ACTION_APPLICATION_RESTRICTIONS_CHANGED` 인텐트로 알 수 있다. 이 인텐트는 **코드에서 동적으로 등록한 수신기에만** 전달되고, 매니페스트에 선언한 수신기에는 오지 않는다.
- 적용 결과는 **keyed app states**로 EMM에 피드백할 수 있다. iOS의 `com.apple.feedback.managed`에 해당한다.

**업무 프로필(work profile)**은 Android 5.0(API 21)부터 있는, 한 기기 안에 IT 관리자가 통제하는 별도 프로필이다. 관리자는 업무 프로필에서 쓸 앱과 기기 기능을 정하고, 사용자는 개인 프로필에서 개인 앱을 그대로 쓴다. 두 프로필은 저장 공간이 분리되어 있어서 한쪽의 파일 URI가 다른 쪽에서는 유효하지 않고, 대부분의 인텐트는 기본적으로 프로필 경계를 넘지 않는다. Apple 사용자 등록의 분리된 업무 영역과 비슷한 자리다.

## 선택적 초기화와 전체 초기화

MAM에서 가장 많이 쓰는 동작이 **선택적 초기화(selective wipe)**다. 퇴사자나 분실 기기에서 업무 데이터만 지우고 개인 데이터는 남긴다.

| | 전체 초기화 | 선택적 초기화 (MDM) | 선택적 초기화 (MAM) |
| --- | --- | --- | --- |
| 지우는 범위 | 기기 전체, 공장 초기 상태 | 회사 데이터·앱·설정 | 앱 안의 회사 데이터 |
| 기기 등록 | 필요 | 필요 | 필요 없음 |
| Apple에서 | `EraseDevice` 명령(스키마상 사용자 등록에서는 금지) | 관리 해제, `RemoveApplication`, 사용자 등록의 키 파기 | 운영체제 기능은 없고 앱 SDK가 수행 |
| Intune에서 | Wipe | Retire | 앱 데이터 초기화 요청, 조건부 실행의 Wipe data |

Intune 문서는 MAM 선택적 초기화가 앱에서 회사 데이터를 지우며, 사용자가 앱을 쓰는 중이면 SDK가 **30분마다** 초기화 요청이 있는지 확인하고, 앱을 처음 실행해 회사 계정으로 로그인할 때도 확인한다고 적는다. 즉 MAM 초기화는 **앱이 실행되어야** 일어난다.

{: .question }
퇴사한 직원이 회사 메일 앱을 다시는 열지 않는다면, MAM 선택적 초기화는 언제 실행될까? 조건부 실행의 Offline grace period(기본 90일 후 삭제)가 왜 필요한지 생각해 보자.

또 하나, Intune 문서에 따르면 iOS에서 앱 PIN은 같은 개발사 앱끼리 공유하는 키체인에 저장된다. 그래서 앱 하나를 선택적 초기화해도 그 PIN은 지워지지 않는다. 같은 개발사의 다른 앱이 아직 쓸 수 있기 때문이다.

## Apple 기본 기능 vs SDK 기반 MAM

| | Apple 기본 기능 (관리형 앱) | SDK 기반 MAM (예: Intune APP) |
| --- | --- | --- |
| 기기 등록 | 필요 (BYOD는 사용자 등록) | 필요 없음 |
| 정책을 지키는 주체 | 운영체제 | 앱 안의 SDK |
| 앱 쪽 작업 | 없음(제한은 OS가 적용). 구성·피드백은 앱이 읽고 씀 | SDK를 넣거나 앱을 감싸야 함 |
| 경계 단위 | 앱·계정 | 앱 안의 계정(다중 ID) |
| 복사·붙여넣기 | `requireManagedPasteboard` (iOS 15부터) | 정책 설정으로 제한, 글자 수 허용치도 있음 |
| 다른 이름으로 저장 | Open In 경계로 제어 | Save copies of org data |
| 앱 PIN | 없음 (기기 암호만) | 있음 |
| 조건부 실행 | 없음 | OS 버전, 탈옥, 오프라인 기간 등 |
| 업무 데이터 지우기 | 앱 삭제, 관리 해제 | 앱 안 회사 데이터만 삭제 |
| Wi-Fi, VPN, 인증서 배포 | 됨 (앱별 VPN 포함) | 등록 안 하면 안 됨 |
| 비밀 값 전달 | DDM `AppConfig` + ManagedApp (iOS 18.4부터) | SDK와 ID 공급자 로그인 |

두 방식은 둘 중 하나를 고르는 관계가 아니다. Microsoft 문서도 MDM과 앱 보호 정책을 함께 쓰는 구성을 설명하고, 등록된 기기에는 덜 엄격한 정책을, 등록 안 된 기기에는 더 엄격한 정책을 따로 걸 수 있다고 적는다.

## iOS 개발자: MAM 친화적인 앱 만들기

회사 고객에게 앱을 파는 개발사라면, 앱이 MDM·MAM 환경에서 잘 동작해야 한다. Apple 문서와 샘플에서 확인되는 일은 다섯 가지다.

1. **구성 읽기.** `UserDefaults.standard`의 `com.apple.configuration.managed` 사전을 읽는다. Apple 샘플은 "MDM에서 온 값은 사용 전에 검증하고, 검증에 실패하면 합리적인 기본값을 쓰라"고 주석을 달아 두었다.
2. **변경 감지.** `UserDefaults.didChangeNotification`을 구독해 다시 읽는다. Apple 샘플도 이 알림으로 구성을 다시 읽는다.
3. **피드백 쓰기.** `com.apple.feedback.managed` 키에 사전을 쓴다. 서버는 `ManagedApplicationFeedback` 명령으로 읽는다. Apple 샘플은 피드백 키와 타입을 문서로 공개하라고 적는다.
4. **명세 공개.** 지원하는 키, 타입, 기본값, 허용 범위를 문서로 공개한다. AppConfig 정의 파일을 쓰면 여러 EMM 콘솔이 읽을 수 있다.
5. **비밀 값은 다른 길로.** `UserDefaults` 구성에는 비밀 값을 넣지 않는다. iOS 18.4 이상이면 ManagedApp 프레임워크의 자격 증명 제공자를 쓴다.

Managed Open In과 관리형 붙여넣기는 운영체제가 적용하므로 앱이 따로 할 일은 없다. 다만 앞의 주의 상자처럼, 앱이 자기 코드로 데이터를 내보내는 기능(자체 공유 기능, 외부 업로드 등)은 이 제한 밖이다.

### 예제: 구성 읽기, 검증, 피드백 쓰기

아래 프로그램은 macOS 명령줄에서 돌아가는 시뮬레이션이다. MDM 대신 프로그램이 직접 `com.apple.configuration.managed` 키에 사전을 써서, 앱 쪽 코드가 어떻게 반응하는지 본다.

{: .warning }
이 예제는 **실제 MDM이 구성을 전달하는 과정을 테스트하지 않았다.** 실제 iOS 기기에서 MDM이 값을 넣는 경로는 `UserDefaults.standard`이고, 예제는 실습 흔적을 남기지 않으려고 임시 suite(`UserDefaults(suiteName:)`)를 쓴다. 읽기·검증·피드백 쓰기 코드와 `didChangeNotification` 동작만 확인한 것이다.

핵심 부분은 이렇다. 값마다 타입을 확인하고, 틀리면 기본값을 쓰고 오류를 모은다.

```swift
let configKey = "com.apple.configuration.managed"
let feedbackKey = "com.apple.feedback.managed"

func readConfig(_ d: UserDefaults)
    -> (AppConfig, [String]) {
    var c = fallback
    var errors: [String] = []
    guard let raw = d.dictionary(forKey: configKey) else {
        return (c, [])
    }
    if let s = raw["serverURL"] as? String,
       let u = URL(string: s), u.scheme == "https" {
        c.serverURL = u
    } else if raw["serverURL"] != nil {
        errors.append("serverURL must be an https URL")
    }
    // tenantID, allowExport도 같은 방식
    return (c, errors)
}

func writeFeedback(_ d: UserDefaults, _ errs: [String]) {
    let fb: [String: Any] = [
        "configValid": errs.isEmpty,
        "configErrors": errs,
    ]
    d.set(fb, forKey: feedbackKey)
}
```

변경 알림을 받는 쪽에는 함정이 하나 있다. **피드백을 쓰는 것도 `UserDefaults` 변경이라서 `didChangeNotification`이 다시 온다.** 그래서 구성이 실제로 바뀌었을 때만 적용하도록 직전 값과 비교한다.

```swift
func onDefaultsChanged(_ d: UserDefaults) {
    notes += 1
    let (c, errs) = readConfig(d)
    guard c != current else { return }
    current = c
    applied += 1
    writeFeedback(d, errs)
    // ... 출력
}
```

시뮬레이션은 세 단계다. 앱 실행 직후(구성 없음), MDM이 올바른 구성을 보냄, MDM이 잘못된 값(`http` 주소, 문자열 `"no"`인 불리언)을 보냄.

macOS 15에서 Xcode 16.2의 Swift 6.0.3(`swiftc`)으로 빌드해 실행한 결과다.

```bash
swiftc managed_config.swift -o managed_config
./managed_config
```

```text
[1] app launch, nothing from MDM yet
  applied: https://api.example.com tenant=default export=true
  feedback: valid=true []
[2] MDM sends a valid config
  applied: https://mdm-demo.example.com tenant=sales-kr export=false
  feedback: valid=true []
[3] MDM sends bad values
  applied: https://api.example.com tenant=sales-kr export=true
  feedback: valid=false ["serverURL must be an https URL", "allowExport must be a boolean"]
handler calls: 6 applied: 3
```

Swift 6.4.3에서 `-swift-version 6`(Swift 6 언어 모드)으로 빌드해도 같은 결과가 나왔다.

결과에서 볼 것은 세 가지다.

- **[3]**에서 잘못된 `serverURL`과 `allowExport`는 기본값으로 돌아가고, 올바른 `tenantID`만 반영됐다. 잘못된 값 하나 때문에 앱이 멈추지 않는다.
- 피드백에 어떤 키가 왜 틀렸는지 남는다. 서버 관리자가 `ManagedApplicationFeedback`으로 이것을 읽으면 기기를 직접 보지 않고도 원인을 안다.
- `handler calls: 6 applied: 3`. 알림은 여섯 번 왔지만 적용은 세 번이다. 나머지 세 번은 피드백을 쓰면서 생긴 알림이고, 비교 덕분에 무한 반복 없이 걸러졌다.

{: .note }
예제는 직전 구성과 비교하려고 구성 타입을 `Equatable`로 만들었다. 비교 없이 알림마다 피드백을 쓰면, 쓰기가 알림을 부르고 알림이 다시 쓰기를 부르는 반복이 생긴다.

## 실무에서는

아래는 공식 문서의 사실이 아니라 필자의 판단이다.

{: .tip }
**BYOD는 "등록할 수 있는가"부터 정한다.** 사용자 등록을 받아들일 수 있는 직원이면 Apple 기본 기능(관리형 앱, Managed Open In, 앱별 VPN)으로 앱 수정 없이 많은 것을 막을 수 있다. 등록 자체가 어려운 대상(협력사, 등록을 거부하는 직원)이면 SDK 기반 MAM이 사실상 유일한 길이다. 등록 여부가 쓸 수 있는 도구를 정하기 때문이다.

{: .tip }
**Open In을 막을 때 붙여넣기와 AirDrop도 같이 막는다.** `allowOpenFromManagedToUnmanaged`만 `false`로 두면 문서는 막혀도 본문 복사나 AirDrop이 남는다. `requireManagedPasteboard`와 `forceAirDropUnmanaged`를 함께 켜야 경계가 일관된다. 표에서 보듯 기본값이 각각 `false`라서 명시하지 않으면 적용되지 않는다.

{: .tip }
**앱 구성은 "틀린 값이 와도 죽지 않게" 만든다.** 구성은 사람이 MDM 콘솔에 손으로 넣는 값이라 오타가 생긴다. 예제처럼 키마다 검증하고, 기본값으로 돌아가고, 피드백에 이유를 남기면 지원 문의 하나를 줄일 수 있다.

{: .tip }
**새 앱은 두 구성 방식을 모두 지원한다.** 고객사 MDM이 아직 DDM `AppConfig`를 지원하지 않을 수 있다. Apple 문서도 새 버전 앱이 `UserDefaults` 방식과 ManagedApp을 모두 지원하라고 권한다. 비밀 값이 필요한 기능만 ManagedApp이 있을 때 켜는 식으로 나누면 양쪽 고객을 다 받을 수 있다.

{: .tip }
**선택적 초기화를 믿기 전에 "앱이 안 열리면?"을 따진다.** MAM 초기화는 앱이 실행되어야 일어나므로, 오프라인 유예 기간과 계정 비활성화 조건을 같이 설정해 두는 것이 안전하다. 서버 쪽 토큰 폐기(로그인 세션 끊기)는 앱이 실행되지 않아도 서버에서 적용되므로 함께 쓴다.

## 정리

- **MDM**은 기기 전체를, **MAM**은 업무 앱과 그 안의 데이터만 관리한다. 개인 기기(BYOD)에서 사생활을 지키면서 업무 데이터를 보호하는 방법이다.
- Apple은 **관리형 앱·계정**과 비관리 앱·계정 사이에 경계를 긋는다. 관리형 앱은 서버 명령이나 관리 해제로 데이터와 함께 지울 수 있다.
- **Managed Open In**(`allowOpenFromManagedToUnmanaged` 등), **관리형 붙여넣기**(`requireManagedPasteboard`, iOS 15), AirDrop 제한이 업무 데이터가 개인 앱으로 가는 길을 막는다.
- **앱별 VPN**은 `com.apple.vpn.managed.applayer`의 `VPNUUID`를 앱 `Attributes.VPNUUID`와 맞춰 연결한다.
- 앱 구성은 `com.apple.configuration.managed`, 피드백은 `com.apple.feedback.managed`. DDM의 `com.apple.configuration.app.managed`와 **ManagedApp 프레임워크**(iOS 18.4)는 비밀 값까지 안전하게 넘긴다.
- **사용자 등록**은 업무 데이터를 별도 암호화 영역에 두고, 등록 해제 때 키를 파기한다.
- **Intune 앱 보호 정책**은 SDK로 기기 등록 없이 앱 PIN, 복사·저장 제한, 조건부 실행, 선택적 초기화를 한다. 대신 Wi-Fi·VPN·인증서 배포는 할 수 없다.
- **AppConfig**는 운영체제 기본 구성 방식 위에 키 정의 파일 형식을 맞추는 약속이다. Android는 **관리형 구성**과 **업무 프로필**이 대응한다.
- 앱 개발자는 구성을 검증하고, 변경을 감지하고(피드백 쓰기도 알림을 부른다), 피드백을 남기고, 비밀 값은 다른 길로 받는다.

## 함께 읽기

- [5편 앱 배포와 관리형 앱]({{ '/ios/mdm/apps/' | relative_url }}): 앱 라이선스, `InstallApplication`, 관리형 앱 구성의 기본
- [6편 DDM]({{ '/ios/mdm/ddm/' | relative_url }}): 선언, 자산, 상태 보고의 구조
- [10편 UEM]({{ '/ios/mdm/uem/' | relative_url }}): MDM, MAM, EMM, UEM의 관계와 여러 운영체제 비교

## 실습 소스

- [managed_config.swift]({{ '/assets/examples/ios/mdm/managed_config.swift' | relative_url }}): 관리형 앱 구성을 읽고 검증한 뒤 피드백을 쓰는 과정을 임시 `UserDefaults` suite로 시뮬레이션한다

## 참고

- [apple/device-management (GitHub)](https://github.com/apple/device-management): `com.apple.applicationaccess`, `com.apple.vpn.managed.applayer`, `InstallApplication`, `RemoveApplication`, `Settings`, `ManagedApplicationFeedback`, `app.managed` 스키마
- [Apple Developer: Configuring managed apps and extensions](https://developer.apple.com/documentation/devicemanagement/configuring-managed-apps-and-extensions)
- [Apple Developer: AppManaged](https://developer.apple.com/documentation/devicemanagement/appmanaged)
- [Apple Developer: ManagedApp](https://developer.apple.com/documentation/managedapp)
- [Apple Developer: Managed Application Feedback command](https://developer.apple.com/documentation/devicemanagement/managed-application-feedback-command)
- [Apple Developer Archive: ManagedAppConfig 샘플 코드](https://developer.apple.com/library/archive/samplecode/sc2279/Introduction/Intro.html)
- [Apple Developer: UserDefaults.didChangeNotification](https://developer.apple.com/documentation/foundation/userdefaults/didchangenotification)
- [Apple Platform Deployment: Manage organizational data on Apple devices](https://support.apple.com/guide/deployment/depaa73a4973/web): Managed Open In, 관리형 붙여넣기, 키보드, 관리형 도메인
- [Apple Platform Deployment: Account-driven enrollment methods](https://support.apple.com/guide/deployment/dep4d9e9cd26/web): 데이터 분리 키, 등록 해제 시 키 파기와 앱 삭제
- [Apple Platform Deployment: Intro to device management security](https://support.apple.com/guide/deployment/dep82058a5f7/web): 사용자 등록의 별도 APFS 볼륨
- [Microsoft Learn: App protection policies overview](https://learn.microsoft.com/en-us/intune/app-management/protection/overview)
- [Microsoft Learn: iOS/iPadOS app protection policy settings](https://learn.microsoft.com/en-us/intune/app-management/protection/ref-settings-ios)
- [Microsoft Learn: Wipe only corporate data from apps](https://learn.microsoft.com/en-us/intune/app-management/protection/wipe-corporate-data)
- [Microsoft Learn: Intune App SDK](https://learn.microsoft.com/en-us/intune/developer/app-sdk/)
- [AppConfig Community](https://www.appconfig.org/), [AppConfig: iOS](https://www.appconfig.org/ios.html)
- [Android Developers: Set up managed configurations](https://developer.android.com/work/managed-configurations)
- [Android Developers: Work profiles](https://developer.android.com/work/managed-profiles)
