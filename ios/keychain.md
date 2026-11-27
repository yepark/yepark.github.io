---
title: "Keychain에 비밀 값 저장하기"
description: "토큰과 비밀번호를 Keychain에 저장하는 SecItem API와 접근성 등급, Face ID 보호를 설명하고, Keychain을 받치는 Secure Enclave의 구조와 CryptoKit 키 실습, TEE·TA·TrustZone·Secure Element·Android Keystore와의 차이를 정리합니다."
parent: iOS
nav_order: 24
permalink: /ios/keychain/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-28
last_modified_date: 2026-11-28
seo:
  type: BlogPosting
tags: [iOS, Keychain, Security, SecItem, Secure-Enclave, TEE]
---

# Keychain에 비밀 값 저장하기
{: .no_toc }

{% include article-toc.md %}

로그인 후 받은 액세스 토큰을 어디에 저장할까? `UserDefaults`는 쓰기 쉽지만, 앱 폴더 안의 plist 파일에 **평문으로** 저장된다. 백업이나 탈옥 기기, 개발용 도구로 그대로 읽힌다. 토큰, 비밀번호, 암호화 키처럼 유출되면 안 되는 작은 값은 **Keychain**에 저장한다.

**Keychain**은 운영체제가 관리하는 암호화된 저장소다. 데이터는 기기 고유 키와 사용자 암호로 보호되며, 기본적으로 저장한 앱만 읽을 수 있다. 다만 API가 C 스타일이라 처음 쓰면 낯설다. 이 글에서는 자주 쓰는 패턴을 정리한다.

앞부분의 SecItem 예제는 직접 실행하지 못했다. API 이름과 동작은 Apple Security 프레임워크 문서를 기준으로 했다. 뒷부분의 Secure Enclave 예제는 Apple silicon(M4) Mac의 macOS 15.6에서 직접 실행했고, 실제 출력을 붙였다. iPhone에서 실행한 결과가 아니다.

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

## Secure Enclave: 은행 건물 안의 금고실

지금까지 "Keychain은 암호화된다"고만 했다. 그 암호화 키를 실제로 지키는 곳이 **Secure Enclave**다.

**Secure Enclave**는 Apple 칩(SoC) 안에 따로 들어 있는 보안 전용 부품이다. Apple Platform Security 가이드는 이것을 "Apple SoC에 통합된 전용 보안 하위 시스템"이라고 하고, "메인 프로세서와 격리되어 있다"고 설명한다.

{: .tip }
은행 건물을 떠올려 보자. 앱과 iOS가 돌아가는 메인 프로세서(Application Processor)는 손님이 드나드는 은행 로비다. Secure Enclave는 그 건물 안에 있지만 문이 따로 잠긴 **금고실**이다. 로비에 도둑이 들어와도 금고실 안의 열쇠는 볼 수 없다. 로비에서는 "이 서류에 도장 찍어 주세요" 하고 창구로 넘기고, 도장 찍힌 결과만 돌려받는다.

가이드는 이 설계의 목적을 "Application Processor 커널이 뚫려도 민감한 사용자 데이터를 안전하게 지키는 것"이라고 적고 있다.

### 금고실 안에 있는 것

Apple Platform Security 가이드의 "Secure Enclave" 장에 나오는 부품을 정리했다.

| 부품 | 하는 일 |
| --- | --- |
| Secure Enclave Processor | Secure Enclave 전용 CPU. 다른 일에는 쓰지 않는다 |
| Memory Protection Engine | Secure Enclave가 쓰는 메모리를 암호화하고(AES), 위조를 확인하는 태그(CMAC)를 붙인다 |
| Secure Enclave Boot ROM | 바꿀 수 없는 시작 코드. sepOS의 서명을 확인한 뒤에만 실행한다 |
| sepOS | Secure Enclave에서 도는 운영체제. Apple이 고친 L4 마이크로커널 기반 |
| TRNG (진짜 난수 생성기) | 키를 만들 때 쓰는 난수를 만든다 |
| UID, GID 키 | UID는 기기마다 다른 뿌리 키, GID는 같은 칩을 쓰는 기기끼리 같은 키 |
| AES Engine | 대칭키 암호화를 하는 하드웨어. 하드웨어 키는 UID나 GID에서 만든다 |
| Public Key Accelerator (PKA) | RSA, 타원곡선(ECC) 같은 공개키 연산을 하는 하드웨어 |
| 보안 비휘발성 저장소 | 전원이 꺼져도 남는 전용 저장소. 모든 사용자 데이터 암호화 키의 뿌리가 되는 값이 여기 있다 |

몇 가지를 풀어 보자.

- **전용 CPU인 이유.** 가이드는 Secure Enclave Processor를 Secure Enclave에만 쓰는 이유로 "같은 실행 코어를 공유하는 악성 소프트웨어에 의존하는 부채널 공격을 막는 데 도움이 된다"고 적었다. 부채널 공격은 계산 결과가 아니라 걸린 시간, 전력 같은 흔적을 엿보고 비밀을 알아내는 공격이다.
- **자기만의 안전한 부팅.** 기기를 켜면 Application Processor가 sepOS 이미지를 Secure Enclave에 넘긴다. Secure Enclave Boot ROM은 이미지의 해시와 서명을 확인하고, 서명이 맞지 않으면 Secure Enclave를 더 쓰지 못하게 막는다.
- **UID는 꺼낼 수 없다.** 가이드는 "UID 덕분에 데이터를 특정 기기에 암호학적으로 묶을 수 있다"고 하고, UID와 GID는 JTAG 같은 디버깅 단자로도 읽을 수 없다고 적었다. 제조 과정에서도 Apple이나 협력사가 UID를 보거나 저장하지 않도록 만든다.
- **하드웨어 키는 소프트웨어에도 보이지 않는다.** AES Engine과 PKA 안의 키는 "sepOS 소프트웨어에도 보이지 않는다." 소프트웨어는 그 키로 암호화·복호화를 **요청**할 수는 있지만, 키를 **꺼낼** 수는 없다.

