---
title: "Keychain에 비밀 값 저장하기"
description: "토큰과 비밀번호를 UserDefaults가 아니라 Keychain에 저장해야 하는 이유와 SecItem API의 추가·조회·수정·삭제, 접근성 등급, 기기 이전과 백업, 앱 간 공유, Face ID로 보호하는 방법을 Swift 예제로 설명합니다."
parent: iOS
nav_order: 24
permalink: /ios/keychain/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, Keychain, Security, SecItem]
---

# Keychain에 비밀 값 저장하기
{: .no_toc }

{% include article-toc.md %}

로그인 후 받은 액세스 토큰을 어디에 저장할까? `UserDefaults`는 쓰기 쉽지만, 앱 폴더 안의 plist 파일에 **평문으로** 저장된다. 백업이나 탈옥 기기, 개발용 도구로 그대로 읽힌다. 토큰, 비밀번호, 암호화 키처럼 유출되면 안 되는 작은 값은 **Keychain**에 저장한다.

**Keychain**은 운영체제가 관리하는 암호화된 저장소다. 데이터는 기기 고유 키와 사용자 암호로 보호되며, 기본적으로 저장한 앱만 읽을 수 있다. 다만 API가 C 스타일이라 처음 쓰면 낯설다. 이 글에서는 자주 쓰는 패턴을 정리한다.

이 글을 쓴 환경에는 Xcode가 없어 예제를 직접 실행하지 못했다. API 이름과 동작은 Apple Security 프레임워크 문서를 기준으로 했다.

## 무엇을 어디에 저장하나

| 저장소 | 암호화 | 어울리는 데이터 |
| --- | --- | --- |
| `UserDefaults` | 없음 (기기 전체 암호화만) | 설정 값, 마지막 탭 위치 |
| 파일 + 데이터 보호(Data Protection) | 파일 단위 | 문서, 캐시 |
| **Keychain** | 항목 단위 | 토큰, 비밀번호, 암호화 키 |
| Secure Enclave | 키를 칩 밖으로 꺼낼 수 없음 | 서명·키 합의용 개인 키 ([App Attest]({{ '/ios/app-attest/' | relative_url }})) |

Keychain은 수 KB 이하의 작은 비밀에 맞다. 큰 데이터는 암호화 키만 Keychain에 두고, 데이터는 그 키로 [AES-GCM]({{ '/pki/aes-gcm/' | relative_url }}) 암호화해 파일로 저장한다.

## 항목의 구성

Keychain API는 **사전(dictionary)**으로 "어떤 항목인지"를 설명해 넘긴다. 토큰이나 비밀번호는 보통 `kSecClassGenericPassword` 종류를 쓴다.

| 키 | 뜻 |
| --- | --- |
| `kSecClass` | 항목 종류. 일반 비밀번호, 인터넷 비밀번호, 인증서, 키 등 |
| `kSecAttrService` | 항목을 구분하는 이름. 보통 앱 번들 ID나 서비스 이름 |
| `kSecAttrAccount` | 같은 서비스 안의 구분자. 예: `"accessToken"` |
| `kSecValueData` | 저장할 값 (`Data`) |
| `kSecAttrAccessible` | 언제 읽을 수 있는지 (아래 표) |

`service`와 `account`의 조합이 항목의 열쇠다. 같은 조합으로 다시 추가하면 `errSecDuplicateItem` 오류가 난다.

## 저장·조회·삭제

```swift
import Foundation
import Security

enum KeychainError: Error {
    case unexpectedStatus(OSStatus)
}

struct Keychain {
    let service: String

    func save(_ value: Data, account: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        let attributes: [String: Any] = [
            kSecValueData as String: value,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly,
        ]

        // 이미 있으면 수정, 없으면 추가
        var status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if status == errSecItemNotFound {
            let newItem = query.merging(attributes) { $1 }
            status = SecItemAdd(newItem as CFDictionary, nil)
        }
        guard status == errSecSuccess else { throw KeychainError.unexpectedStatus(status) }
    }

    func read(account: String) throws -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess else { throw KeychainError.unexpectedStatus(status) }
        return result as? Data
    }

    func delete(account: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw KeychainError.unexpectedStatus(status)
        }
    }
}
```

사용하는 쪽은 이렇다.

```swift
let keychain = Keychain(service: "com.example.todo")
try keychain.save(Data("eyJhbGciOi...".utf8), account: "accessToken")

if let data = try keychain.read(account: "accessToken") {
    let token = String(decoding: data, as: UTF8.self)
}

try keychain.delete(account: "accessToken")   // 로그아웃
```

모든 함수는 `OSStatus` 정수를 돌려준다. 자주 만나는 값이다.

| 값 | 뜻 |
| --- | --- |
| `errSecSuccess` (0) | 성공 |
| `errSecItemNotFound` (-25300) | 항목 없음. 오류가 아니라 "아직 저장 안 됨"으로 처리 |
| `errSecDuplicateItem` (-25299) | 이미 있음. `SecItemAdd` 대신 `SecItemUpdate` |
| `errSecInteractionNotAllowed` (-25308) | 기기가 잠겨 있어 지금은 읽을 수 없음 |

