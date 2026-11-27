---
title: "MainActor와 UI 상태 관리"
parent: Concurrency
grand_parent: Swift
nav_order: 6
permalink: /swift/concurrency/main-actor/
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
date: 2026-11-16
description: "MainActor 격리와 UI 상태 소유권, Task의 문맥 상속과 무거운 연산 분리 원칙을 설명합니다."
first_written: 2026-11-16
last_modified_date: 2026-11-27
tags: [Swift, Concurrency, MainActor, UI]
---

# MainActor와 UI 상태 관리
{: .no_toc }

{% include article-toc.md %}

UIKit과 AppKit을 비롯한 UI 프레임워크는 화면 상태를 메인 실행 문맥에서 다루도록 요구한다. `MainActor`는 이 규칙을 Swift의 격리 모델로 표현한 전역 actor다. UI를 담당하는 타입에 `@MainActor`를 붙이면 컴파일러가 잘못된 접근을 찾아준다.

## UI 상태가 의미하는 것

목록 데이터, 로딩 표시, 오류 문구처럼 화면이 읽는 값이 UI 상태다. 이 값들이 여러 실행 흐름에서 무질서하게 바뀌면 이전 결과가 최신 화면을 덮거나 표시가 어긋날 수 있다.

`@MainActor`는 이런 상태의 소유 경계를 선언한다. 하지만 함수에 붙였다고 무거운 계산이 가벼워지는 것은 아니다. 예제에서는 ‘어디서 상태를 바꾸는가’와 ‘어디서 오래 계산하는가’를 각각 확인하자.

## 화면 상태를 타입 단위로 격리하기

ViewModel 전체가 화면 상태를 관리한다면 타입에 한 번 표시하는 편이 가장 명확하다.

```swift
@MainActor
final class ProfileViewModel {
    private(set) var name = ""
    private(set) var isLoading = false
    private(set) var errorMessage: String?

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let profile = try await ProfileService().fetchProfile()
            name = profile.name
        } catch is CancellationError {
            // 화면이 사라져 취소된 경우에는 오류 문구를 띄우지 않는다.
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
```

`load()`가 네트워크 응답을 기다리는 동안 MainActor를 계속 붙잡는 것은 아니다. `await`에서 Task가 중단되고 MainActor는 다른 UI 작업을 실행할 수 있다. 응답 뒤의 `name` 변경은 다시 MainActor에 격리된 상태에서 실행된다.

## 격리 밖에서 호출하면 await가 필요하다

MainActor에 격리되지 않은 코드에서 ViewModel을 사용하면 actor 경계를 건너야 한다.

```swift
func refresh(_ viewModel: ProfileViewModel) async {
    await viewModel.load()
}
```

호출 지점의 `await`는 실행 문맥이 MainActor로 전환될 수 있다는 뜻이다. 반대로 이미 MainActor에 격리된 메서드끼리는 동기 접근에 `await`가 필요하지 않다.

## 선언으로 의도를 남기기

기존 completion handler 코드에서는 다음처럼 필요한 부분만 메인 큐로 보내는 방식이 흔했다.

```swift
DispatchQueue.main.async {
    self.title = title
}
```

Concurrency 코드에서는 UI를 소유한 타입이나 메서드에 `@MainActor`를 선언하는 편이 낫다. 어느 상태가 보호되는지 타입에 남고, 호출을 빠뜨리면 컴파일러가 알려주기 때문이다.

일부 코드만 MainActor에서 실행해야 한다면 `MainActor.run`을 사용할 수 있다.

```swift
func loadTitle() async throws {
    let title = try await service.fetchTitle()

    await MainActor.run {
        self.title = title
    }
}
```

이는 기존 코드를 단계적으로 옮길 때 유용하다. 하지만 한 타입의 여러 프로퍼티가 모두 UI 상태라면, 매번 `MainActor.run`으로 감싸기보다 타입 전체에 `@MainActor`를 붙이는 편이 보호 범위를 이해하기 쉽다.

## MainActor의 Task는 백그라운드 버튼이 아니다

`Task { }`는 만들어진 곳의 actor 문맥을 이어받는다.

```swift
@MainActor
func didTapRefresh() {
    Task {
        // 이 Task는 MainActor 격리를 이어받는다.
        await viewModel.load()
    }
}
```