### 어떤 기기에 있나

Apple Platform Security 가이드가 적은 목록이다.

- iPhone 5s 이후 모든 iPhone
- iPad Air 이후 모든 iPad
- Apple silicon을 쓰는 모든 Mac, Apple T2 보안 칩이 있는 Intel Mac
- Apple TV HD 이후, Apple Watch Series 1 이후, Apple Vision Pro, 모든 HomePod

개발자 문서 "Protecting keys with the Secure Enclave"는 앱에서 Secure Enclave 키를 쓸 수 있는 기기를 "A7 이후 프로세서의 iOS 기기, 또는 Touch Bar와 Touch ID가 있는 Mac이나 M1 이후 프로세서의 Mac"이라고 적었다. 시뮬레이터처럼 지원하지 않는 환경도 있으므로 코드에서는 `SecureEnclave.isAvailable`로 확인한다.

### Keychain, Face ID와 어떻게 이어지나

Secure Enclave는 앱이 직접 부르지 않아도 이미 Keychain과 파일 암호화 밑에서 일하고 있다.

**1) Keychain 항목의 암호화.** 가이드의 "Keychain data protection" 장에 따르면, Keychain 항목은 AES-256-GCM 키 두 개로 암호화된다.

| 키 | 암호화하는 것 | 보호 |
| --- | --- | --- |
| 테이블 키 (metadata key) | `kSecValueData`를 뺀 나머지 속성 | Secure Enclave가 보호하고, 빠른 검색을 위해 Application Processor에 캐시 |
| 행마다 다른 키 (per-row key) | 비밀 값 `kSecValueData` | 쓸 때마다 **반드시 Secure Enclave를 한 번 거친다** |

그래서 `service`, `account`로 항목을 찾는 일은 빠르고, 실제 비밀 값을 꺼내는 일은 매번 금고실 창구를 거친다.

**2) 클래스 키와 기기 암호.** 앞에서 본 접근성 등급(`kSecAttrAccessible...`)은 데이터 보호 **클래스**와 이어진다. 클래스마다 **클래스 키**가 있고, 이 키가 잠겨 있으면 그 클래스의 데이터를 읽을 수 없다. 가이드의 "Data Protection classes" 장은 이렇게 적었다.

- Complete Protection 클래스: "클래스 키는 사용자 암호와 기기 UID에서 만든 키로 보호된다." 기기가 잠기면 곧 풀어 둔 클래스 키를 버린다.
- Protected Until First User Authentication 클래스: 풀어 둔 클래스 키를 잠겨도 메모리에서 지우지 않는다. 그래서 `AfterFirstUnlock` 항목은 잠긴 화면에서도 읽힌다.

**3) 암호를 기기 밖에서 맞혀 볼 수 없다.** 가이드의 "Passcodes and passwords" 장에 따르면 기기 암호는 UID와 얽혀(entangled) 있다. 그래서 암호를 무작정 대입하는 공격도 **그 기기 위에서** 해야 한다. 한 번 시도에 약 80밀리초가 걸리도록 맞춰 두었고, 틀릴수록 길어지는 대기 시간도 Secure Enclave가 강제한다.

{: .tip }
금고실 열쇠(클래스 키)는 "주인의 비밀번호"와 "이 건물에만 있는 도장(UID)"을 합쳐야 만들어진다. 도둑이 금고 내용물을 통째로 복사해 가도, 도장이 이 건물 밖으로 나오지 않으니 다른 곳에서는 비밀번호를 맞혀 볼 수조차 없다.

**4) Face ID와 Touch ID.** 가이드의 "Face ID and Touch ID security" 장에 따르면 등록할 때 Secure Enclave가 얼굴·지문 템플릿 데이터를 처리하고, 암호화해서 저장한다. Touch ID 데이터는 Secure Enclave만 읽을 수 있는 형태로 저장되며, 기기를 떠나지 않고 Apple에 보내지지도 백업에 들어가지도 않는다. 앞의 `.biometryCurrentSet` 항목을 읽을 때 얼굴이 맞는지 판단하는 곳도 Secure Enclave다.

## 앱에서 Secure Enclave 키 쓰기

Keychain에는 **비밀 값**을 넣는다. 그런데 서명용 개인 키 같은 것은 Keychain에 넣어도 한 가지 약점이 남는다.

Apple 개발자 문서 "Protecting keys with the Secure Enclave"는 이렇게 설명한다. Keychain에 둔 개인 키도 **쓰려면 잠깐 평문으로 메모리에 복사해야 한다.** 앱이 뚫리면 그 순간 키도 새어 나갈 수 있다. Secure Enclave로 키를 보호하면 앱은 평문 키를 **한 번도 만지지 않는다.** Secure Enclave에 키를 만들라고 시키고, 나중에 서명하라고 시키고, 결과만 받는다.

{: .note }
Keychain 항목은 "금고에 넣어 둔 서류"다. 필요하면 꺼내서 로비에서 읽는다. Secure Enclave 키는 "금고실 직원만 쓸 수 있는 도장"이다. 서류를 들여보내면 도장 찍힌 결과만 나오고, 도장 자체는 절대 나오지 않는다.

### 제약

