---
title: "SSL 인증서 체인과 SSL 피닝"
parent: "iOS"
nav_order: 10
permalink: /ios/ssl-pinning/
first_written: 2026-11-15
last_modified_date: 2026-11-15
tags: [iOS, Swift, SSL, TLS, Pinning, URLSession]
---

# SSL 인증서 체인과 SSL 피닝
{: .no_toc }

<details open markdown="block">
  <summary>목차</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

앱이 `https://`로 서버에 접속할 때마다, iOS는 몰래 한 가지를 확인한다.

> **"지금 대화하는 상대가 진짜 그 서버가 맞나?"**

이 확인에 쓰는 것이 **인증서**이고, 인증서가 믿을 만한지 따라가 보는 길이 **인증서 체인**이다. 여기에 "우리 앱은 이 서버만 믿겠다"고 한 번 더 못 박는 것이 **SSL 피닝**이다.

{: .note }
요즘 실제로 쓰는 기술의 이름은 TLS다. SSL은 예전 이름인데, 지금도 습관처럼 "SSL 인증서", "SSL 피닝"이라고 부른다. 이 글에서도 그냥 SSL이라고 쓴다.

## 인증서 체인: 보증의 사슬

인증서는 **"이 공개 키는 github.com의 것이 맞다"**라고 적힌 증명서다. 그런데 아무나 이런 증명서를 만들 수 있으면 의미가 없다. 그래서 인증서에는 **누가 보증했는지**가 함께 적혀 있다.

재직증명서로 비유하면 이렇다.

- 내 재직증명서는 **회사**가 보증한다.
- 그 회사는 **사업자 등록**으로 나라가 보증한다.
- 나라는 모두가 이미 믿고 있다.

인증서도 똑같이 사슬처럼 이어진다. 실제로 github.com이 보내 주는 인증서를 확인해 보자.

```bash
echo | openssl s_client -connect github.com:443 -servername github.com -showcerts 2>/dev/null \
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
| 끝 | **루트(root) 인증서** | 사슬의 맨 위. iPhone 안에 미리 들어 있다 |

iOS는 0번에서 시작해서 "누가 보증했지?"를 따라 위로 올라간다. 그러다 **iPhone에 미리 들어 있는 루트 인증서**에 닿으면 "믿을 수 있다"고 판단한다. 이렇게 따라 올라가는 길이 **인증서 체인**이다.

{: .tip }
체인은 "github.com → 회사 → 나라"처럼 보증을 따라 올라가는 길이다. 맨 위가 내 폰이 원래 믿는 곳이면 통과다.

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

`-1202`는 `NSURLErrorServerCertificateUntrusted`, 즉 **"서버 인증서를 믿을 수 없음"**이다. 기간, 도메인 이름, 보증 사슬이 하나라도 틀리면 iOS가 알아서 연결을 막는다.

{: .note }
이 결과는 이 글을 쓴 Mac(macOS 15.6)에서 같은 `URLSession` 코드로 실행한 것이다.

## 그럼 SSL 피닝은 왜 필요할까

기본 검사의 기준은 **"폰이 믿는 루트 인증서까지 이어지는가"**다. 그런데 폰이 믿는 루트 인증서는 바뀔 수 있다.

- 회사 보안 장비를 쓰려고 기기에 **회사 루트 인증서**를 설치한 경우
- 개발자가 트래픽을 보려고 **Charles 같은 프록시의 루트 인증서**를 설치한 경우

이러면 중간에서 대화를 엿보는 장비가 만든 가짜 github.com 인증서도 **기본 검사를 통과한다.** 그 장비의 루트를 폰이 믿고 있기 때문이다.

**SSL 피닝은 "폰이 믿는 루트 전체"가 아니라 "내가 정한 열쇠"만 믿게 하는 것**이다. 앱 안에 서버의 공개 키 정보를 미리 적어 두고(= 핀을 꽂아 두고), 접속할 때 그것과 맞는지 한 번 더 본다.

{: .tip }
기본 검사는 "나라에서 인정한 회사의 재직증명서면 OK"이고, 피닝은 "우리 회사 인사팀 도장이 찍힌 것만 OK"다.

### 피닝의 대가

Apple은 2021년 1월 개발자 뉴스(Identity Pinning)에서 이렇게 말한다.

- "In most cases, pinning is not necessary and should be avoided." (대부분은 피닝이 필요 없고 피하는 게 좋다.)
- 피닝한 키가 바뀌면 **앱이 그 서버에 접속하지 못한다.** 서버 인증서를 교체하는 날 앱이 먹통이 될 수 있다.
- 피닝은 기본 검사를 **느슨하게 만들 수 없고, 더 엄격하게만** 만든다. 기본 검사는 여전히 통과해야 한다.

그래서 피닝을 한다면 Apple이 권하는 두 가지를 지킨다.

1. **서버(리프) 키 대신 CA(중간·루트) 키를 피닝한다.** 같은 CA에서 새 인증서를 받으면 앱을 고치지 않아도 된다.
2. **핀을 두 개 이상 넣는다.** 하나가 바뀌어도 나머지로 접속할 수 있다.

## 핀 값 구하기

핀에 넣는 값은 **"인증서 공개 키 정보(SPKI)의 SHA-256 해시를 Base64로 바꾼 것"**이다. 말은 어렵지만, Apple이 알려 준 명령 한 줄이면 나온다.

- **SPKI**(Subject Public Key Info): 인증서 안에서 "공개 키 + 키 종류"가 들어 있는 부분
- **SHA-256 해시**: 긴 데이터를 짧은 지문으로 바꾸는 것. 내용이 조금만 달라도 지문이 완전히 달라진다

```bash
# 서버 인증서들을 파일로 받기
echo | openssl s_client -connect github.com:443 -servername github.com -showcerts 2>/dev/null > chain.txt

