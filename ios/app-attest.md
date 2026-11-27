---
title: "App Attest와 attestKey"
description: "DeviceCheck의 App Attest로 키를 만들고 attestKey로 증명한 뒤, 서버에서 attestation과 assertion을 검증하는 흐름을 Swift 코드와 검증 단계로 설명합니다."
parent: iOS
nav_order: 23
permalink: /ios/app-attest/
date: 2026-11-26
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
last_modified_date: 2026-11-27
tags: [iOS, Security, DeviceCheck, App-Attest]
---

# App Attest와 attestKey
{: .no_toc }

{% include article-toc.md %}

출석 체크를 하면 포인트를 주는 앱이 있다고 생각해 보자. 서버 API는 `POST /rewards/check-in` 하나다. 앱의 네트워크 요청을 복사하면 스크립트로 이 API를 수천 번 호출할 수 있다. 로그인 토큰만으로는 요청을 보낸 쪽이 우리가 배포한 앱인지, 앱을 흉내 내는 프로그램인지 구분하기 어렵다.

**App Attest**는 이 질문에 답하기 위한 기능이다. 앱은 기기의 Secure Enclave(개인 키를 꺼낼 수 없게 보관하는 칩 안의 별도 보안 영역)에 키를 만들고, Apple에 이 키가 정상 기기의 정상 앱에서 만들어졌다는 증명(attestation)을 받는다. 서버는 이 증명을 검증해 공개 키를 저장하고, 이후 중요한 요청마다 그 키로 서명한 assertion을 확인한다.

이 글은 DeviceCheck 프레임워크의 `DCAppAttestService`를 기준으로 한다. iOS 14부터 사용할 수 있다.

## 세 단계로 나뉘는 흐름

App Attest는 한 번의 API 호출로 끝나지 않는다. 앱과 서버가 각자 해야 할 일이 있다.

| 단계 | 앱에서 호출하는 API | 서버가 하는 일 |
| --- | --- | --- |
| 1. 키 생성 | `generateKey()` | 없음 |
| 2. 키 증명 | `attestKey(_:clientDataHash:)` | attestation 검증, 공개 키와 카운터 저장 |
| 3. 요청 서명 | `generateAssertion(_:clientDataHash:)` | assertion 서명과 카운터 검증 |

1·2단계는 앱 설치당 한 번 한다. 3단계는 포인트 지급이나 결제처럼 보호하려는 요청마다 한다. `attestKey`는 Apple 서버와 통신하므로 요청마다 호출하면 안 된다.

## 준비: 지원 여부와 entitlement

먼저 `isSupported`를 확인한다. 시뮬레이터나 지원하지 않는 환경에서는 `false`가 나온다.

```swift
import DeviceCheck

let service = DCAppAttestService.shared
guard service.isSupported else {
    // App Attest 없이 처리할 경로로 보낸다
    return
}
```

앱 타깃의 Signing & Capabilities에서 **App Attest**를 추가하면 entitlements 파일에 다음 키가 생긴다.

```xml
<key>com.apple.developer.devicecheck.appattest-environment</key>
<string>development</string>
```

`development`로 받은 증명은 개발 환경용이다. 배포 빌드에서는 `production`으로 바꾼다. 서버는 이 값에 따라 검증 기준(아래의 `aaguid`)이 달라지므로, 서버에서도 어느 환경의 증명을 받을지 정해 둔다.

## 1단계: generateKey로 키 만들기

```swift
let keyID = try await service.generateKey()
```

`generateKey()`는 Secure Enclave에 P-256 키 쌍을 만들고, 그 키를 가리키는 식별자(`keyID`, Base64 문자열)를 돌려준다. 개인 키는 기기 밖으로 나오지 않는다. 앱이 저장해야 하는 것은 `keyID`뿐이다.

이 키는 앱 설치에 묶인다. 앱을 지웠다가 다시 설치하거나, 백업을 다른 기기로 복원하면 사용할 수 없다. 그래서 `keyID`를 저장했더라도 이후 호출에서 `DCError.invalidKey`가 나오면 새 키를 만드는 경로가 필요하다.

## 2단계: attestKey로 키 증명받기

`attestKey`가 이 글의 핵심이다. 앱은 키와 함께 **서버가 준 일회용 challenge의 해시**를 넘긴다.

