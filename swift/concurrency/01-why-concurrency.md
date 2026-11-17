---
title: "Swift Concurrency 실행 모델"
parent: Concurrency
grand_parent: Swift
nav_order: 1
permalink: /swift/concurrency/why-concurrency/
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
date: 2026-11-16
description: "Swift Concurrency의 중단과 재개, Task 실행 단위, 콜백과 async/await의 차이를 분석합니다."
first_written: 2026-11-16
last_modified_date: 2026-11-17
tags: [Swift, Concurrency, Async-Await]
---

# Swift Concurrency 실행 모델
{: .no_toc }

{% include article-toc.md %}

앱은 네트워크 응답, 파일 읽기, 데이터베이스 조회처럼 **결과가 바로 나오지 않는 일**을 자주 한다. 결과를 기다리는 동안 메인 스레드를 막으면 화면이 멈춘다. 그렇다고 모든 작업을 직접 스레드와 큐로 관리하면 실행 순서, 오류, 취소, 공유 상태를 함께 추적하기가 어려워진다.

Swift Concurrency는 이 문제를 언어 차원에서 다룬다. 핵심 도구는 `async`/`await`, Task, actor다.

{: .note }
GCD의 `sync`/`async`, Serial/Concurrent Queue가 아직 헷갈린다면 [GCD와 DispatchQueue]({{ '/swift/concurrency/gcd-queue-basics/' | relative_url }})부터 읽는 것을 권한다.

## 먼저 떠올릴 상황

새로고침 버튼을 눌렀을 때 서버 응답이 늦어도 스크롤은 계속 움직여야 한다. ‘요청 결과를 기다리는 일’과 ‘화면 이벤트를 처리하는 일’을 함께 진행할 수 있어야 하기 때문이다.

본문의 `Profile`, `requestProfile`, `show`는 앱마다 달라지는 데이터와 동작을 표현한 예시 이름이다. 그대로 복사해 실행할 완성 앱은 아니다. 먼저 호출 순서를 이해하고 다음 편의 구체적인 네트워크 예제로 연결하자.

## 동기 코드가 화면을 멈추는 이유

동기 함수는 결과가 나올 때까지 호출한 쪽을 붙잡는다.

```swift
func loadProfileSynchronously() -> Profile {
    // 네트워크가 끝날 때까지 현재 스레드를 점유한다고 가정
    requestProfile()
}

let profile = loadProfileSynchronously()
show(profile)
```

이 코드가 메인 스레드에서 실행되고 네트워크에 2초가 걸리면, 그동안 터치 처리와 화면 그리기도 멈춘다. 오래 걸리는 작업은 **기다리는 동안 실행 자원을 양보**할 수 있어야 한다.

## 콜백으로 해결했을 때의 문제

오래된 비동기 API는 완료 클로저로 결과를 돌려주는 경우가 많다.

```swift
func loadProfile(
    completion: @escaping (Result<Profile, Error>) -> Void
) {
    requestProfile { result in
        completion(result)
    }
}

loadProfile { result in
    switch result {
    case .success(let profile):
        loadPosts(userID: profile.id) { postsResult in
            switch postsResult {
            case .success(let posts):
                show(profile: profile, posts: posts)
            case .failure(let error):
                show(error)
            }
        }
    case .failure(let error):
        show(error)
    }
}
```

콜백 자체가 잘못된 것은 아니다. 하지만 작업이 이어질수록 코드가 안쪽으로 깊어지고, 각 단계의 오류 처리와 취소를 직접 연결해야 한다. 함수가 종료된 뒤 클로저가 실행되므로 값의 수명과 캡처도 따로 생각해야 한다.

## async/await로 같은 흐름 표현하기

비동기 함수에는 `async`, 호출 지점에는 `await`를 표시한다.

```swift
func loadProfile() async throws -> Profile {
    try await requestProfile()
}

func loadScreen() async {
    do {
        let profile = try await loadProfile()
        let posts = try await loadPosts(userID: profile.id)
        show(profile: profile, posts: posts)
    } catch {
        show(error)
    }
}
```

