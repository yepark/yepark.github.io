---
title: "구성 프로파일과 페이로드"
description: "Wi-Fi, 인증서, 암호, 제한 같은 설정을 담는 Apple 구성 프로파일(.mobileconfig)의 구조와 주요 페이로드, 식별자 규칙, 설치·교체·제거 동작, 서명과 민감 정보 처리를 Python으로 만든 예제로 설명합니다."
parent: Apple MDM
grand_parent: iOS
nav_order: 3
permalink: /ios/mdm/profiles/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, MDM, Configuration-Profile, mobileconfig]
---

# 구성 프로파일과 페이로드
{: .no_toc }

{% include article-toc.md %}

MDM으로 기기에 "사내 Wi-Fi에 자동 연결하고, 화면 잠금 암호는 6자리 이상, 카메라는 끈다"는 설정을 넣으려면 **구성 프로파일(configuration profile)**을 보낸다. 구성 프로파일은 설정을 담은 XML 파일이고, 확장자는 `.mobileconfig`다. MDM 없이 메일이나 웹으로 배포해 사용자가 직접 설치할 수도 있지만, MDM으로 보내면 사용자 확인 없이 설치하고 나중에 바꾸거나 지울 수 있다.

## 구조: 바깥 상자와 페이로드

프로파일은 바깥 상자(`Configuration`) 안에 설정 단위인 **페이로드(payload)**를 여러 개 담는 구조다.

```text
Configuration (프로파일 전체)
 ├─ PayloadIdentifier: com.example.office
 ├─ PayloadUUID, PayloadDisplayName ...
 └─ PayloadContent
     ├─ com.apple.wifi.managed          (Wi-Fi)
     ├─ com.apple.applicationaccess     (제한)
     └─ com.apple.mobiledevice.passwordpolicy (암호 정책)
```

모든 페이로드는 공통 키 네 개를 가진다.

| 키 | 뜻 | 규칙 |
| --- | --- | --- |
| `PayloadType` | 페이로드 종류 | Apple이 정한 값 |
| `PayloadIdentifier` | 사람이 읽는 식별자 | 역도메인 형식. 같은 식별자의 프로파일을 다시 설치하면 **교체**된다 |
| `PayloadUUID` | 고유 식별자 | 내용을 바꿀 때마다 새로 만드는 것이 안전하다 |
| `PayloadVersion` | 형식 버전 | 보통 `1` |

`PayloadIdentifier`가 같으면 기기는 "같은 프로파일의 새 버전"으로 보고 이전 것을 지운 뒤 새것을 설치한다. 식별자를 바꾸면 이전 프로파일이 남은 채로 하나 더 설치돼 설정이 겹친다. 서버는 프로파일마다 식별자를 고정해 두고 내용만 바꿔 보내는 방식으로 관리한다.

## 예제: 사무실 기본 설정 프로파일

Python의 `plistlib`으로 프로파일을 만들어 보자. 실제 서비스에서는 MDM 서버가 이런 코드로 기기별 프로파일을 만든다.

```python
import plistlib

profile = {
    "PayloadType": "Configuration",
    "PayloadVersion": 1,
    "PayloadIdentifier": "com.example.office",
    "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000010",
    "PayloadDisplayName": "사무실 기본 설정",
    "PayloadRemovalDisallowed": True,
    "PayloadContent": [
        {
            "PayloadType": "com.apple.wifi.managed",
            "PayloadVersion": 1,
            "PayloadIdentifier": "com.example.office.wifi",
            "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000011",
            "SSID_STR": "Example-Office",
            "EncryptionType": "WPA2",
            "AutoJoin": True,
            "Password": "<Wi-Fi 암호>",
        },
        {
            "PayloadType": "com.apple.applicationaccess",
            "PayloadVersion": 1,
            "PayloadIdentifier": "com.example.office.restrictions",
            "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000012",
            "allowCamera": False,
            "allowScreenShot": False,
            "allowAppInstallation": False,
        },
        {
            "PayloadType": "com.apple.mobiledevice.passwordpolicy",
            "PayloadVersion": 1,
            "PayloadIdentifier": "com.example.office.passcode",
            "PayloadUUID": "8A7B2C3D-0000-4000-8000-000000000013",
            "forcePIN": True,
            "minLength": 6,
            "maxFailedAttempts": 10,
        },
    ],
}

with open("office.mobileconfig", "wb") as f:
    plistlib.dump(profile, f)

print(plistlib.load(open("office.mobileconfig", "rb"))["PayloadDisplayName"])
```

만든 파일의 앞부분은 이렇다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>PayloadContent</key>
	<array>
		<dict>
			<key>AutoJoin</key>
			<true/>
			<key>EncryptionType</key>
			<string>WPA2</string>
			...