```swift
import CryptoKit

let challenge = try await api.fetchAttestChallenge()      // 서버가 만든 임의 바이트
let clientDataHash = Data(SHA256.hash(data: challenge))

let attestation = try await service.attestKey(keyID, clientDataHash: clientDataHash)
try await api.registerAttestation(keyID: keyID, attestation: attestation)
```

`attestKey`를 호출하면 시스템이 Apple 서버에 이 키의 증명을 요청한다. 결과인 `attestation`은 CBOR(JSON과 비슷한 구조를 더 작은 바이너리로 표현하는 형식)로 인코딩된 객체다.

```
{
  fmt: "apple-appattest",
  attStmt: { x5c: [credCert, intermediateCert], receipt: <bytes> },
  authData: <bytes>
}
```

- `x5c`: Apple App Attestation Root CA로 이어지는 인증서 체인. 첫 번째 인증서(credCert)에 앱이 만든 공개 키가 들어 있다.
- `authData`: 앱 ID 해시, 카운터, 키 식별자 등이 정해진 바이트 배치로 들어 있다.
- `receipt`: 나중에 Apple에 위험 지표를 조회할 때 쓰는 영수증.

challenge를 서버가 만들어야 하는 이유는 재전송 방지다. 앱이 직접 만든 값을 쓰면 공격자가 예전에 성공한 attestation을 그대로 다시 보낼 수 있다. 서버는 challenge를 발급하고, 한 번 사용되거나 일정 시간이 지나면 버린다.

### 키 생성과 증명을 하나로 묶기

실제 앱에서는 1·2단계를 함께 처리하고, **서버 등록이 성공한 뒤에만** `keyID`를 저장한다. 중간에 실패한 키를 저장해 두면 이후 assertion이 모두 서버에서 거절된다.

```swift
import CryptoKit
import DeviceCheck

enum AppAttestError: Error {
    case unsupported
}

final class AppAttestClient {
    private let service = DCAppAttestService.shared
    private let store: KeyIDStore      // Keychain 등에 keyID를 저장
    private let api: AttestAPI

    init(store: KeyIDStore, api: AttestAPI) {
        self.store = store
        self.api = api
    }

    func attestedKeyID() async throws -> String {
        guard service.isSupported else { throw AppAttestError.unsupported }
        if let saved = store.load() { return saved }

        let keyID = try await service.generateKey()
        let challenge = try await api.fetchAttestChallenge()
        let clientDataHash = Data(SHA256.hash(data: challenge))
        let attestation = try await service.attestKey(keyID, clientDataHash: clientDataHash)

        try await api.registerAttestation(keyID: keyID, attestation: attestation)
        store.save(keyID)
        return keyID
    }

    func resetKey() {
        store.delete()
    }
}
```

`attestKey`나 서버 등록이 실패하면 그 `keyID`는 버리고 다음 시도에서 새로 만든다. 같은 키에 증명을 반복해서 요청하는 것보다 단순하고, 상태도 "등록된 키가 있다/없다" 두 가지로 줄어든다.

## 서버: attestation 검증하기

서버는 받은 attestation을 아래 순서로 검증한다. 하나라도 실패하면 등록을 거절한다.

1. `x5c`의 인증서 체인이 Apple App Attestation Root CA까지 이어지는지 확인한다.
2. `clientDataHash = SHA256(challenge)`를 서버에서 다시 계산하고, `nonce = SHA256(authData ‖ clientDataHash)`를 만든다.
3. credCert의 확장 `1.2.840.113635.100.8.2`에서 값을 꺼내 2번의 `nonce`와 같은지 비교한다. 이 비교로 attestation이 이번 challenge에 대해 만들어졌음을 확인한다.
4. credCert 공개 키의 SHA-256 해시가 앱이 보낸 `keyID`(Base64 디코딩한 값)와 같은지 확인한다.
5. `authData`의 RP ID 해시가 `SHA256("팀ID.번들ID")`와 같은지 확인한다. 다른 앱이 만든 증명을 막는 단계다.
6. `authData`의 카운터가 0인지 확인한다.
7. `aaguid`가 개발 환경이면 `appattestdevelop`, 운영 환경이면 `appattest` 뒤에 0 바이트 7개가 붙은 값인지 확인한다.
8. `authData`의 credential ID가 `keyID`와 같은지 확인한다.

