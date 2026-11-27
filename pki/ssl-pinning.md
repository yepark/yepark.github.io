---
title: "TLS 인증서 검증과 피닝"
parent: "PKI & 암호"
nav_order: 6
permalink: /pki/ssl-pinning/
last_modified_at: 2026-11-20
seo:
  type: BlogPosting
date: 2026-11-15
description: "TLS 기본 신뢰 검사와 SPKI 피닝의 차이, iOS 설정·검증 코드와 인증서 교체 위험을 설명합니다."
redirect_from:
  - /ios/ssl-pinning/
first_written: 2026-11-15
last_modified_date: 2026-11-20
tags: [iOS, Swift, SSL, TLS, Pinning, URLSession]
---

# TLS 인증서 검증과 피닝
{: .no_toc }

{% include article-toc.md %}

HTTPS 연결은 암호화할 통로를 만드는 것과 접속 대상의 신원을 확인하는 것을 함께 수행한다. 인증서 검증은 서버의 이름·유효 기간·용도·발급 경로가 정책에 맞는지 판단한다. 피닝은 이 기본 검증에 앱이 정한 인증서 또는 공개 키 조건을 추가한다.

현재 프로토콜 이름은 TLS다. 예전 이름인 ‘SSL 피닝’도 관용적으로 쓰지만 이 글에서는 TLS 피닝이라고 부른다.

## 기본 신뢰 검사 위에 추가하는 조건

인증서는 공개 키와 서버 이름을 연결하고, 인증서 체인은 신뢰하는 발급자까지 그 연결을 검증하는 데 쓰인다. 피닝(pinning)은 여기에 "이 서버라면 이 키여야 한다"는 앱만의 조건을 하나 더 거는 것이다. 서버의 인증서 교체 계획과 백업 핀을 준비하지 않으면 정상 서버도 차단할 수 있다. 예제의 호스트와 핀 값은 실제 서비스에 그대로 복사하지 않는다.

## 인증서 체인: 보증의 사슬

인증서는 **"이 공개 키는 github.com의 것이 맞다"**라고 적힌 증명서다. 그런데 아무나 이런 증명서를 만들 수 있으면 의미가 없다. 그래서 인증서에는 **누가 보증했는지**가 함께 적혀 있다.

서버가 보내는 목록은 클라이언트가 구성한 최종 검증 경로와 같다고 보장되지 않는다. 루트는 보통 클라이언트의 신뢰 저장소에 있으며 서버가 보내지 않을 수도 있다. 아래는 서버가 제공한 인증서를 관찰하는 명령이다.

```bash
echo | openssl s_client \
    -connect github.com:443 \
    -servername github.com \
    -showcerts 2>/dev/null \
  | grep -E "^ *[0-9] s:|^ *i:"
```

```text
 0 s:CN=github.com
   i:C=GB, O=Sectigo Limited, CN=Sectigo Public Server Authentication CA DV E36
 1 s:C=GB, O=Sectigo Limited, CN=Sectigo Public Server Authentication CA DV E36
   i:C=GB, O=Sectigo Limited, CN=Sectigo Public Server Authentication Root E46
 2 s:C=GB, O=Sectigo Limited, CN=Sectigo Public Server Authentication Root E46
   i:C=US, ST=New Jersey, L=Jersey City, O=The USERTRUST Network, CN=USERTrust ECC Certification Authority
```

`s:`는 **이 인증서의 주인**, `i:`는 **보증해 준 곳(발급자)**이다. 2026년 11월 15일에 받아 본 결과다.

| 위치 | 이름 | 하는 일 |
| --- | --- | --- |
| 0번 | **리프(leaf) 인증서** | github.com 자신의 인증서 |
| 1번 | **중간(intermediate) 인증서** | 리프 인증서를 보증 |
| 신뢰 앵커 | **신뢰 저장소에서 선택한 인증서** | 클라이언트가 신뢰하는 경로의 출발점. 서버 제공 목록의 마지막 항목과 다를 수 있음 |

