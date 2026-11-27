---
title: "앱 배포와 관리형 앱"
description: "ABM의 Apps and Books(예전 VPP)로 앱 라이선스를 사고 기기·사용자에 배정하는 방법, InstallApplication 명령과 관리형 앱, 관리형 앱 구성(Managed App Configuration), 맞춤형 앱과 사내 앱 배포를 설명합니다."
parent: Apple MDM
grand_parent: iOS
nav_order: 5
permalink: /ios/mdm/apps/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, MDM, VPP, Apps-and-Books, Managed-App-Configuration]
---

# 앱 배포와 관리형 앱
{: .no_toc }

{% include article-toc.md %}

회사 기기 500대에 업무용 메신저를 깔아야 한다고 하자. 직원마다 App Store에 로그인해 직접 받게 하면 개인 Apple 계정이 필요하고, 유료 앱이면 각자 결제해야 하며, 퇴사할 때 앱을 회수할 수도 없다. MDM은 기관이 앱 **라이선스**를 사서 기기에 직접 배정하는 방식으로 이 문제를 푼다.

## 라이선스: Apps and Books

ABM(Apple Business Manager)에는 **앱 및 도서(Apps and Books)** 메뉴가 있다. 예전 이름은 **VPP(Volume Purchase Program)**이고, API와 문서에는 지금도 VPP라는 이름이 남아 있다. 기관은 여기서 앱 라이선스를 대량으로 산다. 무료 앱도 "0원 라이선스"를 받아야 MDM으로 배정할 수 있다.

MDM 서버는 ABM에서 받은 **콘텐츠 토큰**(`sToken`, 유효 기간 1년)으로 Apps and Books API에 접속해 라이선스를 관리한다.

| API 작업 | 하는 일 |
| --- | --- |
| 자산 조회 | 기관이 가진 앱 라이선스 목록과 남은 수량 |
| 배정(associate) | 라이선스를 기기 일련번호 또는 사용자에게 붙인다 |
| 회수(disassociate) | 라이선스를 떼어 다른 기기에 다시 쓸 수 있게 한다 |
| 알림 | 배정 결과를 비동기로 받는다 |

### 기기 배정과 사용자 배정

| 방식 | 라이선스가 붙는 곳 | Apple 계정 | 어울리는 경우 |
| --- | --- | --- | --- |
| 기기 배정 | 기기 일련번호 | 필요 없음 | 회사 소유 기기, 공용 기기 |
| 사용자 배정 | 사용자(관리형 Apple 계정 등) | 필요 | 한 사람이 여러 기기를 쓰는 경우, BYOD |

회사 기기에는 대부분 **기기 배정**을 쓴다. 사용자가 App Store에 로그인하지 않아도 앱이 설치되고, 기기를 회수하면 라이선스를 떼어 다른 기기에 붙일 수 있다.

## 설치: InstallApplication

라이선스를 배정한 뒤 MDM 서버는 기기에 설치 명령을 보낸다.

```xml
<dict>
  <key>CommandUUID</key>
  <string>0002-INSTALL-MESSENGER</string>
  <key>Command</key>
  <dict>
    <key>RequestType</key>
    <string>InstallApplication</string>
    <key>iTunesStoreID</key>
    <integer>1234567890</integer>
    <key>ManagementFlags</key>
    <integer>1</integer>
    <key>Options</key>
    <dict>
      <key>PurchaseMethod</key>
      <integer>1</integer>
    </dict>
  </dict>
</dict>
```

| 키 | 뜻 |
| --- | --- |
| `iTunesStoreID` | App Store 앱 ID |
| `ManagementFlags` | `1`이면 관리 해제 시 앱과 데이터를 삭제 |
| `PurchaseMethod` | `1`이면 Apps and Books 라이선스로 설치 |

감독된 기기에서는 사용자 확인 없이 설치되고, 비감독 기기에서는 "이 앱을 설치하시겠습니까?" 확인 창이 뜬다. 설치는 비동기라서 명령 응답(`Acknowledged`)은 "설치를 시작했다"는 뜻일 뿐이다. 실제 설치 완료는 `ManagedApplicationList`나 `InstalledApplicationList`로 다시 확인한다.

## 관리형 앱

MDM이 설치했거나, 사용자가 이미 설치한 앱을 MDM이 관리 대상으로 넘겨받은 앱을 **관리형 앱(managed app)**이라고 한다. 관리형 앱에는 다음 기능이 따라온다.

- 관리 해제 시 앱과 데이터 삭제
- 관리형 앱 구성 전달 (아래)
- 업무 데이터가 개인 앱으로 넘어가지 않게 제한 (관리형 앱 ↔ 비관리 앱 사이의 열기·복사 제한)
- 앱별 VPN 연결
- 백업 제외