검증이 끝나면 `keyID`, 공개 키, 카운터(0), `receipt`를 사용자 또는 설치 단위로 저장한다.

`authData`의 앞부분은 다음과 같이 배치된다.

| 오프셋 | 길이 | 내용 |
| --- | --- | --- |
| 0 | 32 | RP ID 해시 |
| 32 | 1 | 플래그 |
| 33 | 4 | 카운터 (big-endian) |
| 37 | 16 | aaguid |
| 53 | 2 | credential ID 길이 |
| 55 | 가변 | credential ID, 이어서 COSE 공개 키 |

CBOR 파싱과 인증서 체인 검증은 직접 구현하기보다 검증된 라이브러리를 쓰는 편이 안전하다. 직접 구현할 부분은 2~8번의 비교 로직이다.

## 3단계: generateAssertion으로 요청 서명하기

키가 등록되면 보호할 요청마다 assertion을 붙인다. 이번에도 서버가 준 challenge를 포함한 `clientData`를 만들고, 그 해시를 서명하게 한다.

```swift
struct CheckInRequest: Encodable {
    let challenge: String   // 서버가 발급한 일회용 값 (Base64)
    let userID: String
    let date: String
}

func sendCheckIn(userID: String) async throws {
    let keyID = try await attestClient.attestedKeyID()
    let challenge = try await api.fetchAssertionChallenge()

    let body = CheckInRequest(
        challenge: challenge.base64EncodedString(),
        userID: userID,
        date: ISO8601DateFormatter().string(from: .now)
    )
    let clientData = try JSONEncoder().encode(body)
    let clientDataHash = Data(SHA256.hash(data: clientData))

    let assertion = try await DCAppAttestService.shared
        .generateAssertion(keyID, clientDataHash: clientDataHash)

    try await api.checkIn(clientData: clientData, assertion: assertion, keyID: keyID)
}
```

요청 본문(`clientData`)을 그대로 서버에 보낸다는 점이 중요하다. 서버는 받은 바이트로 해시를 다시 계산해야 하므로, 서명한 뒤 본문을 다시 인코딩하면 검증이 깨진다.

`generateAssertion`은 Apple 서버와 통신하지 않고 기기에서 서명만 한다. 그래서 요청마다 호출해도 된다.

## 서버: assertion 검증하기

assertion은 `signature`와 `authenticatorData`를 담은 CBOR 객체다. 서버는 저장해 둔 공개 키로 다음을 확인한다.

1. `clientDataHash = SHA256(clientData)`를 계산한다.
2. `nonce = SHA256(authenticatorData ‖ clientDataHash)`를 만든다.
3. 저장된 공개 키로 `signature`가 `nonce`에 대한 올바른 ECDSA 서명인지 확인한다.
4. `authenticatorData`의 RP ID 해시가 `SHA256("팀ID.번들ID")`와 같은지 확인한다.
5. `authenticatorData`의 카운터가 저장된 값보다 큰지 확인하고, 통과하면 저장 값을 갱신한다.
6. `clientData` 안의 challenge가 서버가 발급했고 아직 쓰이지 않은 값인지 확인한다.

카운터는 같은 assertion을 다시 보내는 재전송을 막는다. 같은 키에서 동시에 여러 요청이 들어오면 카운터 순서가 뒤바뀔 수 있으므로, 카운터 갱신은 원자적으로 처리한다.

## 오류 처리

`DCAppAttestService`는 `DCError`를 던진다. 원인별로 대응이 다르다.

| 오류 | 의미 | 앱의 대응 |
| --- | --- | --- |
| `.featureUnsupported` | 이 환경에서 App Attest를 쓸 수 없음 | App Attest 없는 경로로 처리 |
| `.invalidKey` | 키가 없거나 쓸 수 없음 (재설치·복원 등) | 저장된 `keyID`를 지우고 1단계부터 다시 |
| `.invalidInput` | 잘못된 인자 | 해시 길이(32바이트) 등 호출 코드를 점검 |
| `.serverUnavailable` | Apple 서버에 연결할 수 없음 | 잠시 뒤 재시도 |
| `.unknownSystemFailure` | 그 밖의 시스템 오류 | 재시도 후 실패하면 대체 경로 |

