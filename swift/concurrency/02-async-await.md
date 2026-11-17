---
title: "2. async/await 기초: 기다리는 함수 만들고 부르기"
parent: Concurrency
grand_parent: Swift
nav_order: 2
permalink: /swift/concurrency/async-await/
first_written: 2026-11-16
last_modified_date: 2026-11-16
tags: [Swift, Concurrency, Async-Await, Continuation]
---

# async/await 기초: 기다리는 함수 만들고 부르기
{: .no_toc }

{% include article-toc.md %}

`async`는 함수가 실행 중 중단될 수 있음을 선언하고, `await`는 그 함수를 호출하는 곳에 중단 가능성을 표시한다. 오류까지 발생할 수 있다면 `async throws`로 선언한다.

## async 함수 선언하기

```swift
func fetchName() async -> String {
    "yep"
}

func fetchUser() async throws -> User {
    try await api.user()
}
```

선언 순서는 매개변수 뒤에 `async`, 그다음 `throws`, 반환 화살표다.

```text
func 이름() async throws -> 반환형
```

호출할 때도 같은 의미가 드러난다.

```swift
let name = await fetchName()
let user = try await fetchUser()
```

`try`는 실패 가능성, `await`는 중단 가능성을 나타낸다. 둘의 작성 순서는 `try await`다.

## await 전후의 실행 순서

한 Task 안의 코드는 기본적으로 순서대로 진행된다.

```swift
func load() async throws {
    print("A")
    let user = try await fetchUser()
    print("B: \(user.name)")
}
```

항상 A가 먼저, B가 나중에 출력된다. `await` 동안 같은 스레드가 계속 묶여 있지는 않지만, `fetchUser()`의 결과가 준비되기 전에는 다음 줄로 가지 않는다.

또한 중단 전과 재개 후의 스레드가 같다고 가정하면 안 된다. Swift 코드에서는 “어느 스레드인가”보다 “어느 actor에 격리되어 있는가”를 기준으로 안전성을 판단한다.

## URLSession과 Decodable 예제

Foundation의 `URLSession`은 async API를 제공한다.

```swift
import Foundation

struct User: Decodable, Sendable {
    let id: Int
    let name: String
}

enum APIError: Error {
    case invalidResponse
}

func fetchUser(from url: URL) async throws -> User {
    let (data, response) = try await URLSession.shared.data(from: url)

    guard let http = response as? HTTPURLResponse,
          (200..<300).contains(http.statusCode) else {
        throw APIError.invalidResponse
    }

    return try JSONDecoder().decode(User.self, from: data)
}
```

네트워크 오류와 디코딩 오류는 모두 `throw`되어 호출자가 한곳에서 처리할 수 있다.

```swift
func printUser(from url: URL) async {
    do {
        let user = try await fetchUser(from: url)
        print(user.name)
    } catch is CancellationError {
        print("작업 취소")
    } catch {
        print("불러오기 실패: \(error)")
    }
}
```

취소를 일반 오류와 구분하면 취소된 화면에서 불필요한 오류 알림을 띄우지 않을 수 있다.

## async 함수는 어디서 호출할 수 있나

`await`는 이미 비동기 문맥인 `async` 함수나 Task 안에서 사용한다.

```swift
func refresh() async {
    let name = await fetchName()
    print(name)
}

Task {
    await refresh()
}
```

동기 함수에 무조건 `Task`를 추가하기보다, 가능하면 호출 체인을 `async`로 유지한다. 그래야 상위 작업이 완료와 취소를 구조적으로 기다릴 수 있다. 이벤트 핸들러처럼 동기 세계와 맞닿는 경계에서 Task를 만드는 것이 자연스럽다.

## 순차 실행이 필요한 경우

두 번째 작업이 첫 번째 결과를 요구하면 순차 `await`가 맞다.

```swift
let user = try await fetchUser()
let posts = try await fetchPosts(userID: user.id)
```

반대로 두 작업이 서로 독립적이라면 이 코드는 불필요하게 오래 걸린다.

```swift
let profile = try await fetchProfile()
let notices = try await fetchNotices()
```

둘을 함께 시작하는 방법은 4편의 `async let`에서 다룬다. 먼저 데이터 의존성이 있는지 확인한 뒤 병렬화를 선택해야 한다.

## 콜백 API를 continuation으로 연결하기

기존 완료 클로저 API가 async 버전을 제공하지 않는다면 checked continuation을 사용할 수 있다.

```swift
func requestToken() async throws -> String {
    try await withCheckedThrowingContinuation { continuation in
        legacyRequestToken { result in
            continuation.resume(with: result)
        }
    }
}
```

`withCheckedThrowingContinuation`은 콜백의 `Result`를 async 함수의 반환 또는 오류로 바꾼다.

{: .warning }
continuation은 모든 경로에서 **정확히 한 번** `resume`해야 한다. 한 번도 호출하지 않으면 Task가 영원히 기다리고, 두 번 호출하면 잘못된 동작이다. 직접 제어하지 않는 API를 감쌀 때는 성공·실패·취소 경로를 모두 확인한다.

continuation은 비동기 작업을 새로 만드는 도구가 아니다. 이미 비동기인 콜백 API와 async/await 사이를 연결하는 다리다.

## async가 필요 없는 함수

계산을 바로 끝내고 중단할 이유가 없다면 동기 함수로 둔다.

```swift
func displayName(first: String, last: String) -> String {
    "\(first) \(last)"
}
```

“나중에 필요할 것 같아서” 모든 함수에 `async`를 붙이면 호출자까지 불필요하게 비동기화된다. 네트워크, 파일 I/O, actor 전환처럼 실제 중단 지점이 있거나 비동기 API를 호출할 때 사용한다.

## 정리

- 비동기 함수는 `async`, 실패도 가능하면 `async throws`로 선언한다.
- 호출 지점에는 `await`와 필요할 경우 `try`를 쓴다.
- `await` 전후의 코드 순서는 유지되지만 같은 스레드에서 재개된다고 가정하지 않는다.
- 의존하는 작업은 순서대로 기다리고, 독립 작업만 함께 실행한다.
- 콜백 API는 checked continuation으로 연결하되 정확히 한 번 재개한다.

## 다음 편

다음 편에서는 Task를 직접 만들고, 결과를 기다리고, 화면이나 검색 조건이 바뀌었을 때 작업을 취소하는 방법을 다룬다.

→ [3. Task: 비동기 작업 시작하고 취소하기]({{ '/swift/concurrency/task-cancellation/' | relative_url }})

## 참고

- [The Swift Programming Language: Concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/)
- [Swift Evolution SE-0296: Async/await](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0296-async-await.md)
- [Swift Evolution SE-0300: Continuations](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0300-continuation.md)