위 서버 제공 목록의 2번은 이름에 Root가 있지만 발급자가 USERTrust인 교차 서명 인증서다. 목록의 마지막이므로 iPhone이 미리 신뢰하는 루트라고 결론 내릴 수 없다. iOS는 로컬 신뢰 저장소와 인증서 정보를 바탕으로 경로를 구성하고 SSL 정책의 호스트 이름·기간·용도 등도 검사한다. 발급자를 따라가는 것만으로 검증이 끝나지는 않는다.

## iOS가 기본으로 해 주는 검사

다행히 이 체인 검사는 iOS가 알아서 한다. 코드를 한 줄도 안 써도 된다.

일부러 잘못 만든 인증서를 쓰는 시험용 사이트(badssl.com)에 `URLSession`으로 접속해 봤다.

```swift
import Foundation

for host in ["expired.badssl.com", "wrong.host.badssl.com",
             "self-signed.badssl.com", "untrusted-root.badssl.com", "badssl.com"] {
    do {
        let (_, response) = try await URLSession(configuration: .ephemeral)
            .data(from: URL(string: "https://\(host)/")!)
        print(host, "→ 성공", (response as? HTTPURLResponse)?.statusCode ?? -1)
    } catch {
        print(host, "→ 실패", (error as NSError).code)
    }
}
```

```text
expired.badssl.com → 실패 -1202
wrong.host.badssl.com → 실패 -1202
self-signed.badssl.com → 실패 -1202
untrusted-root.badssl.com → 실패 -1202
badssl.com → 성공 200
```

| 사이트 | 무엇이 잘못됐나 | 결과 |
| --- | --- | --- |
| expired | 유효 기간이 지난 인증서 | 실패 |
| wrong.host | 다른 도메인의 인증서 | 실패 |
| self-signed | 아무도 보증하지 않은 인증서 | 실패 |
| untrusted-root | 폰이 모르는 루트가 보증한 인증서 | 실패 |
| (정상) | 문제 없음 | 성공 |

`-1202`는 `NSURLErrorServerCertificateUntrusted`다. 위 환경에서 관측한 결과이며 모든 인증서 실패가 반드시 같은 코드가 되는 것은 아니다. URL 오류에는 기간 등 다른 인증서 오류 코드도 있다. 운영에서는 오류 코드와 원인을 기록하되 검증 실패를 우회하지 않는다.

{: .note }
이 결과는 이 글을 쓴 Mac(macOS 15.6)에서 같은 `URLSession` 코드로 실행한 것이다.

## 그럼 피닝은 왜 필요할까

기본 검사의 기준은 **"폰이 믿는 루트 인증서까지 이어지는가"**다. 그런데 폰이 믿는 루트 인증서는 바뀔 수 있다.

- 회사 보안 장비를 쓰려고 기기에 **회사 루트 인증서**를 설치한 경우
- 개발자가 트래픽을 보려고 **Charles 같은 프록시의 루트 인증서**를 설치한 경우

사용자가 해당 루트에 TLS 신뢰를 부여했고 호스트 이름 등 나머지 정책도 충족하면, 그 장비가 발급한 github.com 인증서가 기본 검사를 통과할 수 있다. 인증서 파일을 단순히 설치한 것과 TLS 신뢰를 허용한 것은 구분한다.

**피닝은 "폰이 믿는 루트 전체"가 아니라 "내가 정한 열쇠"만 믿게 하는 것**이다. 앱 안에 서버의 공개 키 정보를 미리 적어 두고(= 핀을 꽂아 두고), 접속할 때 그것과 맞는지 한 번 더 본다.

### 피닝의 대가

Apple은 2021년 1월 개발자 뉴스(Identity Pinning)에서 이렇게 말한다.

- "In most cases, pinning is not necessary and should be avoided." (대부분은 피닝이 필요 없고 피하는 게 좋다.)
- 피닝한 키가 바뀌면 **앱이 그 서버에 접속하지 못한다.** 서버 인증서를 교체하는 날 앱이 먹통이 될 수 있다.
- 피닝은 기본 검사를 **느슨하게 만들 수 없고, 더 엄격하게만** 만든다. 기본 검사는 여전히 통과해야 한다.