`SecCopyErrorMessageString(status, nil)`로 사람이 읽는 메시지를 얻을 수 있다.

## 접근성 등급: 언제 읽을 수 있나

`kSecAttrAccessible`은 "기기가 어떤 상태일 때 이 항목을 읽을 수 있는가"를 정한다.

| 값 | 읽을 수 있는 때 | 다른 기기로 이전 |
| --- | --- | --- |
| `kSecAttrAccessibleWhenUnlocked` | 기기가 잠금 해제된 동안 | 됨 |
| `kSecAttrAccessibleAfterFirstUnlock` | 재부팅 후 한 번 잠금 해제한 뒤부터 | 됨 |
| `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly` | 잠금 해제 중, 기기 암호가 설정된 경우만 | 안 됨 |
| `...ThisDeviceOnly` 붙은 값 | 위와 같음 | **안 됨** |

- 백그라운드에서 토큰을 갱신하는 앱(푸시를 받아 서버와 통신 등)은 잠긴 상태에서도 읽어야 하므로 `AfterFirstUnlock` 계열을 쓴다. `WhenUnlocked`를 쓰면 화면이 잠긴 동안 `errSecInteractionNotAllowed`가 난다.
- `ThisDeviceOnly`가 붙으면 암호화된 백업으로 새 기기에 옮겨지지 않는다. 기기에 묶여야 하는 토큰에 쓴다.

## 앱을 지워도 남을 수 있다

Keychain 항목은 앱의 샌드박스 폴더가 아니라 시스템 저장소에 있어서, **앱을 삭제해도 항목이 남아 있을 수 있다.** 다시 설치한 앱이 이전 사용자의 토큰을 읽어 자동 로그인되는 일이 생긴다. 흔한 대응은 첫 실행 여부를 `UserDefaults`(앱 삭제 시 함께 지워짐)에 기록해 두고, 첫 실행이면 Keychain 항목을 지우는 것이다.

```swift
if !UserDefaults.standard.bool(forKey: "hasLaunchedBefore") {
    try? keychain.delete(account: "accessToken")
    UserDefaults.standard.set(true, forKey: "hasLaunchedBefore")
}
```

## 앱 간 공유

같은 개발 팀의 앱이나 앱 확장(위젯, 공유 확장)이 같은 토큰을 써야 하면 **Keychain 공유** 기능을 켜고 `kSecAttrAccessGroup`에 같은 그룹을 지정한다. 그룹 이름은 팀 ID로 시작하며, 서로 다른 팀의 앱과는 공유할 수 없다.

## Face ID로 보호하기

읽을 때마다 Face ID나 Touch ID를 요구하려면 접근 제어를 붙인다.

```swift
var error: Unmanaged<CFError>?
let access = SecAccessControlCreateWithFlags(
    nil,
    kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly,
    .biometryCurrentSet,   // 지금 등록된 얼굴·지문만. 새로 등록하면 항목이 무효화된다
    &error
)

let item: [String: Any] = [
    kSecClass as String: kSecClassGenericPassword,
    kSecAttrService as String: "com.example.todo",
    kSecAttrAccount as String: "paymentPIN",
    kSecValueData as String: Data("1234".utf8),
    kSecAttrAccessControl as String: access as Any,
]
SecItemAdd(item as CFDictionary, nil)
```

이 항목을 `SecItemCopyMatching`으로 읽으면 시스템이 Face ID 화면을 띄운다. `Info.plist`에 `NSFaceIDUsageDescription`(Face ID를 쓰는 이유)을 적어야 한다. `.biometryCurrentSet`은 누군가 기기에 자기 얼굴을 추가 등록하면 항목을 읽을 수 없게 되어, 결제 비밀번호처럼 민감한 값에 어울린다.

## 정리

- 토큰·비밀번호·암호화 키는 `UserDefaults`가 아니라 Keychain에 저장한다.
- 항목은 `service` + `account`로 구분하고, `SecItemAdd`·`CopyMatching`·`Update`·`Delete`로 다룬다. 결과는 `OSStatus`로 확인한다.
- `kSecAttrAccessible`로 언제 읽을 수 있는지와 기기 이전 여부를 정한다. 백그라운드에서 읽어야 하면 `AfterFirstUnlock` 계열을 쓴다.
- 앱을 지워도 항목이 남을 수 있으므로 첫 실행 때 정리한다.
- Face ID 보호는 `SecAccessControl`로 건다.

## 참고

- [Apple: Keychain services](https://developer.apple.com/documentation/security/keychain-services)
- [Apple: Storing keys in the keychain](https://developer.apple.com/documentation/security/storing-keys-in-the-keychain)
- [Apple: Restricting keychain item accessibility](https://developer.apple.com/documentation/security/restricting-keychain-item-accessibility)
- [Apple Platform Security Guide: Keychain data protection](https://support.apple.com/guide/security/keychain-data-protection-secb0694df1a/web)
