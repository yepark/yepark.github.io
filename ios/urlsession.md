---
title: "URLSession으로 네트워킹하기"
description: "URLSession의 async/await API로 REST API를 호출하고 JSON을 Codable로 변환하는 방법, HTTP 상태 확인과 오류 분류, 요청 만들기, 타임아웃·취소·재시도, URLProtocol로 서버 없이 테스트하는 방법을 Swift 예제로 설명합니다."
parent: iOS
nav_order: 25
permalink: /ios/urlsession/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [iOS, URLSession, Networking, Codable, async-await]
---

# URLSession으로 네트워킹하기
{: .no_toc }

{% include article-toc.md %}

대부분의 앱은 서버와 대화한다. iOS에서 HTTP 통신의 기본 도구는 Foundation의 **URLSession**이다. 별도 라이브러리 없이도 요청, 응답, 업로드, 다운로드, 백그라운드 전송까지 처리할 수 있고, Swift Concurrency의 `async/await`를 지원한다.

이 글은 [Spring 연재]({{ '/spring/' | relative_url }})에서 만든 할 일 API(`/api/todos`)를 iOS 앱에서 호출하는 코드를 예로 든다. 이 글을 쓴 환경에는 Xcode가 없어 Swift 코드를 직접 실행하지 못했지만, 서버 응답 형식은 Spring 연재에서 실제로 확인한 것이다.

## 가장 짧은 요청

```swift
let url = URL(string: "https://api.example.com/api/todos")!
let (data, response) = try await URLSession.shared.data(from: url)
```

`URLSession.shared`는 기본 설정의 공용 세션이다. `data(from:)`은 응답 본문(`Data`)과 응답 정보(`URLResponse`)를 돌려준다. 이 한 줄에는 빠진 것이 많다. HTTP 상태 코드 확인, JSON 변환, 오류 구분이다.

## 응답을 타입으로 받기

서버의 JSON은 이런 모양이다.

```json
[{"id":1,"title":"장보기","done":false,"createdAt":"2026-11-27T11:41:53.056935Z"}]
```

같은 모양의 Swift 타입을 `Codable`로 선언한다([NSCoding과 Codable]({{ '/ios/nscoding-codable/' | relative_url }})).

```swift
struct Todo: Codable, Identifiable, Sendable {
    let id: Int
    let title: String
    let done: Bool
    let createdAt: Date
}
```

서버가 날짜를 ISO 8601 형식, 그것도 소수점 아래 초가 붙은 형식으로 보내므로 디코더의 날짜 전략을 맞춘다.

```swift
extension JSONDecoder {
    static let api: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let text = try decoder.singleValueContainer().decode(String.self)
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            guard let date = formatter.date(from: text) else {
                throw DecodingError.dataCorrupted(.init(codingPath: decoder.codingPath,
                                                        debugDescription: "날짜 형식 오류: \(text)"))
            }
            return date
        }
        return decoder
    }()
}
```

기본 `.iso8601` 전략은 소수점 아래 초를 읽지 못해 디코딩이 실패한다. 서버의 실제 응답 형식을 보고 전략을 정해야 하는 대표적인 예다.

## API 클라이언트

```swift
enum APIError: Error {
    case invalidResponse
    case http(status: Int, body: Data)
    case decoding(Error)
}

struct TodoAPI {
    let baseURL: URL
    let session: URLSession

    init(baseURL: URL, session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
    }

    func list(done: Bool? = nil) async throws -> [Todo] {
        var components = URLComponents(url: baseURL.appending(path: "api/todos"),
                                       resolvingAgainstBaseURL: false)!
        if let done {
            components.queryItems = [URLQueryItem(name: "done", value: String(done))]
        }
        let request = URLRequest(url: components.url!)
        return try await send(request)
    }

    func create(title: String) async throws -> Todo {
        var request = URLRequest(url: baseURL.appending(path: "api/todos"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONEncoder().encode(["title": title])
        return try await send(request)
    }

    private func send<T: Decodable>(_ request: URLRequest) async throws -> T {
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            throw APIError.http(status: http.statusCode, body: data)
        }
        do {
            return try JSONDecoder.api.decode(T.self, from: data)
        } catch {
            throw APIError.decoding(error)
        }
    }
}
```

몇 가지를 짚는다.

- **URLSession은 404나 500에서 오류를 던지지 않는다.** 서버가 응답만 했다면 성공으로 돌려준다. 상태 코드는 직접 확인해야 한다.
- 쿼리 문자열은 문자열을 이어 붙이지 말고 `URLComponents`로 만든다. 한글이나 특수 문자를 알맞게 인코딩해 준다.
- 실패 응답의 본문(`body`)을 오류에 담아 두면, Spring 서버가 보낸 [ProblemDetail]({{ '/spring/rest-api/' | relative_url }})(`{"detail": "...", "errors": {...}}`)을 디코딩해 사용자에게 필드별 메시지를 보여 줄 수 있다.
- `session`을 매개변수로 받아 두면 테스트에서 가짜 세션을 넣을 수 있다(아래).

## 오류를 세 종류로 나눠 처리하기

