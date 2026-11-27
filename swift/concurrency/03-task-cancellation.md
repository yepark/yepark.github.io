---
title: "Task 수명과 취소"
parent: Concurrency
grand_parent: Swift
nav_order: 3
permalink: /swift/concurrency/task-cancellation/
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
date: 2026-11-16
description: "Task 생성과 수명, 구조화된 동시성, 협력적 취소와 검색 작업의 최신 결과 보장 방법을 설명합니다."
first_written: 2026-11-16
last_modified_date: 2026-11-27
tags: [Swift, Concurrency, Task, Cancellation]
---

# Task 수명과 취소
{: .no_toc }

{% include article-toc.md %}

Task는 Swift 비동기 코드의 실행 단위다. 모든 async 함수는 Task 안에서 실행되며, 동기 코드에서 비동기 작업을 시작해야 할 때 `Task { }`를 만들 수 있다.

## 작업을 시작한 뒤의 수명 생각하기

검색창에서 ‘스’를 입력한 뒤 곧바로 ‘스위프트’로 고쳤다고 하자. 첫 검색 결과는 더 이상 필요하지 않을 수 있다. 어떤 작업을 취소할지 알려면 시작할 때 반환된 Task 참조를 보관해야 한다.

`cancel()`은 강제 종료 버튼이 아니라 취소 상태를 알리는 요청이다. 실행 중인 함수가 그 상태를 확인하거나 취소를 지원하는 API에서 오류를 받아야 흐름을 멈출 수 있다. 아래 코드는 시작·참조 보관·취소 요청·취소 확인 순서로 읽자.

## Task 만들기

```swift
let task = Task {
    try await fetchUser()
}
```

클로저의 반환값과 오류 형식에 따라 `task`의 타입이 정해진다. 위 코드는 개념적으로 `Task<User, Error>`다.

결과가 필요하면 `value`를 기다린다.

```swift
do {
    let user = try await task.value
    print(user.name)
} catch {
    print(error)
}
```

`Task { }`는 현재 actor 격리, 우선순위, task-local 값 같은 문맥을 이어받는다. 특히 `@MainActor` 안에서 만든 Task의 클로저도 MainActor에 격리될 수 있다. Task를 만들었다고 무조건 백그라운드 스레드로 이동하는 것은 아니다.

## 구조화된 작업과 구조화되지 않은 Task

`async let`과 TaskGroup의 자식 작업은 부모 범위가 끝나기 전에 모두 완료되고, 취소와 우선순위가 계층을 따라 전파되는 **구조화된 동시성**이다.

반면 `Task { }`로 만든 작업은 생성한 함수의 범위를 벗어나 계속 실행할 수 있는 구조화되지 않은 작업이다. 핸들을 저장하지 않으면 완료나 취소를 추적하기 어렵다.

```swift
func startAndForget() {
    Task {
        await sendAnalytics()
    }
    // 함수는 Task 완료를 기다리지 않고 끝난다.
}
```

버튼 탭, 화면 생명주기, delegate 메서드처럼 동기 API에서 async 코드로 들어가는 경계에서는 유용하다. 하지만 async 함수 안에서 단순히 `Task`를 만들고 잊기보다 직접 `await`하거나 TaskGroup으로 관계를 표현하는 편이 좋다.

## 취소는 요청이다

```swift
let task = Task {
    try await downloadLargeFile()
}

task.cancel()
```

`cancel()`은 작업을 즉시 강제 종료하지 않는다. Task의 취소 상태를 표시하고, 작업이 그 상태를 확인해 스스로 멈추는 **협력적 취소**다.

취소를 확인하는 대표적인 방법은 두 가지다.

```swift
if Task.isCancelled {
    return partialResult
}

try Task.checkCancellation()
```

- `Task.isCancelled`는 상태만 확인한다.
- `Task.checkCancellation()`은 취소됐다면 `CancellationError`를 던진다.

`Task.sleep`처럼 일부 async API도 기다리는 중 취소되면 오류를 던진다.

## 긴 반복 작업에 취소 지점 넣기

CPU 계산에는 자연스러운 `await`가 없을 수 있다. 반복문 중간에 취소를 확인해야 한다.

```swift
func makeThumbnails(_ images: [Image]) async throws -> [Thumbnail] {
    var result: [Thumbnail] = []

    for image in images {
        try Task.checkCancellation()
        result.append(resize(image))
    }

    return result
}
```

매 반복마다 확인하는 비용이 부담되는 아주 작은 연산이라면 일정 횟수마다 검사할 수 있다. 핵심은 사용자가 화면을 떠났는데도 큰 계산이 끝까지 계속되지 않게 만드는 것이다.

## 검색 입력 디바운스 예제

사용자가 새 글자를 입력할 때 이전 검색을 취소하는 패턴이다.

```swift
import Foundation

@MainActor
final class SearchModel {
    private var searchTask: Task<Void, Never>?
    private var latestRequestID = UUID()
    private let requestSearch: @Sendable (String) async throws -> [String]
    private(set) var results: [String] = []

    init(requestSearch: @escaping @Sendable (String) async throws -> [String]) {
        self.requestSearch = requestSearch
    }

    func search(text: String) {
        searchTask?.cancel()
        let requestID = UUID()
        latestRequestID = requestID

        searchTask = Task { [weak self, requestSearch] in
            do {
                try await Task.sleep(for: .milliseconds(300))
                let newResults = try await requestSearch(text)
                try Task.checkCancellation()
                guard let self, self.latestRequestID == requestID else {
                    return
                }
                self.results = newResults
            } catch is CancellationError {
                // 새 검색이 시작된 정상적인 흐름
            } catch {
                // 취소가 다른 오류 타입으로 전달되거나 오래된 요청이 실패해도
                // 최신 검색의 결과를 지우지 않는다.
                guard !Task.isCancelled,
                      let self, self.latestRequestID == requestID else {
                    return
                }
                self.results = []
            }
        }
    }

    func cancelSearch() {
        latestRequestID = UUID()
        searchTask?.cancel()
        searchTask = nil
    }

    deinit {
        searchTask?.cancel()
    }
}
```