코드가 위에서 아래로 읽히고, 반환값과 `throw`를 동기 함수처럼 사용할 수 있다. `await`에서 함수는 잠시 멈출 수 있지만 **스레드를 붙잡고 기다리지는 않는다.** 기다리는 일이 끝나면 런타임이 Task를 다시 실행한다.

{: .tip }
`await`는 “여기서 스레드를 멈춘다”가 아니라 “이 함수가 여기서 중단되고 나중에 이어질 수 있다”는 표시다.

## 비동기와 동시성, 병렬성 구분하기

세 용어는 비슷하지만 초점이 다르다.

| 용어 | 뜻 | 예 |
| --- | --- | --- |
| 비동기 | 결과를 기다리는 동안 다른 일을 할 수 있음 | 네트워크 응답 기다리기 |
| 동시성 | 여러 작업의 진행 시간을 겹쳐 관리함 | 사진 여러 장 내려받기 |
| 병렬성 | 여러 코어가 같은 순간에 실제 계산함 | 큰 이미지 여러 장 처리하기 |

`async` 함수를 두 번 순서대로 `await`하면 여전히 순차 실행이다.

```swift
let profile = try await loadProfile()
let settings = try await loadSettings()
```

두 번째 작업은 첫 번째가 끝난 뒤 시작한다. 서로 의존하지 않는 작업을 함께 시작하려면 `async let`이나 TaskGroup이 필요하다. 4편에서 다룬다.

## Task가 실제 실행 단위다

모든 비동기 함수는 어떤 Task 안에서 실행된다. 함수가 다른 `async` 함수를 호출해도 자동으로 새 Task가 생기지는 않는다. 호출자와 피호출자는 같은 Task의 흐름을 이어 간다.

```swift
Task {
    await loadScreen()
}
```

동기 코드에서 비동기 세계로 들어갈 때 `Task`를 만들 수 있다. Task는 우선순위, 취소 상태, task-local 값 같은 실행 문맥도 가진다.

## Swift Concurrency가 해결하려는 것

- 중첩 콜백을 순차 코드처럼 읽게 한다.
- 부모와 자식 작업의 관계를 만들어 완료와 취소를 추적한다.
- actor로 공유 가변 상태를 격리한다.
- `Sendable` 검사로 격리 영역 사이의 위험한 값 전달을 막는다.
- Swift 6 언어 모드에서는 잠재적인 데이터 경쟁을 컴파일 오류로 찾는다.

{: .warning }
Swift Concurrency를 사용한다고 모든 코드가 자동으로 빠르거나 안전해지는 것은 아니다. `await` 사이에서 상태가 바뀔 수 있고, 취소는 협력적으로 동작하며, 잘못 만든 무제한 Task는 자원을 과하게 쓸 수 있다. 뒤의 글에서 하나씩 확인한다.

## 정리

- 오래 걸리는 작업을 메인 스레드에서 동기로 기다리면 UI가 멈춘다.
- `async` 함수는 중단될 수 있고, `await`는 그 가능성이 있는 호출 지점이다.
- `async`/`await`는 콜백 흐름을 반환값과 오류 처리로 다시 표현한다.
- `async`만 붙인다고 여러 일이 동시에 시작되지는 않는다.
- 비동기 코드는 Task 안에서 실행된다.

## 다음 편

다음 편에서는 `async throws` 함수를 직접 만들고 호출하면서, `await`의 실행 순서와 기존 콜백 API를 continuation으로 연결하는 방법을 다룬다.

→ [async/await와 비동기 함수]({{ '/swift/concurrency/async-await/' | relative_url }})

## 참고

- [The Swift Programming Language: Concurrency](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/)
- [Swift Evolution SE-0296: Async/await](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0296-async-await.md)
- [Swift Evolution SE-0304: Structured Concurrency](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0304-structured-concurrency.md)