```

Python 3.13에서 실행해 plist로 다시 읽히는 것까지 확인했다. Mac에서는 `plutil -lint office.mobileconfig`로 형식을 검사할 수 있다. 다만 형식이 맞다고 기기가 받아들이는 것은 아니다. 키 이름이 틀리면 대부분 조용히 무시되므로, Apple Configurator나 테스트 기기에 설치해 설정이 실제로 적용됐는지 확인한다.

예제의 `allowAppInstallation`(App Store 앱 설치 금지)은 **감독 모드 기기에서만** 적용된다. 같은 제한 페이로드 안에서도 감독 여부에 따라 적용되는 키가 다르므로, 키마다 Apple 문서의 "Supervised" 표시를 확인한다. 감독 모드는 [4편]({{ '/ios/mdm/commands/' | relative_url }})에서 다룬다.

## 자주 쓰는 페이로드

| 페이로드 | `PayloadType` | 하는 일 |
| --- | --- | --- |
| Wi-Fi | `com.apple.wifi.managed` | SSID, 암호, 802.1X 기업 인증 |
| VPN | `com.apple.vpn.managed` | IKEv2 등 VPN 설정, 앱별 VPN |
| 루트 인증서 | `com.apple.security.root` | 사내 CA 인증서 신뢰 |
| PKCS #12 | `com.apple.security.pkcs12` | 개인 키와 인증서 묶음 설치 |
| SCEP / ACME | `com.apple.security.scep` / `.acme` | 기기가 키를 만들고 인증서를 발급받음 |
| 암호 정책 | `com.apple.mobiledevice.passwordpolicy` | 길이, 복잡도, 실패 횟수 |
| 제한 | `com.apple.applicationaccess` | 카메라, 스크린샷, 앱 설치, AirDrop 등 |
| 메일 / Exchange | `com.apple.mail.managed` / `com.apple.eas.account` | 업무 메일 계정 |
| 웹 콘텐츠 필터 | `com.apple.webcontent-filter` | 유해 사이트 차단 |
| 관리형 도메인 | `com.apple.domains` | 이 도메인에서 받은 파일은 관리형 앱에서만 열게 함 |
| 알림 | `com.apple.notificationsettings` | 앱별 알림 허용·스타일 |
| 등록 | `com.apple.mdm` | MDM 등록 ([2편]({{ '/ios/mdm/enrollment/' | relative_url }})) |

## MDM으로 설치하고 지우기

MDM 서버는 프로파일을 명령으로 보낸다.

| 명령 | 하는 일 |
| --- | --- |
| `InstallProfile` | 프로파일 데이터(`Payload` 키에 바이트로)를 보내 설치 |
| `RemoveProfile` | `Identifier`로 지정한 프로파일 제거 |
| `ProfileList` | 설치된 프로파일 목록 조회 |

MDM으로 설치한 프로파일은 MDM으로만 지울 수 있고, 관리 프로파일(등록 프로파일)이 제거되면 그 MDM이 설치한 프로파일도 함께 사라진다. 사용자가 직접 설치한 프로파일과 MDM이 설치한 프로파일은 별개로 취급된다.

## 서명과 민감 정보

프로파일에는 Wi-Fi 암호나 인증서 개인 키 같은 민감한 값이 들어갈 수 있다. 세 가지를 지킨다.

1. **서명**: 프로파일 전체를 [CMS(PKCS #7)]({{ '/pki/pkcs7/' | relative_url }})로 서명하면 설치 화면에 서명자가 표시되고, 전송 중 변조를 막을 수 있다. 수동 배포하는 프로파일은 반드시 서명한다.
2. **암호화**: 기기별로 보내는 프로파일은 그 기기의 ID 인증서로 페이로드를 암호화할 수 있다. 그 기기만 열 수 있다.
3. **개인 키를 직접 넣지 않기**: PKCS #12로 개인 키를 넣는 대신 SCEP·ACME 페이로드로 기기가 직접 키를 만들게 하면, 서버와 전송 경로에 개인 키가 존재하지 않는다.

## 프로파일 방식의 한계

프로파일은 "설치한 순간의 설정"을 넣는 방식이다. 설정이 지금도 제대로 적용돼 있는지 알려면 서버가 `ProfileList` 같은 명령으로 주기적으로 물어봐야 하고, 여러 조건(예: "OS 17 이상이고 이 앱이 깔린 기기에만")을 조합하려면 서버가 직접 판단해 보내고 지워야 한다. 기기 수만 대에서 이런 폴링은 부담이 크다. 이 한계를 줄이려고 나온 것이 [DDM]({{ '/ios/mdm/ddm/' | relative_url }})이다. DDM에서도 기존 프로파일을 그대로 쓸 수 있는 "레거시 프로파일 구성"이 있어 단계적으로 옮길 수 있다.

## 정리

- 구성 프로파일은 설정 페이로드 여러 개를 담은 plist XML 파일(`.mobileconfig`)이다.
- `PayloadIdentifier`가 같으면 교체, 다르면 추가로 설치된다. 서버는 식별자를 고정해 관리한다.
- 같은 제한 페이로드라도 감독 모드에서만 적용되는 키가 있다.
- MDM으로 설치한 프로파일은 MDM으로만 지울 수 있고, 관리 해제 시 함께 제거된다.
- 민감한 값은 서명·암호화하고, 개인 키는 SCEP·ACME로 기기에서 만들게 한다.

## 실습 소스

- [make_profiles.py]({{ '/assets/examples/ios/mdm/make_profiles.py' | relative_url }}): 등록 프로파일, 사무실 설정 프로파일, `DeviceInformation` 명령과 응답 예시를 만든다

## 참고

- [Apple Developer: Configuring multiple devices using profiles](https://developer.apple.com/documentation/devicemanagement/configuring-multiple-devices-using-profiles)
- [Apple Developer: Profile-Specific Payload Keys](https://developer.apple.com/documentation/devicemanagement/profile-specific-payload-keys)
- [Apple Developer: Restrictions](https://developer.apple.com/documentation/devicemanagement/restrictions)
- [Apple Platform Deployment 가이드](https://support.apple.com/guide/deployment/welcome/web)
