---
title: "Sendable과 Swift 6 동시성 검사"
parent: Concurrency
grand_parent: Swift
nav_order: 7
permalink: /swift/concurrency/sendable-swift-6/
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
date: 2026-11-16
description: "Sendable과 @Sendable 캡처 검사, Swift 6 언어 모드와 동시성 마이그레이션 경계를 설명합니다."
first_written: 2026-11-16
last_modified_date: 2026-11-17
tags: [Swift, Concurrency, Sendable, Swift-6]
---

# Sendable과 Swift 6 동시성 검사
{: .no_toc }

{% include article-toc.md %}

actor가 자기 상태를 안전하게 보호해도, actor나 Task 사이로 안전하지 않은 참조를 넘기면 다시 데이터 경쟁이 생길 수 있다. `Sendable`은 값이 하나의 동시성 격리 영역에서 다른 영역으로 안전하게 전달될 수 있음을 나타내는 프로토콜이다.

Swift 6 언어 모드는 이 경계를 엄격하게 검사해, 잠재적인 데이터 경쟁을 컴파일 오류로 다룬다.

## 안전하게 넘긴다는 말의 의미

값을 다른 작업에 넘겼는데 원래 작업도 같은 내부 데이터를 바꿀 수 있다면 동시 접근 문제가 생길 수 있다. `Sendable`은 이런 경계를 넘어 전달해도 안전하도록 설계된 타입이라는 약속이다.

구조체라고 내부가 자동으로 전부 안전한 것은 아니다. 구조체가 변경 가능한 클래스 참조를 보관하면 그 참조도 함께 검토해야 한다. 컴파일 오류를 만나면 먼저 어떤 값이 어느 격리 영역에서 어디로 넘어가는지 찾아보자.

## 값 타입과 Sendable

저장 프로퍼티가 모두 `Sendable`인 구조체와 열거형은 안전하게 전달할 수 있다.

```swift
struct User: Sendable {
    let id: UUID
    let name: String
}

enum LoadingState: Sendable {
    case idle
    case loading
    case loaded(User)
}
```

`UUID`, `String`과 위의 `User`가 Sendable이므로 `LoadingState`도 Sendable 조건을 만족한다. 값 타입은 전달할 때 독립된 값처럼 다루기 쉬워 동시성 경계에서 좋은 기본 선택이다.

```swift
struct UnsafeContainer: Sendable {
    var object: NSMutableString // Sendable이 아닌 변경 가능한 참조
}
```

반면 변경 가능한 참조를 저장하면 컴파일러가 경고하거나 Swift 6 언어 모드에서 오류를 낸다. 선언에 `Sendable`만 붙인다고 내부 참조가 안전해지는 것은 아니다.

## 변경 가능한 클래스가 위험한 이유

클래스 인스턴스를 두 Task에 넘기면 두 곳이 같은 객체를 가리킨다.

```swift
final class Session {
    var token: String = ""
}
```

두 Task가 `token`을 동시에 변경할 수 있으므로 이 클래스는 그대로 Sendable일 수 없다. 해결 방향은 상태의 성격에 따라 다르다.

- 전달용 데이터라면 불변 `struct`로 바꾼다.
- 공유 가변 상태라면 `actor`가 소유하게 한다.
- UI 상태라면 `@MainActor`에 격리한다.
- 클래스가 꼭 필요하고 완전히 불변이라면 `final` 클래스와 `let` 프로퍼티로 모델링한다.
- lock 기반 구현이 필요하다면 모든 접근을 실제로 동기화한다.

actor 타입은 자체 격리로 가변 상태를 보호하므로 암시적으로 Sendable이다.

```swift
actor TokenStore {
    private var token = ""

    func update(_ newValue: String) {
        token = newValue
    }

    func current() -> String {
        token
    }
}
```

## @Sendable 클로저

Task처럼 동시에 실행될 수 있는 곳에 전달되는 클로저에는 `@Sendable` 제약이 붙을 수 있다.

```swift
func perform(
    operation: @escaping @Sendable () async -> Void
) -> Task<Void, Never> {
    Task {
        await operation()
    }
}
```

`@Sendable` 클로저는 캡처한 값도 안전해야 한다. 변경 가능한 지역 변수나 Sendable이 아닌 클래스 인스턴스를 여러 Task가 공유하도록 캡처하면 컴파일러가 문제를 지적한다.

```swift
func startJobs() async {
    var total = 0

    await withTaskGroup(of: Void.self) { group in
        for _ in 0..<10 {
            group.addTask {
                // total += 1  // 여러 자식 Task의 동시 변경이라 허용되지 않는다.
            }
        }
    }
}
```

결과를 Task에서 반환하고 부모 Task가 모으거나, 공유 집계를 actor에 맡기면 된다.

```swift
func totalScore() async -> Int {
    await withTaskGroup(of: Int.self, returning: Int.self) { group in
        for index in 0..<10 {
            group.addTask {
                await score(for: index)
            }
        }

        var total = 0
        for await score in group {
            total += score
        }
        return total
    }
}
```

## @unchecked Sendable은 마지막 수단

컴파일러가 내부 동기화 구현을 확인할 수 없을 때 `@unchecked Sendable`로 개발자가 안전성을 직접 보증할 수 있다.

```swift
final class LockedCache: @unchecked Sendable {
    // 모든 읽기와 쓰기가 동일한 lock으로 보호된 구현이어야 한다.
}
```