# 인증서 하나(cert.pem)의 핀 값 구하기 (Apple 문서에 나온 명령)
cat cert.pem | openssl x509 -inform pem -noout -outform pem -pubkey \
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
| 리프 (서버) | 가장 엄격하다 | 서버 인증서를 바꿀 때마다 앱 업데이트가 필요하다 |
| 중간 (CA) | 같은 CA에서 새 인증서를 받으면 앱을 안 고쳐도 된다 | CA가 중간 인증서를 바꾸면 접속이 막힌다 |
| 루트 (CA) | 가장 오래 바뀌지 않는다 | 같은 루트를 쓰는 다른 인증서도 통과한다 |

Apple은 서버 대신 **CA 키를 피닝**하고, **핀을 여러 개** 넣으라고 권한다. 그래서 위 예제도 중간 인증서 + 루트 인증서 두 개를 넣었다.

## 정리

- **인증서 체인**: 리프 → 중간 → 루트로 이어지는 보증의 사슬. 루트는 폰에 미리 들어 있다.
- **기본 검사**는 iOS가 알아서 한다. 기간, 도메인, 체인 중 하나라도 틀리면 `-1202`로 막는다.
- **SSL 피닝**은 "폰이 믿는 루트 전체" 대신 "내가 정한 키"만 믿게 하는 것이다. 회사나 프록시 루트 인증서가 깔린 기기에서도 가짜 서버를 막는다.
- 핀 값은 **SPKI의 SHA-256 해시(Base64)**다. `openssl` 한 줄로 구한다.
- 방법은 두 가지다. **Info.plist의 `NSPinnedDomains`**, 또는 **`URLSessionDelegate`에서 직접 검사**.
- Apple은 대부분 피닝이 필요 없다고 말한다. 한다면 **CA 키를, 여러 개** 피닝한다.

## 참고

- [Apple Developer News: Identity Pinning: How to configure server certificates for your app (2021-01-14)](https://developer.apple.com/news/?id=g9ejcf8y)
- [Apple: NSPinnedDomains](https://developer.apple.com/documentation/bundleresources/information-property-list/nsapptransportsecurity/nspinneddomains)
- [Apple: SecTrustEvaluateWithError](https://developer.apple.com/documentation/security/sectrustevaluatewitherror(_:_:))
- [Apple: SecTrustCopyCertificateChain](https://developer.apple.com/documentation/security/sectrustcopycertificatechain(_:))
- [badssl.com: 잘못된 인증서 시험용 사이트](https://badssl.com/)
- 이 글의 PKI 쪽 배경: [RSA 암호화와 전자서명 정리](/pki/rsa/), [PKCS#10 인증서 서명 요청과 Subject DN](/pki/pkcs10-subject/)