```swift
do {
    try await sendCheckIn(userID: userID)
} catch let error as DCError where error.code == .invalidKey {
    attestClient.resetKey()
    try await sendCheckIn(userID: userID)   // 새 키로 한 번만 다시 시도
}
```

## 정책: 무엇을 막고 무엇을 막지 못하는가

App Attest가 증명하는 것은 "이 요청은 정상 Apple 기기에서 실행 중인 우리 앱이 만든 키로 서명됐다"는 사실이다. 다음은 증명하지 않는다.

- 사용자가 악의가 없다는 것. 정상 앱으로도 어뷰징할 수 있다.
- 사용자 인증. 로그인과 App Attest는 별개이며, 서버는 둘 다 확인한다.
- 모든 탈옥·변조 환경의 차단. 위험 신호 중 하나로 다룬다.

그래서 `isSupported`가 `false`이거나 검증에 실패했을 때 무조건 차단하기보다, 요청의 위험도에 따라 정한다. 출석 포인트라면 App Attest가 없는 요청에 한도를 낮게 주고, 송금처럼 위험한 요청이라면 추가 인증을 요구하는 식이다.

사용자가 많은 앱에 처음 적용할 때는 한 번에 전체 사용자에게 켜지 않는다. `attestKey`는 Apple 서버를 거치므로 전체 사용자가 동시에 키를 증명하면 요청이 몰린다. 일부 사용자부터 단계적으로 켜고, 처음에는 검증 결과를 기록만 하다가 차단으로 넘어가는 편이 안전하다.

서버에 저장한 `receipt`로 Apple에 위험 지표(fraud metric)를 조회할 수도 있다. 한 기기에서 최근 만들어진 증명 키의 수를 대략 알려 주므로, 같은 기기에서 재설치를 반복하며 키를 새로 만드는 패턴을 찾는 데 쓴다.

## 점검 목록

- 시뮬레이터가 아닌 실기기에서 시험했는가
- entitlement 환경과 서버의 `aaguid` 기준이 같은가
- challenge를 서버에서 발급하고 한 번만 쓰게 했는가
- 서버 등록이 성공한 뒤에만 `keyID`를 저장하는가
- `invalidKey`에서 새 키를 만드는 경로가 있는가
- assertion 카운터를 원자적으로 갱신하는가
- 지원하지 않는 기기와 검증 실패에 대한 정책이 있는가

## 주요 API

| API | 역할 |
| --- | --- |
| `DCAppAttestService.shared` | App Attest 서비스 싱글턴 |
| `isSupported` | 현재 기기·환경에서 사용할 수 있는지 |
| `generateKey() async throws -> String` | Secure Enclave에 키를 만들고 keyID를 돌려준다 |
| `attestKey(_:clientDataHash:) async throws -> Data` | Apple 서버를 거쳐 키 증명(attestation)을 받는다. 설치당 한 번 |
| `generateAssertion(_:clientDataHash:) async throws -> Data` | 요청 데이터 해시에 서명한 assertion. 요청마다 |
| `DCError.Code` | `.featureUnsupported`, `.invalidKey`, `.invalidInput`, `.serverUnavailable`, `.unknownSystemFailure` |
| `SHA256.hash(data:)` | CryptoKit. `clientDataHash` 계산 |
| `com.apple.developer.devicecheck.appattest-environment` | entitlement. `development` 또는 `production` |

## 이어서 읽기

- [비동기 단위 테스트와 UI 테스트]({{ '/ios/unit-test/' | relative_url }})
- [iOS 프레임워크의 링크와 배포]({{ '/ios/fix-framework/' | relative_url }})

## 참고

- [Apple: Establishing your app's integrity](https://developer.apple.com/documentation/devicecheck/establishing-your-app-s-integrity)
- [Apple: Validating apps that connect to your server](https://developer.apple.com/documentation/devicecheck/validating-apps-that-connect-to-your-server)
- [Apple: Assessing fraud risk](https://developer.apple.com/documentation/devicecheck/assessing-fraud-risk)
- [Apple: DCAppAttestService](https://developer.apple.com/documentation/devicecheck/dcappattestservice)