이 선언은 검사를 끄는 버튼이 아니다. 누락된 lock이나 외부로 새어 나간 변경 가능한 참조가 있으면 컴파일은 성공해도 데이터 경쟁은 남는다. 검증된 lock 기반 구현처럼 명확한 불변식이 있을 때만 제한적으로 사용하고, 주석과 테스트로 근거를 남긴다.

## Swift 컴파일러 버전과 언어 모드는 다르다

Swift 6 컴파일러를 사용한다고 모든 타깃이 자동으로 Swift 6 언어 모드가 되는 것은 아니다. 프로젝트는 타깃별로 Swift 언어 모드를 선택할 수 있다.

- **Swift 5 언어 모드**: 엄격한 동시성 검사를 단계적으로 경고로 확인할 수 있다.
- **Swift 6 언어 모드**: 완전한 데이터 경쟁 안전성 검사가 기본이며 위반이 오류가 된다.

따라서 큰 프로젝트는 한 번에 모든 코드를 바꾸기보다 타깃별로 옮길 수 있다.

## 현실적인 마이그레이션 순서

### 1. 경고를 먼저 켠다

Swift 5 언어 모드에서 Strict Concurrency Checking을 `Complete`로 설정해 잠재 문제를 확인한다. 명령줄에서는 상황에 따라 다음 옵션을 사용할 수 있다.

```text
-strict-concurrency=complete
```

### 2. 소유권과 격리를 정한다

경고를 무조건 억제하기 전에 “이 상태는 누가 소유해야 하는가?”를 먼저 결정한다.

| 문제 | 우선 고려할 해결책 |
| --- | --- |
| 전역으로 변경되는 UI 상태 | `@MainActor` |
| 여러 작업이 공유하는 캐시·세션 | `actor` |
| 작업 사이로 전달하는 데이터 | 불변 `Sendable` 값 타입 |
| 병렬 클로저가 지역 변수를 변경 | 결과를 반환해 부모가 집계 |
| 기존 콜백 API의 격리가 불명확 | API 경계에 격리 선언 또는 continuation 적용 |

### 3. 라이브러리 경계를 확인한다

아직 동시성 주석이 충분하지 않은 모듈은 `@preconcurrency import`가 마이그레이션에 도움을 줄 수 있다. 이것도 영구적인 해결보다는 외부 라이브러리가 적절한 Sendable·격리 정보를 제공할 때까지 쓰는 호환 장치에 가깝다.

### 4. 타깃 단위로 Swift 6 모드를 켠다

경고를 해결한 타깃부터 Swift 6 언어 모드로 전환하고 테스트한다. 컴파일 성공뿐 아니라 취소, actor 재진입, UI 갱신 순서 같은 런타임 동작도 함께 확인한다.

## Swift 6.2에서 달라진 선택지

Swift 6.2는 프로젝트가 원할 때 **기본 MainActor 격리**를 선택할 수 있게 했다. 이 설정을 켜면 명시적인 격리 선언이 없는 코드가 기본적으로 MainActor에 격리되고, 동시 실행기에서 실행해야 하는 async 함수는 `@concurrent`로 의도를 표시할 수 있다.

중요한 점은 다음과 같다.

- 기존 프로젝트의 동작이 컴파일러 업데이트만으로 자동 변경되지는 않는다.
- 기본 MainActor 격리는 프로젝트·타깃 설정으로 선택한다.
- 라이브러리와 서버 코드는 UI 앱과 다른 기본값이 더 적합할 수 있다.
- `@concurrent`는 CPU 작업을 어디서 실행할지 명시하는 도구이지, 모든 async 함수에 붙이는 장식이 아니다.

마이그레이션 문서는 사용하는 Xcode와 Swift 버전에 맞춰 확인해야 한다.

## 전체 흐름 다시 보기

Swift Concurrency의 도구들은 서로 다른 문제를 해결한다.

| 도구 | 해결하는 문제 |
| --- | --- |
| `async` / `await` | 중단될 수 있는 비동기 흐름 표현 |
| `Task`, `async let`, TaskGroup | 비동기 작업의 생명주기와 구조 |
| actor, `@MainActor` | 공유 가변 상태의 격리 |
| `Sendable`, `@Sendable` | 격리 영역 사이로 전달되는 값의 안전성 |
| Swift 6 검사 | 위 규칙을 컴파일 단계에서 강제 |

한 기능을 전부 actor로 바꾸거나 모든 함수에 `@MainActor`를 붙이는 것이 목표는 아니다. 값의 소유자, 실행 경계, 취소 범위를 코드에 정확히 표현하면 컴파일러가 그 설계를 검증해 준다.

## 정리

- `Sendable`은 격리 영역 사이로 안전하게 전달할 수 있는 값을 나타낸다.
- 변경 가능한 참조는 값 타입, actor, 전역 actor 또는 실제 동기화로 다시 설계한다.
- `@Sendable` 클로저가 캡처하는 값도 동시성에 안전해야 한다.
- `@unchecked Sendable`은 안전성을 개발자가 실제로 보장할 때만 사용한다.
- Swift 6 컴파일러와 Swift 6 언어 모드는 별개이며 타깃별로 단계적으로 전환할 수 있다.
- Swift 6.2의 기본 MainActor 격리는 선택 사항이고, 기존 프로젝트에 자동 적용되지 않는다.

## 참고

- [Swift 6 Migration Guide](https://www.swift.org/migration/documentation/migrationguide/)
- [Swift Evolution SE-0302: Sendable and @Sendable closures](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0302-concurrent-value-and-concurrent-closures.md)
- [Swift 6.2 Released](https://www.swift.org/blog/swift-6.2-released/)
- [Swift Evolution SE-0466: Control default actor isolation inference](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0466-control-default-actor-isolation.md)