| 종류 | 예 | 앱에서 할 일 |
| --- | --- | --- |
| 전송 오류 (`URLError`) | 오프라인, 타임아웃, DNS 실패, TLS 인증서 오류 | "네트워크를 확인하세요", 재시도 버튼 |
| HTTP 오류 (`APIError.http`) | 400, 401, 404, 500 | 400은 입력 안내, 401은 재로그인, 5xx는 잠시 후 재시도 |
| 변환 오류 (`APIError.decoding`) | 서버 응답 형식이 앱의 타입과 다름 | 개발자 오류. 로그를 남기고 일반 오류 표시 |

```swift
do {
    todos = try await api.list()
} catch let error as URLError where error.code == .notConnectedToInternet {
    message = "인터넷 연결을 확인하세요"
} catch let error as URLError where error.code == .cancelled {
    // 화면을 벗어나 취소된 것. 오류로 표시하지 않는다
} catch APIError.http(let status, _) where status == 401 {
    message = "다시 로그인하세요"
} catch {
    message = "잠시 후 다시 시도하세요"
}
```

## 타임아웃, 취소, 재시도

- **타임아웃**: `URLRequest.timeoutInterval`(기본 60초)은 데이터가 오가지 않는 시간의 한도다. 전체 요청 시간 한도는 `URLSessionConfiguration.timeoutIntervalForResource`로 정한다.
- **취소**: `async` 함수를 실행 중인 `Task`를 취소하면 URLSession 요청도 취소되고 `URLError.cancelled`가 던져진다. SwiftUI의 `.task` 수정자는 화면이 사라질 때 자동으로 취소한다([Task 취소]({{ '/swift/concurrency/task-cancellation/' | relative_url }})).
- **재시도**: 타임아웃이나 5xx는 잠시 기다렸다 다시 시도할 만하다. 단, POST처럼 상태를 바꾸는 요청은 서버가 이미 처리했을 수 있으므로, 서버가 멱등 키(같은 요청을 두 번 받아도 한 번만 처리하는 식별자)를 지원할 때만 자동 재시도한다.

## 서버 없이 테스트하기: URLProtocol

`URLProtocol`을 상속하면 URLSession의 요청을 가로채 원하는 응답을 돌려줄 수 있다.

```swift
final class StubProtocol: URLProtocol {
    nonisolated(unsafe) static var handler: ((URLRequest) -> (Int, Data))?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        let (status, data) = Self.handler!(request)
        let response = HTTPURLResponse(url: request.url!, statusCode: status,
                                       httpVersion: nil, headerFields: nil)!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: data)
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}
}

// 테스트
let config = URLSessionConfiguration.ephemeral
config.protocolClasses = [StubProtocol.self]
let api = TodoAPI(baseURL: URL(string: "https://test.local")!, session: URLSession(configuration: config))

StubProtocol.handler = { _ in (404, Data(#"{"detail":"할 일을 찾을 수 없습니다: 99"}"#.utf8)) }
// api.list()가 APIError.http(status: 404, ...)를 던지는지 확인
```

실제 서버나 네트워크 없이 성공, 404, 잘못된 JSON 같은 경우를 빠르게 재현할 수 있다. `handler`는 테스트 사이에 공유되는 정적 상태라 테스트를 병렬로 돌리지 않거나, 요청 URL로 응답을 구분하도록 만든다.

## App Transport Security

iOS는 기본적으로 `http://`(평문) 접속을 막고 TLS 1.2 이상의 HTTPS만 허용한다(ATS). 개발 중 로컬 서버(`http://localhost`)에 접속하려면 `Info.plist`의 ATS 예외 설정이 필요하지만, 배포 앱에서 예외를 넓게 열면 심사와 보안 모두에 문제가 된다. 서버는 HTTPS로 운영한다. TLS 연결이 맺어지는 과정은 [TLS 1.3 핸드셰이크]({{ '/pki/tls13/' | relative_url }})에, 인증서 검증을 더 엄격하게 하는 방법은 [TLS 피닝]({{ '/pki/ssl-pinning/' | relative_url }})에 있다.

## 정리

- `URLSession.shared.data(for:)`의 async API로 요청하고, 응답은 `Codable`로 변환한다. 서버의 날짜 형식에 디코더 전략을 맞춘다.
- URLSession은 HTTP 오류 상태에서 예외를 던지지 않으므로 상태 코드를 직접 확인한다.
- 오류는 전송(`URLError`), HTTP, 변환 세 종류로 나눠 사용자 안내를 다르게 한다. 취소는 오류로 표시하지 않는다.
- 상태를 바꾸는 요청은 멱등 키가 있을 때만 자동 재시도한다.
- `URLProtocol`로 서버 없이 테스트하고, ATS 예외는 최소로 둔다.

## 참고

- [Apple: URLSession](https://developer.apple.com/documentation/foundation/urlsession)
- [Apple: Fetching website data into memory](https://developer.apple.com/documentation/foundation/fetching-website-data-into-memory)
- [WWDC21: Use async/await with URLSession](https://developer.apple.com/videos/play/wwdc2021/10095/)
- [Apple: URLProtocol](https://developer.apple.com/documentation/foundation/urlprotocol)