새 입력이 오면 이전 Task를 취소한다. 300ms 안에 새 입력이 들어오면 `Task.sleep`이 `CancellationError`를 던져 네트워크 요청까지 가지 않는다. 요청 API가 취소를 지원하면 실행 중인 네트워크 작업에도 취소가 전달될 수 있다.

`requestSearch`는 생성할 때 전달하는 검색 함수다. 예를 들어 `SearchModel(requestSearch: service.search)`처럼 실제 서비스와 연결한다. 이렇게 분리하면 화면 상태 관리와 서버 통신을 따로 시험할 수 있다.

### 취소와 최신 결과 보장은 다른 문제다

두 요청의 완료 순서는 시작 순서와 다를 수 있다.

| 순서 | 사건 | 지켜야 할 동작 |
| --- | --- | --- |
| 1 | “스” 검색 A 시작 | A의 식별자를 보관 |
| 2 | “스위프트” 검색 B 시작 | A 취소 요청, 최신 식별자를 B로 교체 |
| 3 | B 성공 | 화면에 B 결과 표시 |
| 4 | A가 뒤늦게 성공하거나 실패 | B 결과를 덮거나 지우지 않음 |

`cancel()`은 A가 즉시 멈췄다고 보장하지 않는다. 그래서 성공 경로에는 취소 검사와 식별자 확인을, 실패 경로에도 최신 요청 확인을 둔다. 네트워크 라이브러리는 취소를 `CancellationError`가 아닌 `URLError.cancelled` 같은 자체 오류로 알릴 수 있다. `catch is CancellationError`만 처리하고 나머지 오류에서 무조건 결과를 지우면 이전 요청의 실패가 최신 화면을 비울 수 있다.

`[weak self]`는 검색을 기다리는 동안 모델을 불필요하게 계속 살려 두지 않기 위해 사용했다. 화면 소유자는 종료 시점에 `cancelSearch()`도 호출한다. 모델이 화면 밖에서 계속 보관될 수 있으므로 `deinit`만을 화면 이탈의 신호로 삼지 않는다.

## Task.detached는 언제 쓰나

```swift
let task = Task.detached(priority: .utility) {
    calculateReport()
}
```

detached Task는 생성한 곳의 actor 격리와 task-local 문맥을 이어받지 않는다. 캡처한 값도 격리 영역을 건너므로 `Sendable`이어야 한다. 문맥 상속을 끊어야 할 명확한 이유가 없다면 일반 `Task`나 구조화된 자식 작업을 우선한다.

{: .warning }
`Task.detached`를 “백그라운드 실행 버튼”처럼 사용하면 actor 상태를 우회하거나 취소 관계를 잃기 쉽다. CPU 작업을 UI 격리에서 분리하려면 별도 서비스의 격리를 설계하고, Swift 6.2에서는 `@concurrent` 같은 명시적 모델도 검토한다.

## 오류를 삼키지 않기

`Task { try await work() }`의 핸들을 저장하지 않고 `value`도 기다리지 않으면 발생한 오류를 관찰하기 어렵다. 오류가 중요한 작업은 다음 중 하나로 책임을 분명히 한다.

- 상위 async 함수가 `try await`한다.
- Task 핸들을 저장하고 `value`를 기다린다.
- Task 내부에서 오류를 잡아 사용자 상태나 로그로 남긴다.

## 주요 API

| API | 역할 |
| --- | --- |
| `Task { }` | 현재 actor와 우선순위를 이어받는 비구조화 작업 |
| `Task.detached { }` | 현재 문맥을 이어받지 않는 작업 |
| `task.cancel()` | 취소 요청. 작업이 스스로 확인해야 멈춘다 |
| `task.value` | 작업 결과를 기다려 받는다 |
| `Task.isCancelled` | 취소 요청 여부 확인 |
| `Task.checkCancellation()` | 취소됐으면 `CancellationError`를 던진다 |
| `Task.sleep(for:)` | 기다리는 중에도 취소에 반응한다 |
| `withTaskCancellationHandler(operation:onCancel:)` | 취소 순간 정리 코드를 실행 |

## 정리

- Task는 async 코드가 실행되는 단위다.
- `Task { }`는 현재 actor 문맥을 이어받지만 부모 범위에 묶인 자식 작업은 아니다.
- 취소는 강제 종료가 아니라 협력적인 요청이다.
- 긴 작업은 `Task.checkCancellation()` 또는 `Task.isCancelled`로 반응한다.
- `Task.detached`는 문맥과 격리를 끊어야 할 때만 제한적으로 사용한다.

## 다음 편

다음 편에서는 서로 독립적인 여러 작업을 실제로 함께 시작하는 `async let`과 TaskGroup을 비교한다.

→ [구조화된 동시성과 TaskGroup]({{ '/swift/concurrency/parallel-work/' | relative_url }})

## 참고

- [The Swift Programming Language: Tasks and Task Groups](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/#Tasks-and-Task-Groups)
- [Swift Evolution SE-0304: Structured Concurrency](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0304-structured-concurrency.md)
- [Swift Evolution SE-0317: async let](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0317-async-let.md)