네트워크처럼 비동기 API를 기다리는 일은 문제없다. 기다리는 동안 MainActor가 양보되기 때문이다. 그러나 동기적인 이미지 변환이나 대규모 JSON 계산을 이 Task 안에서 오래 실행하면 여전히 UI 반응을 막는다.

```swift
@MainActor
func makeThumbnail(from data: Data) async throws -> Image {
    // Task { }로 감싸도 CPU 연산 자체가 자동으로 다른 곳으로 이동하지 않는다.
    try await imageProcessor.thumbnail(from: data)
}
```

무거운 계산은 UI 타입에서 분리한 서비스에 맡기고, 결과만 MainActor로 가져오는 구조가 좋다. Swift 6.2에서는 명시적으로 동시 실행기에서 실행할 비동기 함수에 `@concurrent`를 사용할 수 있다. 다만 이 문법은 프로젝트의 Swift 버전과 격리 설정을 확인한 뒤 도입해야 한다.

## MainActor와 메인 스레드

Apple 플랫폼에서 MainActor의 실행기는 메인 스레드와 연결된다. 그래도 애플리케이션 코드는 “현재 스레드가 무엇인가”보다 “이 선언이 어느 actor에 격리되어 있는가”를 기준으로 설계하는 편이 안전하다.

- `@MainActor`는 타입과 함수의 **격리 계약**이다.
- `Thread.isMainThread` 검사는 현재 순간의 실행 위치만 알려준다.
- `DispatchQueue.main.async`는 큐에 작업을 보내지만 타입의 상태를 컴파일러가 보호하게 하지는 않는다.

## 흔한 실수

### 모든 비동기 함수에 @MainActor 붙이기

UI와 관계없는 네트워크 계층이나 저장소까지 MainActor에 넣으면 격리 경계가 불필요하게 커진다. UI 상태의 소유자에만 붙이고, 서비스는 독립된 값이나 actor로 설계한다.

### await가 곧 백그라운드 실행이라고 생각하기

`await`는 중단 가능 지점이다. 호출한 함수가 어디서 실행되는지는 해당 함수의 격리 선언에 따라 결정된다.

### Task.detached로 UI 상태 바꾸기

detached task는 MainActor 문맥을 이어받지 않는다. UI 상태를 변경하려면 MainActor 경계를 명시적으로 건너야 하고, 대개는 detached task 자체가 필요하지 않다.

## 주요 API

| API | 역할 |
| --- | --- |
| `@MainActor` | 타입·함수·프로퍼티를 메인 actor에 격리 |
| `MainActor.run { }` | 메인 actor에서 클로저를 실행하고 결과를 받는다 |
| `Task { @MainActor in }` | 메인 actor에서 시작하는 작업 |
| `MainActor.assumeIsolated { }` | 이미 메인에서 실행 중임을 확인하고 동기적으로 접근 |
| `nonisolated` | 메인 actor 타입 안에서 격리를 해제한 멤버 |
| `DispatchQueue.main.async` | GCD 방식의 메인 큐 전달. 컴파일러 격리 검사는 받지 않는다 |

## 정리

- `MainActor`는 UI 상태에 맞는 전역 actor다.
- ViewModel처럼 UI 상태를 소유한 타입 전체에 `@MainActor`를 붙이면 보호 범위가 선명해진다.
- MainActor의 async 함수도 `await` 중에는 다른 UI 작업에 실행 기회를 준다.
- MainActor에서 만든 `Task { }`는 actor 문맥을 이어받으므로 CPU 작업을 자동으로 백그라운드로 보내지 않는다.
- 무거운 계산은 별도 서비스로 분리하고 결과만 UI 격리 영역으로 가져온다.

## 다음 편

마지막 편에서는 actor 사이를 오가는 값이 안전한지 표현하는 `Sendable`과 Swift 6의 엄격한 동시성 검사를 정리한다.

→ [Sendable과 Swift 6 동시성 검사]({{ '/swift/concurrency/sendable-swift-6/' | relative_url }})

## 참고

- [The Swift Programming Language: Global Actors](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/#Global-Actors)
- [Swift Evolution SE-0316: Global Actors](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0316-global-actors.md)
- [Swift 6.2 Released](https://www.swift.org/blog/swift-6.2-released/)
- [Swift Evolution SE-0461: Run nonisolated async functions on the caller's actor by default](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0461-async-function-isolation.md)