개발자 문서가 적은 제약은 세 가지다.

- **하드웨어가 있어야 한다.** (위의 기기 목록)
- **NIST P-256 타원곡선 키만 된다.** 쓰임새는 서명·검증과 ECDH 키 합의(그리고 그것을 이용한 대칭키 암호화)뿐이다. RSA 키나 AES 키를 Secure Enclave 안에 만들 수는 없다.
- **이미 있는 키를 넣을 수 없다.** 키는 반드시 Secure Enclave 안에서 새로 만든다. 문서는 "평문 키를 Secure Enclave 안팎으로 옮기는 방법이 없다는 것이 보안의 기본"이라고 적었다.

그리고 "그 키를 만든 Secure Enclave만 그 키를 쓸 수 있다"고 적었다. 즉 키는 **기기에 묶인다.**

### CryptoKit으로 만들기

가장 짧은 방법은 CryptoKit의 `SecureEnclave` 타입이다. 아래는 키를 만들고, 서명하고, 일반 공개 키로 검증하고, 개인 키를 "꺼내" 보는 프로그램이다. 전체 파일은 아래 [실습 소스](#실습-소스)에 있다.

```swift
import CryptoKit
import Foundation

typealias SEKey = SecureEnclave.P256.Signing.PrivateKey

print("1. isAvailable:", SecureEnclave.isAvailable)

// 2. Secure Enclave 안에서 키 만들기
let key = try SEKey()
let pub = key.publicKey
print("2. 공개 키 (x963):",
      pub.x963Representation.count, "바이트")

// 3. 서명은 Secure Enclave 안에서 일어난다
let msg = Data("hello enclave".utf8)
let sig = try key.signature(for: msg)

// 4. 일반 CryptoKit 공개 키로 검증
let verifier = try P256.Signing.PublicKey(
    x963Representation: pub.x963Representation)
print("4. 검증:",
      verifier.isValidSignature(sig, for: msg))

// 5. 개인 키를 "꺼내" 보기
let blob = key.dataRepresentation
print("5. dataRepresentation:", blob.count, "바이트")
do {
    _ = try P256.Signing.PrivateKey(
        rawRepresentation: blob)
} catch {
    print("   일반 P256 키로 읽기 실패:", error)
}

// 6. blob으로 같은 키 되살리기
let again = try SEKey(dataRepresentation: blob)
print("6. 되살린 키의 공개 키 같음:",
      again.publicKey.rawRepresentation
          == pub.rawRepresentation)
```

빌드하고 실행한다. 명령줄 프로그램이지만 따로 서명이나 entitlement(앱이 가진 특별 권한 목록)를 넣지 않아도 실행되었다.

```bash
swiftc se_demo.swift -o se_demo
./se_demo
```

실제 출력이다. (macOS 15.6, Apple M4, Swift 6.0.3)

```text
1. isAvailable: true
2. 공개 키 (x963): 65 바이트
3. 서명 (DER): 71 바이트
4. 검증: true
   바꾼 메시지 검증: false
5. dataRepresentation: 284 바이트
   앞 16바이트: 04820118318201143081f50c02726b31
   일반 P256 키로 읽기 실패: underlyingCoreCryptoError(error: -1)
6. 되살린 키의 공개 키 같음: true
   되살린 키 서명 검증: true
7. 공유 비밀 같음: true
```

한 줄씩 보자.

- **2.** 공개 키는 65바이트다. 맨 앞 `04` 한 바이트와 좌표 x, y 각 32바이트다. 공개 키는 원래 공개해도 되는 값이라 자유롭게 꺼낼 수 있다.
- **3.** DER 형식 서명은 71바이트였다. 같은 프로그램을 다시 실행했을 때는 70바이트가 나왔다. 서명 값이 매번 달라서 길이도 조금씩 달라진다.
- **4.** Secure Enclave가 만든 서명을 **보통의** `P256.Signing.PublicKey`로 검증했다. 서버는 Secure Enclave가 없어도 이 서명을 검증할 수 있다는 뜻이다. 한 글자 바꾼 메시지는 `false`다.
- **5.** `dataRepresentation`은 284바이트다. P-256 개인 키 원본은 32바이트이므로 이것은 키 자체가 아니다. 이 값을 일반 P-256 개인 키로 읽으려 하면 오류가 난다.
- **6.** 그런데 같은 값을 `SecureEnclave` 타입에 다시 넣으면 **같은 키**가 되살아나서 서명도 된다.

{: .tip }
`dataRepresentation`은 "금고실 보관증"이다. 보관증에는 도장이 들어 있지 않다. 이 건물의 금고실 창구에 내밀어야만 "아, 그 도장이요" 하고 대신 찍어 준다. 다른 기기에 보관증을 가져가도 쓸모가 없다. 위 결과의 284바이트라는 길이와 앞부분 바이트는 내 실행에서 본 값일 뿐, Apple이 형식을 공개한 것이 아니다.

CryptoKit `SecureEnclave` 타입은 Keychain에 자동으로 저장하지 않는다. 앱을 다시 켰을 때 같은 키를 쓰려면 `dataRepresentation`을 직접 저장해 두어야 한다. 이 값은 앞에서 만든 `Keychain` 구조체로 Keychain에 넣어 두면 된다.

### Security 프레임워크로 만들기

`SecKeyCreateRandomKey`에 `kSecAttrTokenID: kSecAttrTokenIDSecureEnclave`를 주면 키가 Secure Enclave 안에서 만들어진다. 개발자 문서의 예제를 따라 쓴 코드다.

```swift
var err: Unmanaged<CFError>?
let access = SecAccessControlCreateWithFlags(
    nil,
    kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
    .privateKeyUsage,
    &err
)!

let attrs: [String: Any] = [
    kSecAttrKeyType as String:
        kSecAttrKeyTypeECSECPrimeRandom,
    kSecAttrKeySizeInBits as String: 256,
    kSecAttrTokenID as String:
        kSecAttrTokenIDSecureEnclave,
    kSecPrivateKeyAttrs as String: [
        kSecAttrIsPermanent as String: permanent,
        kSecAttrApplicationTag as String:
            Data("com.example.se.demo".utf8),
        kSecAttrAccessControl as String: access,
    ] as [String: Any],
]
let priv = SecKeyCreateRandomKey(
    attrs as CFDictionary, &err)
```

예제 프로그램은 이 키로 개인 키 내보내기(`SecKeyCopyExternalRepresentation`), 공개 키 꺼내기, 서명과 검증을 차례로 해 본다. `kSecAttrIsPermanent`를 `false`(메모리에만)와 `true`(Keychain에 저장)로 한 번씩 실행했다. 실제 출력이다.

```text
permanent=false 성공
  개인 키 내보내기 실패: Error Domain=NSOSStatusErrorDomain Code=-4 "export not implemented for key <SecKeyRef:('com.apple.setoken') 0x14ef07c00>" (kCFMessagePortTransportError / kCSIdentityDeletedErr / unimpErr: /  / unimplemented core routine) UserInfo={numberOfErrorsDeep=0, NSDescription=export not implemented for key <SecKeyRef:('com.apple.setoken') 0x14ef07c00>}
  공개 키: 65 바이트
  검증: true
permanent=true 실패: Error Domain=NSOSStatusErrorDomain Code=-34018 "failed to add key to keychain: <SecKeyRef:('com.apple.setoken') 0x14ef0c1e0>" UserInfo={numberOfErrorsDeep=0, NSDescription=failed to add key to keychain: <SecKeyRef:('com.apple.setoken') 0x14ef0c1e0>}
```

- 개인 키를 내보내려 하면 `-4`, "export not implemented"가 나온다. 키 이름표에 `com.apple.setoken`(Secure Enclave 토큰)이 보인다.
- 공개 키는 CryptoKit 때와 같은 65바이트로 꺼내진다.
- Keychain에 저장(`permanent=true`)하려 하면 `-34018`이 난다. `security error`로 뜻을 찾아보면 이렇다.

```text
$ security error -34018
Error: 0xFFFF7B1E -34018 A required entitlement isn't present.
```

`permanent=true`가 실패한 이유는 서명 없이 빌드한 명령줄 프로그램에 Keychain 접근 그룹 entitlement가 없기 때문으로 보인다. 임시(ad-hoc) 서명으로 `keychain-access-groups` entitlement를 넣어 보았다.

```text
$ codesign -s - -f --entitlements ent.plist seckey_signed
seckey_signed: replacing existing signature
$ ./seckey_signed; echo "exit=$?"
exit=137
```

아무 출력 없이 프로세스가 바로 종료되었다(종료 코드 137은 SIGKILL로 강제 종료되었다는 뜻이다). 그래서 Secure Enclave 키를 Keychain에 **저장하는** 동작은 이 글에서 확인하지 못했다. 이 부분은 Xcode 앱 타깃처럼 개발자 서명과 entitlement를 제대로 갖춘 앱에서 확인해야 한다.

같은 프로그램을 밤에 Mac 화면이 **잠긴 상태**에서 다시 실행해 보았다. 이번에는 `permanent=false`도 실패했다.

```text
permanent=false 실패: Error Domain=NSOSStatusErrorDomain Code=-25308 "Failed to generate keypair" (errKCInteractionNotAllowed / errSecInteractionNotAllowed: / Interaction is not allowed with the Security Server.) ...
```

`-25308`은 앞의 오류 표에 있던 `errSecInteractionNotAllowed`다. 접근 제어에 `kSecAttrAccessibleWhenUnlockedThisDeviceOnly`를 주었으니, 잠긴 동안에는 키를 만들 수 없다. (출력의 뒷부분은 `...`로 줄였다.) 접근성 등급이 Secure Enclave 키에도 그대로 걸린다는 것을 보여 준다. 한편 접근 제어 없이 만드는 CryptoKit 예제(`SEKey()`)는 잠긴 상태에서도 1~7번이 모두 앞과 같이 성공했다.

{: .warning }
`.privateKeyUsage`를 빼먹지 말자. 개발자 문서에 따르면 이 플래그 없이도 키 생성은 **성공하지만**, 그 키로 서명하려 하면 실패한다. 생성이 잘 되어서 놓치기 쉽다.

### 접근 제어 플래그

`SecAccessControlCreateWithFlags`의 플래그는 Keychain 항목과 Secure Enclave 키에 똑같이 쓴다. 개발자 문서의 설명이다.

| 플래그 | 뜻 |
| --- | --- |
| `.privateKeyUsage` | Secure Enclave 안에서 이 개인 키로 서명할 수 있게 한다. Secure Enclave 밖에서 만드는 키에 쓰면 실패한다 |
| `.userPresence` | 생체 인증 **또는** 기기 암호. 얼굴·지문을 다시 등록해도 계속 쓸 수 있다 |
| `.biometryAny` | 생체 인증. 개발자 문서 예제의 설명은 "Touch ID나 Face ID(또는 대체 수단인 암호)로 인증할 수 있을 때만 키를 쓸 수 있다" |
| `.biometryCurrentSet` | **지금 등록된** 얼굴·지문만. 지문을 추가·삭제하거나 Face ID를 다시 등록하면 항목이 무효가 된다 |

CryptoKit에서는 `SEKey(accessControl:)`처럼 같은 `SecAccessControl` 값을 넘긴다.

### 무엇이 무엇을 지키나

| | Keychain 항목 (`kSecClassGenericPassword`) | Secure Enclave 키 |
| --- | --- | --- |
| 담는 것 | 아무 작은 비밀 값 (토큰, 비밀번호, AES 키) | P-256 개인 키 하나 |
| 앱이 원본 값을 보나 | 본다. 읽으면 평문 `Data`가 나온다 | 못 본다. 결과(서명, 공유 비밀)만 받는다 |
| 하는 일 | 저장과 조회 | 서명, ECDH 키 합의 |
| 앱이 뚫렸을 때 | 읽힌 값은 밖으로 복사될 수 있다 | 공격자가 그 기기에서 키를 **쓸** 수는 있어도 키를 **복사해 갈** 수는 없다 |
| 다른 기기로 | 접근성 등급에 따라 백업·이전된다 | 만든 기기에서만 쓸 수 있다 |

## TEE와 TA

Secure Enclave는 Apple의 이름이다. 업계에는 더 넓은 이름이 있는데, 그것이 **TEE**다. Android 문서나 보안 칩 문서를 읽다 보면 TEE, TA, TrustZone 같은 말이 계속 나온다. 여기서는 표준을 만드는 단체인 **GlobalPlatform**의 문서 "TEE System Architecture v1.2"를 기준으로 정리한다.

### REE와 TEE

- **REE (Rich Execution Environment, 일반 실행 환경)**: Android나 Linux 같은 보통 운영체제(Rich OS)가 도는 환경이다. GlobalPlatform 문서는 Rich OS를 "기능과 성능을 목표로 만들었고, 보안이 우선이 아니다"라고 설명한다. 그리고 "TEE 입장에서는 REE의 모든 것을 믿을 수 없는 것으로 봐야 한다"고 적었다.
- **TEE (Trusted Execution Environment, 신뢰 실행 환경)**: "REE와 나란히 돌지만 REE와 격리된 실행 환경"이다. 일반 소프트웨어 공격으로부터 자기 자산(키, 데이터)을 지키고, 프로그램이 접근할 수 있는 데이터와 기능을 엄격히 제한한다.
- **Trusted OS**: TEE 안에서 도는 운영체제다. 한 TEE에는 Trusted OS가 하나만 있다.

{: .tip }
REE는 누구나 드나드는 은행 로비, TEE는 직원만 들어가는 안쪽 사무실이다. 로비가 아무리 북적여도 안쪽 사무실 문은 로비 쪽에서 열 수 없다. 반대로 안쪽 사무실에서는 로비를 내다볼 수 있다. GlobalPlatform 문서도 "REE가 접근하는 자원 일부는 TEE도 접근할 수 있게 만들 수 있지만, 그 반대는 안 된다"고 적었다.

GlobalPlatform 문서는 TEE를 만드는 기술이 여러 가지이고, 기술에 따라 보안 수준이 다르다고 적었다. 또 TEE는 몇 가지 물리 공격에는 버티지만, 칩 패키지를 물리적으로 뜯는 공격은 보통 TEE가 막는 범위 밖이다. 문서는 "TEE는 SE만큼 안전하지는 않지만, 대부분의 애플리케이션에는 충분하다"고 적었다.

### TA와 CA: 세션을 열고 명령을 보낸다

- **TA (Trusted Application, 신뢰 앱)**: "TEE 안에서 돌면서, TEE 밖의 클라이언트 앱이나 TEE 안의 다른 TA에게 보안 기능을 제공하는 앱"이다. 키 관리, 지문 비교, PIN 확인 같은 일을 맡는다.
- **CA (Client Application, 클라이언트 앱)**: TEE **밖**에서 돌면서 TA를 불러 쓰는 앱이다.
- **TEE Client API**: CA가 TA와 대화할 때 쓰는 표준 C API다.
- **TEE Internal Core API**: TA가 TEE 안에서 쓰는 표준 API(암호 연산, 안전한 저장소 등)다.

대화 순서는 이렇다. GlobalPlatform 문서는 "보통의 앱은 TEE Client API로 TEE와 연결하고, TA와 **세션**을 만들고, 공유 메모리를 준비하고, TA마다 정해진 **명령**을 보내 서비스를 부르고, 연결을 정리한다"고 적었다.

- **세션**은 여러 명령을 하나로 묶는 대화 창구다. CA가 세션을 열면 그 TA의 인스턴스에 연결된다. 각 TA 인스턴스의 메모리는 다른 TA 인스턴스와 분리되어 있다.
- **명령**은 TA가 정한 번호(예: 0번은 "값 올리기")다. 어떤 명령과 매개변수가 유효한지는 TA가 정한다.
- TA는 **밖에서 명령이 와야만** 실행을 시작한다.

### TrustZone: TEE를 만드는 흔한 바탕

TEE를 어떤 하드웨어로 만들지는 표준이 정하지 않는다. 휴대폰에서 많이 보이는 것은 Arm의 **TrustZone**이다.

Arm은 TrustZone for Cortex-A를 "CPU에 들어간 하드웨어 격리"라고 설명한다. 하드웨어로 나뉜 **보안 세계(secure, trusted)**와 **일반 세계(non-secure, non-trusted)**가 있고, 보안 세계에서 신뢰 부팅과 Trusted OS를 돌려 TEE를 만드는 데 흔히 쓰인다고 적었다. 쓰임새로는 인증, 암호, 결제, 키 보관, DRM 등을 들었다.

오픈소스 TEE인 **OP-TEE**의 문서는 두 세계를 오가는 방법을 이렇게 설명한다.

- 두 세계의 전환은 CPU의 **Secure Monitor**(모니터)가 맡는다. 모니터가 보안 세계로 들어가고 나오는 것을 모두 관리한다.
- 일반 세계가 보안 세계를 부를 때는 **SMC**(Secure Monitor Call) 명령을 실행한다. SMC는 항상 모니터가 받는다.
- 요청이 Trusted OS를 향한 것이면, 모니터가 OP-TEE OS 쪽으로 실행을 넘긴다.

{: .note }
TrustZone 방식에서 TEE는 일반 세계와 **같은 CPU**에서 돈다. Android의 Trusty TEE 문서도 "Trusty OS는 Android OS와 같은 프로세서에서 돌지만 격리되어 있다"고 하고, Arm 하드웨어에서는 "TrustZone으로 메인 프로세서를 가상화해 안전한 TEE를 만든다"고 적었다. 반면 Apple 가이드는 Secure Enclave에 **전용** Secure Enclave Processor가 있다고 적었다. 이 글에서 읽은 Apple 가이드의 장들은 Secure Enclave를 GlobalPlatform TEE라고 부르지 않는다. 그래서 이 글은 Secure Enclave를 "TEE와 같은 목적을 가진, 별도 프로세서를 쓰는 Apple의 보안 하위 시스템"으로만 소개한다.

### OP-TEE에서 TA는 어떻게 생겼나

OP-TEE 문서에 따르면 TA는 **UUID**(전 세계에서 겹치지 않는 128비트 이름표)로 구별하고, 빌드한 TA 파일 이름도 `<UUID>.ta`다. TA는 정해진 진입점 함수를 반드시 구현해야 한다.

| 진입점 | 불리는 때 |
| --- | --- |
| `TA_CreateEntryPoint` | TA 인스턴스가 만들어질 때 |
| `TA_OpenSessionEntryPoint` | CA가 세션을 열 때 |
| `TA_InvokeCommandEntryPoint` | CA가 명령을 보낼 때 |
| `TA_CloseSessionEntryPoint` | 세션을 닫을 때 |
| `TA_DestroyEntryPoint` | 인스턴스를 없앨 때 |

아래는 공식 예제 저장소 `optee_examples`의 `hello_world`를 줄여 옮긴 것이다. **이 코드는 실행하지 않았다.** OP-TEE는 TrustZone이 있는 Arm 보드나 QEMU 에뮬레이터 환경이 필요해서, 이 Mac에서는 돌릴 수 없다.

TA 쪽(보안 세계)이다. 받은 값을 1 올려서 돌려준다.

```c
/* ta/hello_world_ta.c (줄임) */
TEE_Result TA_InvokeCommandEntryPoint(
    void *sess_ctx, uint32_t cmd_id,
    uint32_t param_types, TEE_Param params[4])
{
    switch (cmd_id) {
    case TA_HELLO_WORLD_CMD_INC_VALUE:
        return inc_value(param_types, params);
    default:
        return TEE_ERROR_BAD_PARAMETERS;
    }
}

static TEE_Result inc_value(uint32_t param_types,
                            TEE_Param params[4])
{
    /* 매개변수 형식 확인은 생략 */
    params[0].value.a++;
    return TEE_SUCCESS;
}
```

CA 쪽(일반 세계, Linux 프로그램)이다. 연결 → 세션 → 명령 → 정리 순서가 GlobalPlatform 문서의 설명과 그대로 맞는다.

```c
/* host/main.c (줄임, 오류 처리 생략) */
TEEC_UUID uuid = TA_HELLO_WORLD_UUID;

TEEC_InitializeContext(NULL, &ctx);
TEEC_OpenSession(&ctx, &sess, &uuid,
    TEEC_LOGIN_PUBLIC, NULL, NULL, &err_origin);

memset(&op, 0, sizeof(op));
op.paramTypes = TEEC_PARAM_TYPES(
    TEEC_VALUE_INOUT, TEEC_NONE,
    TEEC_NONE, TEEC_NONE);
op.params[0].value.a = 42;

TEEC_InvokeCommand(&sess,
    TA_HELLO_WORLD_CMD_INC_VALUE, &op, &err_origin);
/* op.params[0].value.a 는 이제 43 */

TEEC_CloseSession(&sess);
TEEC_FinalizeContext(&ctx);
```

{: .question }
iOS 앱 개발자가 TA를 직접 짤 일이 있을까? 이 글에서 읽은 Apple 문서에서는 서드파티 앱이 Secure Enclave 안에 코드를 올리는 API를 찾지 못했다. 앱은 `SecKey`, CryptoKit, Keychain, LocalAuthentication 같은 정해진 창구로만 Secure Enclave를 쓴다. Android 앱도 Android 개발자 문서가 안내하는 창구는 TA가 아니라 Android Keystore다.

## Secure Element, TEE, Secure Enclave 비교

이름이 비슷한 것이 하나 더 있다. **Secure Element (SE, 보안 요소)**다.

- GlobalPlatform 문서의 정의: "기기 안에서 보안, 기밀성, 여러 애플리케이션 환경을 제공하는 **변조 방지(tamper-resistant)** 보안 하드웨어." 내장 SE, SIM 카드, 스마트카드 같은 형태가 있다.
- Apple 가이드("Apple Pay component security"): Apple 기기의 Secure Element는 "업계 표준 인증을 받은, Java Card 플랫폼을 돌리는 칩"이다. Apple Pay의 기기 계정 번호(Device Account Number)가 여기에 저장되고, NFC 컨트롤러가 Application Processor와 Secure Element 사이의 통신을 이어 준다.

{: .tip }
비유를 이어 가면, Secure Enclave는 은행 건물 안의 금고실이고, Secure Element는 그 금고실 안에 따로 놓인 **작은 금고**다. 작은 금고는 카드 결제처럼 정해진 일만 하지만, 문을 부수려는 물리 공격까지 버티도록 만들어졌다.

Android 쪽의 짝도 함께 보자. Android 개발자 문서 "Android Keystore system"에 따르면:

- Keystore 키의 원본은 **앱 프로세스에 들어가지 않는다.** 암호 연산은 시스템 프로세스가 대신한다.
- 키를 TEE나 SE 같은 **보안 하드웨어**에 묶을 수 있다. 그러면 키 원본이 보안 하드웨어 밖으로 나오지 않는다.
- Android 9(API 28) 이상 기기에는 **StrongBox KeyMint**가 있을 수 있다. 내장 SE나 통합 보안 영역(iSE)으로 구현되며, TEE보다 강한 격리와 변조 방지를 준다. 자기 CPU, 안전한 저장소, 진짜 난수 생성기, 안전한 타이머 등을 갖춰야 한다.
- StrongBox는 일부 알고리즘(RSA 2048, AES 128/256, ECDSA·ECDH P-256, HMAC-SHA256, Triple DES)만 지원한다. 문서는 StrongBox가 더 느리고 자원이 적으므로 "대부분의 앱에는 필요 없다"고 적었다.

| | TEE (TrustZone 방식 예) | Apple Secure Enclave | Secure Element |
| --- | --- | --- | --- |
| 코드가 도는 곳 | 메인 CPU의 보안 세계 | SoC 안의 전용 Secure Enclave Processor | 별도의 변조 방지 칩 |
| 격리 방식 | CPU 하드웨어가 두 세계를 나눔 | 메인 프로세서와 격리된 하위 시스템, 메모리 암호화 | 칩 자체가 물리적으로 분리, 변조 방지 |
| 물리 공격 | 일부만 (GlobalPlatform: 패키지 파괴는 보통 범위 밖) | 가이드에 일반 비교 없음 | 변조 방지가 정의에 포함 |
| 흔한 쓰임 | 키 관리, PIN·지문 처리, DRM | Keychain·파일 키 보호, Face ID/Touch ID, 앱의 P-256 키 | 결제 카드(Apple Pay), SIM |
| iOS 앱이 닿는 길 | 해당 없음 | Keychain, `SecKey` + `kSecAttrTokenIDSecureEnclave`, CryptoKit `SecureEnclave` | 앱이 직접 쓰는 일반 API는 이 글 범위 밖 |
| Android 앱이 닿는 길 | Android Keystore (`TRUSTED_ENVIRONMENT`) | 해당 없음 | Android Keystore + `setIsStrongBoxBacked(true)` (`STRONGBOX`) |

Android에서 키가 실제로 어디에 있는지는 `KeyInfo.getSecurityLevel()`로 확인한다. 값이 `TRUSTED_ENVIRONMENT`나 `STRONGBOX`면 보안 하드웨어 안에 있다는 뜻이다.

## 실무에서는

아래는 위의 문서 내용을 바탕으로 한 내 판단이다.

**1. 서명이 목적이면 Secure Enclave 키, 값을 다시 꺼내 써야 하면 Keychain.**
서버에 "이 기기가 맞다"를 증명하는 서명이나 기기 간 키 합의라면 Secure Enclave 키가 맞다. 앱이 뚫려도 키가 복사되지 않기 때문이다. 반대로 액세스 토큰이나 서버가 준 API 키는 HTTP 헤더에 **원본 그대로** 실어야 하므로, Secure Enclave에 넣을 방법이 없다. 이런 값은 Keychain 항목이다.

**2. 큰 데이터는 두 단계로.**
Secure Enclave는 AES 키를 직접 만들지 못한다. 대신 ECDH 키 합의로 나온 공유 비밀에서 AES 키를 만들 수 있다(개발자 문서가 말하는 "대칭키 암호화로의 확장"). 단순히 파일을 암호화하는 정도라면 이 글 앞부분처럼 AES 키를 Keychain에 두는 편이 훨씬 간단하다.

**3. 키는 언젠가 사라진다고 가정한다.**
Secure Enclave 키는 만든 기기에서만 쓸 수 있다. 새 iPhone으로 바꾸거나 백업에서 복원하면 `dataRepresentation`이나 Keychain 항목이 옮겨 와도 그 키로 서명할 수 없다고 보고 설계한다. 서버에는 "키가 없어졌을 때 다시 등록하는 흐름"(다시 로그인 → 새 키 생성 → 새 공개 키 등록, 옛 공개 키 폐기)을 처음부터 만들어 둔다.

**4. `.biometryCurrentSet`은 "재등록하면 잠긴다"까지 설계한다.**
사용자가 얼굴을 다시 등록하거나 지문을 추가하면 그 항목이나 키는 무효가 된다. 이것은 버그가 아니라 의도한 동작이다. 읽기가 실패하면 기기 암호나 서버 로그인으로 사용자를 다시 확인하고, 키를 새로 만든다. 이렇게까지 엄격할 필요가 없다면 `.userPresence`가 낫다.

**5. 기기 안의 보호를 서버의 신뢰로 착각하지 않는다.**
Secure Enclave는 "키가 복사되지 않는다"를 보장할 뿐, "요청을 보낸 것이 진짜 내 앱이다"를 서버에 증명해 주지는 않는다. 공격자는 자기 기기의 Secure Enclave로 얼마든지 키를 만들고 서명할 수 있다. 서버가 "이 키가 정상 기기의 정상 앱에서 만들어졌는가"를 확인하려면 Apple이 키를 보증해 주는 [App Attest]({{ '/ios/app-attest/' | relative_url }})가 필요하다. App Attest가 만드는 키도 Secure Enclave 안에 있다.

## 정리

- 토큰·비밀번호·암호화 키는 `UserDefaults`가 아니라 Keychain에 저장한다.
- 항목은 `service` + `account`로 구분하고, `SecItemAdd`·`CopyMatching`·`Update`·`Delete`로 다룬다. 결과는 `OSStatus`로 확인한다.
- `kSecAttrAccessible`로 언제 읽을 수 있는지와 기기 이전 여부를 정한다. 백그라운드에서 읽어야 하면 `AfterFirstUnlock` 계열을 쓴다.
- 앱을 지워도 항목이 남을 수 있으므로 첫 실행 때 정리한다.
- Face ID 보호는 `SecAccessControl`로 건다.
- Keychain의 암호화 키는 Secure Enclave가 지킨다. Secure Enclave는 전용 프로세서, 메모리 암호화, 자기만의 안전한 부팅, 꺼낼 수 없는 UID 키를 가진 Apple 칩 안의 보안 하위 시스템이다.
- 서명용 키는 `SecKeyCreateRandomKey` + `kSecAttrTokenIDSecureEnclave`나 CryptoKit `SecureEnclave.P256`로 Secure Enclave 안에 만든다. P-256만 되고, 앱은 키 원본 대신 그 기기에서만 쓸 수 있는 `dataRepresentation`을 받는다.
- TEE는 일반 OS(REE)와 격리된 실행 환경이고, TA는 그 안에서 도는 앱이다. 바깥의 CA가 TEE Client API로 세션을 열고 명령을 보낸다. 휴대폰에서는 Arm TrustZone이 흔한 바탕이다.
- Secure Element는 물리적 변조 방지까지 갖춘 별도 칩이다. Android에서는 Keystore가 TEE와 StrongBox를 감싸는 창구다.
- 기기 안의 보호와 서버의 신뢰는 다르다. 서버가 앱을 믿으려면 App Attest 같은 증명이 필요하다.

## 실습 소스

본문의 Secure Enclave 예제를 파일로 받을 수 있다. Apple silicon Mac에서 `swiftc 파일이름.swift -o 실행파일`로 빌드해 실행한다.

- [se_demo.swift]({{ '/assets/examples/ios/keychain/se_demo.swift' | relative_url }}): CryptoKit으로 키 생성, 서명·검증, `dataRepresentation`, 키 합의
- [seckey_demo.swift]({{ '/assets/examples/ios/keychain/seckey_demo.swift' | relative_url }}): `SecKeyCreateRandomKey`로 키 생성, 내보내기 시도, Keychain 저장 시도

## 이어서 읽기

- [App Attest와 attestKey]({{ '/ios/app-attest/' | relative_url }}): Secure Enclave 키를 Apple이 보증하게 해서 서버가 앱을 확인하는 방법

## 참고

- [Apple: Keychain services](https://developer.apple.com/documentation/security/keychain-services)
- [Apple: Storing keys in the keychain](https://developer.apple.com/documentation/security/storing-keys-in-the-keychain)
- [Apple: Restricting keychain item accessibility](https://developer.apple.com/documentation/security/restricting-keychain-item-accessibility)
- [Apple Platform Security Guide: Keychain data protection](https://support.apple.com/guide/security/keychain-data-protection-secb0694df1a/web)
- [Apple Platform Security Guide: Secure Enclave](https://support.apple.com/guide/security/secure-enclave-sec59b0b31ff/web)
- [Apple Platform Security Guide: Data Protection classes](https://support.apple.com/guide/security/data-protection-classes-secb010e978a/web)
- [Apple Platform Security Guide: Passcodes and passwords](https://support.apple.com/guide/security/passcodes-and-passwords-sec20230a10d/web)
- [Apple Platform Security Guide: Face ID and Touch ID security](https://support.apple.com/guide/security/face-id-and-touch-id-security-sec067eb0c9e/web)
- [Apple Platform Security Guide: Apple Pay component security](https://support.apple.com/guide/security/apple-pay-component-security-sec2561eb018/web)
- [Apple: Protecting keys with the Secure Enclave](https://developer.apple.com/documentation/security/protecting-keys-with-the-secure-enclave)
- [Apple: CryptoKit SecureEnclave](https://developer.apple.com/documentation/cryptokit/secureenclave)
- [Apple: SecAccessControlCreateFlags](https://developer.apple.com/documentation/security/secaccesscontrolcreateflags)
- [GlobalPlatform: TEE System Architecture v1.2 (PDF)](https://globalplatform.org/wp-content/uploads/2017/01/GPD_TEE_SystemArch_v1.2_PublicRelease.pdf)
- [Arm: TrustZone for Cortex-A](https://www.arm.com/technologies/trustzone-for-cortex-a)
- [OP-TEE: Core architecture](https://optee.readthedocs.io/en/latest/architecture/core.html)
- [OP-TEE: Trusted Applications](https://optee.readthedocs.io/en/latest/building/trusted_applications.html)
- [optee_examples: hello_world](https://github.com/linaro-swg/optee_examples/tree/master/hello_world)
- [Android: Android Keystore system](https://developer.android.com/privacy-and-security/keystore)
- [Android: Trusty TEE](https://source.android.com/docs/security/features/trusty)