## 관리형 앱 구성: 앱에 설정 값 넣기

업무 앱을 처음 켰을 때 사용자가 서버 주소나 회사 코드를 직접 입력하게 하면 불편하고 실수도 많다. **관리형 앱 구성(Managed App Configuration)**을 쓰면 MDM이 앱에 설정 값을 넣어 줄 수 있다.

서버는 앱 설치 명령의 `Configuration` 키나 `Settings` 명령으로 사전(dictionary)을 보낸다.

```xml
<key>Configuration</key>
<dict>
  <key>serverURL</key>
  <string>https://api.example.com</string>
  <key>tenantID</key>
  <string>sales-kr</string>
</dict>
```

앱은 `UserDefaults`의 정해진 키로 이 값을 읽는다.

```swift
let config = UserDefaults.standard.dictionary(forKey: "com.apple.configuration.managed")
let serverURL = config?["serverURL"] as? String

// 값이 바뀌면 알림을 받는다
NotificationCenter.default.addObserver(
    forName: UserDefaults.didChangeNotification, object: nil, queue: .main
) { _ in
    let updated = UserDefaults.standard.dictionary(forKey: "com.apple.configuration.managed")
    // 설정 다시 적용
}
```

앱은 반대로 `com.apple.feedback.managed` 키에 값을 써서 MDM 서버에 상태를 알릴 수 있다(Managed App Feedback). 서버는 `ManagedApplicationFeedback` 명령으로 이 값을 읽는다.

키 이름과 값의 형식은 앱 개발사가 정한다. 여러 MDM 제품에서 같은 형식을 쓰도록 AppConfig Community가 XML 스키마 형식을 제안하고 있다. 관리형 앱 구성은 **암호나 토큰 같은 비밀을 넣는 용도가 아니다.** `UserDefaults`에 평문으로 저장되므로, 비밀은 인증서나 앱의 로그인 절차로 전달한다.

## 맞춤형 앱과 사내 앱

| 방식 | 대상 | 배포 |
| --- | --- | --- |
| 공개 App Store 앱 | 누구나 | Apps and Books 라이선스 |
| 맞춤형 앱(Custom App) | 특정 기관 전용 앱 | 개발사가 App Store Connect에서 특정 기관의 ABM에만 공개. 심사는 받지만 공개 검색에 안 보임 |
| 사내 앱(In-house) | 자사 직원 전용 | Apple Developer Enterprise Program으로 서명한 앱을 MDM이 `InstallEnterpriseApplication` 명령으로 배포 |

새로 시작한다면 맞춤형 앱이 일반적이다. Apple Developer Enterprise Program은 가입 조건이 엄격하고, 인증서 만료나 해지 시 모든 사내 앱이 동시에 실행되지 않는 위험이 있다.

## 앱 업데이트

Apps and Books로 설치한 앱은 App Store 자동 업데이트 설정을 따른다. 특정 버전에서 문제가 생겨 업데이트를 막거나, 반대로 즉시 업데이트를 강제하고 싶다면 `InstallApplication`을 다시 보내 업데이트를 시작하거나, 앱 자동 업데이트 제한을 쓴다. 최신 OS에서는 앱 관리도 [DDM]({{ '/ios/mdm/ddm/' | relative_url }})의 앱 관리 구성으로 옮겨 가고 있다.

## 정리

- 기관은 ABM의 Apps and Books(예전 VPP)에서 앱 라이선스를 사고, MDM 서버가 콘텐츠 토큰으로 API를 써서 기기나 사용자에게 배정한다.
- 회사 기기에는 Apple 계정이 필요 없는 기기 배정이 편하다.
- `InstallApplication` 응답은 설치 시작일 뿐이므로 설치 결과는 따로 조회한다.
- 관리형 앱은 관리 해제 시 삭제, 데이터 유출 제한, 앱별 VPN, 앱 구성 전달을 받을 수 있다.
- 관리형 앱 구성은 `com.apple.configuration.managed` 키로 앱에 설정을 넣는 방법이며, 비밀 값에는 쓰지 않는다.

## 참고

- [Apple Developer: Apps and Books for Organizations](https://developer.apple.com/documentation/devicemanagement/app-and-book-management)
- [Apple Developer: Install Application command](https://developer.apple.com/documentation/devicemanagement/install-application-command)
- [Apple Developer: Distributing custom apps for business](https://developer.apple.com/custom-apps/)
- [AppConfig Community](https://www.appconfig.org/)