그래서 피닝을 한다면 Apple이 권하는 두 가지를 지킨다.

1. **CA(중간·루트) 키 피닝을 검토한다.** 같은 허용 CA 키가 검증 경로에 남아 있으면 리프 키를 교체할 때 핀 변경을 피할 수 있다. 대신 허용 범위는 넓어진다.
2. **핀을 두 개 이상 넣는다.** 하나가 바뀌어도 나머지로 접속할 수 있다.

## 핀 값 구하기

핀에 넣는 값은 **"인증서 공개 키 정보(SPKI)의 SHA-256 해시를 Base64로 바꾼 것"**이다. 말은 어렵지만, Apple이 알려 준 명령 한 줄이면 나온다.

- **SPKI**(Subject Public Key Info): 인증서 안에서 "공개 키 + 키 종류"가 들어 있는 부분
- **SHA-256 해시**: 긴 데이터를 짧은 지문으로 바꾸는 것. 내용이 조금만 달라도 지문이 완전히 달라진다

```bash
# 서버 인증서들을 파일로 받기
echo | openssl s_client \
    -connect github.com:443 \
    -servername github.com \
    -showcerts 2>/dev/null > chain.txt

# 인증서 하나(cert.pem)의 핀 값 구하기 (Apple 문서에 나온 명령)
cat cert.pem \
  | openssl x509 -inform pem -noout -outform pem -pubkey \
  | openssl pkey -pubin -inform pem -outform der \
  | openssl dgst -sha256 -binary \
  | openssl enc -base64
```

`chain.txt`에서 `-----BEGIN CERTIFICATE-----`부터 `-----END CERTIFICATE-----`까지를 하나씩 잘라 `cert.pem`으로 저장한 뒤 실행하면 된다. github.com 체인으로 구한 값은 이렇다.

| 인증서 | 핀 값 (SPKI SHA-256, Base64) |
| --- | --- |
| github.com (리프) | `8gWWkWa8AfAz0khtRYRodss7ieQPpu8Sd7DppK94eVo=` |
| Sectigo ... CA DV E36 (중간) | `ZSagvDzjltLkewXEBuDxIzpW/dpVw1Juvvmd0hhkzdY=` |
| Sectigo ... Root E46 (루트) | `sLVjNUaFYfW7n6EtgBeEpjOlcnBdNPMrZDRF36iwBdE=` |

{: .warning }
이 값은 2026년 11월 15일 기준이다. 서버가 인증서를 바꾸면 값도 바뀐다. 실제 앱에 넣을 때는 그날 다시 구한다.

## 방법 1: Info.plist에 적기 (코드 없음)

Apple이 공식으로 제공하는 방법이다. `Info.plist`에 아래처럼 적으면 iOS가 알아서 피닝을 검사한다. 핀이 맞지 않으면 그 도메인에는 접속하지 않는다.

```xml
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSPinnedDomains</key>
    <dict>
        <key>github.com</key>
        <dict>
            <key>NSIncludesSubdomains</key>
            <true/>
            <key>NSPinnedCAIdentities</key>
            <array>
                <dict>
                    <key>SPKI-SHA256-BASE64</key>
                    <string>ZSagvDzjltLkewXEBuDxIzpW/dpVw1Juvvmd0hhkzdY=</string>
                </dict>
                <dict>
                    <key>SPKI-SHA256-BASE64</key>
                    <string>sLVjNUaFYfW7n6EtgBeEpjOlcnBdNPMrZDRF36iwBdE=</string>
                </dict>
            </array>
        </dict>
    </dict>
</dict>
```

각 키의 뜻은 이렇다.

- `NSPinnedDomains`: 피닝할 도메인 목록
- `NSIncludesSubdomains`: `true`면 바로 아래 하위 도메인(`api.github.com` 등)에도 적용된다. Apple 문서에 따르면 한 단계 아래까지만 적용되고, 두 단계 아래(`a.b.github.com`)에는 적용되지 않는다.
- `NSPinnedCAIdentities`: **CA(중간·루트) 인증서**의 핀 목록. Apple 문서에 따르면 이 키는 체인의 중간 또는 루트 인증서에 있어야 한다.
- `NSPinnedLeafIdentities`: **리프(서버) 인증서**의 핀 목록. CA 대신 서버 키를 피닝할 때 쓴다.

위 예시는 중간 인증서와 루트 인증서 두 개를 핀으로 넣었다. Apple은 핀을 여러 개 넣어 두면 인증서 하나가 바뀌거나 폐기돼도 앱이 계속 접속할 수 있다고 설명한다.

{: .note }
이 방법은 Apple 개발자 뉴스(Identity Pinning)의 설명과 예제를 바탕으로 썼다. 이 글에서 앱으로 직접 실행해 보지는 않았다.

## 방법 2: URLSessionDelegate로 직접 검사

서버마다 다르게 처리하거나, 실패했을 때 로그를 남기고 싶다면 코드로 직접 검사한다. 흐름은 세 단계다.

1. 서버 인증서 확인 요청인지 본다.
2. **iOS 기본 검사를 먼저 통과**시킨다. (피닝은 기본 검사를 대신하지 않는다.)
3. 체인에 있는 인증서 중 **하나라도 핀과 맞으면** 통과, 아니면 연결을 끊는다.

```swift
import Foundation
import Security
import CryptoKit

enum SPKI {
    // 공개 키 앞에 붙는 머리 부분. 키 종류마다 고정값이다.
    static let headers: [String: [UInt8]] = [
        "rsa2048": [0x30, 0x82, 0x01, 0x22, 0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00, 0x03, 0x82, 0x01, 0x0f, 0x00],
        "rsa4096": [0x30, 0x82, 0x02, 0x22, 0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01, 0x01, 0x05, 0x00, 0x03, 0x82, 0x02, 0x0f, 0x00],
        "ec256": [0x30, 0x59, 0x30, 0x13, 0x06, 0x07, 0x2a, 0x86, 0x48, 0xce, 0x3d, 0x02, 0x01, 0x06, 0x08, 0x2a, 0x86, 0x48, 0xce, 0x3d, 0x03, 0x01, 0x07, 0x03, 0x42, 0x00],
        "ec384": [0x30, 0x76, 0x30, 0x10, 0x06, 0x07, 0x2a, 0x86, 0x48, 0xce, 0x3d, 0x02, 0x01, 0x06, 0x05, 0x2b, 0x81, 0x04, 0x00, 0x22, 0x03, 0x62, 0x00],
    ]

    /// 인증서의 핀 값(SPKI SHA-256, Base64). openssl 명령과 같은 값이 나온다.
    static func hash(of certificate: SecCertificate) -> String? {
        guard let key = SecCertificateCopyKey(certificate),
              let attributes = SecKeyCopyAttributes(key) as? [CFString: Any],
              let keyType = attributes[kSecAttrKeyType] as? String,
              let keySize = attributes[kSecAttrKeySizeInBits] as? Int,
              let keyData = SecKeyCopyExternalRepresentation(key, nil) as Data?
        else { return nil }

        let isRSA = keyType == (kSecAttrKeyTypeRSA as String)
        let isEC = keyType == (kSecAttrKeyTypeECSECPrimeRandom as String)
        let name = (isRSA ? "rsa" : isEC ? "ec" : "") + String(keySize)

        guard let header = headers[name] else { return nil }
        let spki = Data(header) + keyData
        return Data(SHA256.hash(data: spki)).base64EncodedString()
    }
}

final class PinningDelegate: NSObject, URLSessionDelegate {
    private let pinnedHashes: Set<String>
    private let expectedHost = "github.com"

    init(pinnedHashes: Set<String>) {
        self.pinnedHashes = pinnedHashes
    }

    func urlSession(
        _ session: URLSession,
        didReceive challenge: URLAuthenticationChallenge,
        completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void
    ) {
        // 1. 서버 인증서 확인 요청이 아니면 원래대로 처리
        guard challenge.protectionSpace.authenticationMethod == NSURLAuthenticationMethodServerTrust,
              let trust = challenge.protectionSpace.serverTrust
        else {
            completionHandler(.performDefaultHandling, nil)
            return
        }

        // 이 예제 세션은 github.com 전용이다. 다른 호스트로 이동하면 거부한다.
        guard challenge.protectionSpace.host == expectedHost else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        // 2. iOS 기본 검사(체인, 도메인 이름, 유효 기간)를 먼저 통과해야 한다
        var error: CFError?
        guard SecTrustEvaluateWithError(trust, &error) else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }

        // 3. 체인에 있는 인증서 중 하나라도 핀과 맞으면 통과
        let chain = SecTrustCopyCertificateChain(trust) as? [SecCertificate] ?? []
        let matched = chain.contains { certificate in
            SPKI.hash(of: certificate).map(pinnedHashes.contains) ?? false
        }

        if matched {
            completionHandler(.useCredential, URLCredential(trust: trust))
        } else {
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }
}
```

쓰는 쪽은 이렇다.

```swift
let session = URLSession(
    configuration: .default,
    delegate: PinningDelegate(pinnedHashes: [
        "ZSagvDzjltLkewXEBuDxIzpW/dpVw1Juvvmd0hhkzdY=",  // 중간 인증서
        "sLVjNUaFYfW7n6EtgBeEpjOlcnBdNPMrZDRF36iwBdE=",  // 루트 인증서 (백업)
    ]),
    delegateQueue: nil
)

let (data, response) = try await session.data(from: URL(string: "https://github.com")!)
```

### 코드에서 짚고 갈 것

**고정 헤더 방식의 범위.** 이 예제는 일반적인 rsaEncryption RSA 2048·4096비트와 명명된 P-256·P-384 키의 정해진 인코딩만 다룬다. 키 종류·비트 수만으로 모든 인증서의 SPKI 알고리즘 식별자와 DER 표현이 같다고 보장할 수 없다. RSA 지수의 인코딩 길이나 알고리즘 파라미터가 다르면 고정 헤더 재구성이 맞지 않을 수 있다. 임의 인증서를 지원하는 제품용 SPKI 파서로 사용하지 않는다. 제품에서는 위의 ATS 설정이나 검증된 ASN.1 처리 구현으로 인증서의 실제 SPKI를 추출하는 방식을 우선한다.

**`SPKI.headers`는 왜 필요할까?** iOS의 `SecKeyCopyExternalRepresentation`은 **공개 키 값만** 돌려준다. 그런데 핀 값은 "키 종류 + 공개 키"(SPKI)를 통째로 해시한 것이다. 그래서 키 종류에 맞는 머리 부분을 앞에 붙여서 SPKI 모양을 다시 만든 다음 해시한다. 이 머리 부분이 없으면 `openssl`로 구한 값과 맞지 않는다.

**`completionHandler`에 넘기는 값**은 SDK 헤더(`NSURLSession.h`)에 네 가지가 정의되어 있다.

| 값 | 뜻 |
| --- | --- |
| `.useCredential` | 넘긴 인증 정보로 진행 (여기서는 "이 서버 믿는다") |
| `.performDefaultHandling` | 이 함수를 안 만든 것처럼 원래대로 처리 |
| `.cancelAuthenticationChallenge` | 요청 전체를 취소 |
| `.rejectProtectionSpace` | 이 요청은 거절하고 다음 인증 방식을 시도 |

**쓸 수 있는 OS 버전**도 SDK 헤더(`SecTrust.h`)에서 확인했다.

- `SecTrustEvaluateWithError`: iOS 12.0부터
- `SecTrustCopyCertificateChain`: iOS 15.0부터 (그 전에는 `SecTrustGetCertificateAtIndex`를 썼는데, iOS 15.0에서 deprecated 됐다)

위 코드는 iOS 15.0 대상으로 Swift 5, Swift 6 모드 모두 컴파일되는 것을 확인했다.

### 실제로 돌려 본 결과

같은 코드를 Mac 명령줄 프로그램으로 만들어 github.com에 접속해 봤다. 체인의 각 인증서와 핀 값을 출력하도록 `print`를 조금 붙였다.

**맞는 핀**(중간 인증서)을 넣었을 때:

```text
[0] github.com
    8gWWkWa8AfAz0khtRYRodss7ieQPpu8Sd7DppK94eVo=
[1] Sectigo Public Server Authentication CA DV E36
    ZSagvDzjltLkewXEBuDxIzpW/dpVw1Juvvmd0hhkzdY=
[2] Sectigo Public Server Authentication Root E46
    sLVjNUaFYfW7n6EtgBeEpjOlcnBdNPMrZDRF36iwBdE=
성공: 200
```

**틀린 핀**을 넣었을 때:

```text
핀이 맞지 않아 연결을 끊는다
실패: -999 cancelled
```

Swift 코드로 계산한 핀 값이 `openssl` 명령으로 구한 값과 **세 개 모두 똑같다.** 틀린 핀일 때는 `-999`(`NSURLErrorCancelled`)로 요청이 취소된다.

## 어느 인증서를 피닝할까

| 피닝 대상 | 좋은 점 | 조심할 점 |
| --- | --- | --- |
| 리프 키 | 특정 서버 키로 제한한다 | 인증서를 갱신해도 키가 같으면 핀은 같다. 허용되지 않은 새 키로 바꾸면 핀 갱신이 필요하다 |
| 중간 (CA) | 같은 CA에서 새 인증서를 받으면 앱을 안 고쳐도 된다 | CA가 중간 인증서를 바꾸면 접속이 막힌다 |
| 루트 키 | 교체 주기가 길 수 있다 | 같은 허용 키로 이어지는 경로를 넓게 허용한다. 호스트 이름 등 기본 검증은 여전히 필요하다 |

Apple은 서버 대신 **CA 키를 피닝**하고, **핀을 여러 개** 넣으라고 권한다. 그래서 위 예제도 중간 인증서 + 루트 인증서 두 개를 넣었다.

## 키 교체와 장애를 함께 시험하기

핀 두 개가 같은 현재 경로에 들어 있다는 사실만으로 독립적인 백업이 보장되지 않는다. 다음 교체 때 유지할 키와 새 키가 무엇인지 서버 운영 계획과 맞추고, 실제 전환 경로로 시험한다. 핀 검증에 실패하면 기본 검증만으로 자동 우회하는 대신 사용자에게 제한된 기능과 복구 경로를 제공한다.

위 실행 기록은 2026년 11월 15일의 특정 Mac과 서버 체인에서 관찰한 결과다. 현재 서버 체인이나 iOS 기기 전체에서 같은 출력이 나옴을 보장하지 않는다. Info.plist 예제는 설정 방법을 설명하며 앱 실행 검증은 별도로 필요하다.

## 참고

- [Apple Developer News: Identity Pinning: How to configure server certificates for your app (2021-01-14)](https://developer.apple.com/news/?id=g9ejcf8y)
- [Apple: NSPinnedDomains](https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity/nspinneddomains)
- [Apple: SecTrustEvaluateWithError](https://developer.apple.com/documentation/security/sectrustevaluatewitherror(_:_:))
- [Apple: SecTrustCopyCertificateChain](https://developer.apple.com/documentation/security/sectrustcopycertificatechain(_:))
- [badssl.com: 잘못된 인증서 시험용 사이트](https://badssl.com/)
- 이 글의 PKI 쪽 배경: [RSA 암호화와 전자서명 정리](/pki/rsa/), [PKCS#10 인증서 서명 요청과 Subject DN](/pki/pkcs10-subject/)
