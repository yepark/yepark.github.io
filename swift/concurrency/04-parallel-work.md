---
title: "4. 여러 작업 한꺼번에: async let과 TaskGroup"
parent: Concurrency
grand_parent: Swift
nav_order: 4
permalink: /swift/concurrency/parallel-work/
first_written: 2026-11-16
last_modified_date: 2026-11-16
tags: [Swift, Concurrency, Async-Let, TaskGroup]
---

# 여러 작업 한꺼번에: async let과 TaskGroup
{: .no_toc }

{% include article-toc.md %}

`await`를 순서대로 쓰면 각 작업도 순서대로 실행된다. 서로 의존하지 않는 작업은 함께 시작해 전체 대기 시간을 줄일 수 있다. 작업 수가 코드에 고정돼 있으면 `async let`, 실행 중 결정되면 TaskGroup이 잘 맞는다.

## 순차 실행과 동시 실행

각 요청에 1초가 걸린다고 가정한다.

```swift
let profile = try await fetchProfile() // 약 1초
let notices = try await fetchNotices() // 약 1초
```

두 요청은 약 2초가 걸린다. `notices`가 `profile` 결과를 필요로 하지 않는다면 함께 시작할 수 있다.

```swift
async let profile = fetchProfile()
async let notices = fetchNotices()

let screen = try await ScreenData(
    profile: profile,
    notices: notices
)
```

두 `async let`은 선언할 때 자식 작업을 시작한다. 값을 사용하는 지점에서 `await`하고, `throws` 함수라면 `try`도 필요하다. 두 요청 시간이 겹치므로 전체는 긴 쪽에 가까워진다.

## async let은 작업 수를 알 때

```swift
func loadDashboard() async throws -> Dashboard {
    async let user = fetchUser()
    async let messages = fetchMessages()
    async let settings = fetchSettings()

    return try await Dashboard(
        user: user,
        messages: messages,
        settings: settings
    )
}
```

`async let` 변수는 현재 스코프를 벗어나기 전에 반드시 완료된다. 직접 기다리지 않고 스코프를 빠져나가면 Swift가 작업을 취소하고 완료를 기다린다. 부모-자식 수명이 코드 블록으로 보이는 구조화된 동시성이다.

모든 작업이 서로 독립적인지 먼저 확인한다. 사용자 ID가 있어야 메시지를 가져올 수 있다면 억지로 함께 실행할 수 없다.

## TaskGroup은 작업 수가 달라질 때

서버에서 받은 ID 수만큼 사용자를 조회한다면 그룹을 사용한다.

```swift
func fetchUsers(ids: [Int]) async throws -> [User] {
    try await withThrowingTaskGroup(
        of: (Int, User).self,
        returning: [User].self
    ) { group in
        for (index, id) in ids.enumerated() {
            group.addTask {
                (index, try await fetchUser(id: id))
            }
        }

        var indexedUsers: [(Int, User)] = []

        for try await item in group {
            indexedUsers.append(item)
        }

        return indexedUsers
            .sorted { $0.0 < $1.0 }
            .map(\.1)
    }
}
```

`group.addTask`로 자식 작업을 동적으로 추가한다. 그룹은 `AsyncSequence`처럼 결과를 **완료되는 순서대로** 전달한다. 입력 순서를 유지해야 하므로 예제는 인덱스를 함께 반환해 마지막에 정렬했다.

## 오류와 취소는 어떻게 전파될까

`withThrowingTaskGroup`의 자식이 오류를 던져도 그 오류는 그룹 결과를 꺼낼 때 관찰된다. `for try await`가 오류를 받으면 그룹 스코프를 빠져나가며 아직 끝나지 않은 자식은 취소된다. 그룹 함수는 모든 자식이 끝난 뒤에만 반환한다.

취소된 자식이 빨리 멈추려면 내부 작업도 취소 상태를 확인해야 한다.

```swift
group.addTask {
    try Task.checkCancellation()
    return try await fetchUser(id: id)
}
```

부모 Task가 취소되면 그룹의 자식도 취소 상태가 된다. 하지만 취소는 여전히 협력적이므로 CPU 반복 작업에는 직접 검사 지점을 넣는다.

## 결과를 모으는 여러 방법

합계를 계산한다면 배열을 만들지 않고 바로 누적할 수 있다.

```swift
let total = await withTaskGroup(of: Int.self, returning: Int.self) { group in
    for value in values {
        group.addTask { await score(value) }
    }

    var sum = 0
    for await score in group {
        sum += score
    }
    return sum
}
```

그룹 본문만 자식 추가와 결과 소비를 담당한다. `TaskGroup` 값을 함수 밖으로 저장하거나 탈출시키면 구조화된 수명 규칙이 깨지므로 허용되지 않는다.

## 너무 많은 Task를 한꺼번에 만들지 않기

ID가 수십 개면 모두 추가해도 괜찮을 수 있지만, 수만 개의 작업을 한 번에 생성하면 메모리와 서버 연결을 과하게 사용할 수 있다. 동시 실행 수를 제한하려면 처음에 일정 개수만 추가하고, 결과 하나를 받을 때 다음 작업 하나를 추가하는 방식으로 back pressure를 만든다.

```swift
func processLimited(
    _ values: [Int],
    limit: Int
) async -> [Output] {
    await withTaskGroup(of: Output.self, returning: [Output].self) { group in
        var iterator = values.makeIterator()
        var results: [Output] = []

        for _ in 0..<min(limit, values.count) {
            if let value = iterator.next() {
                group.addTask { await process(value) }
            }
        }

        while let result = await group.next() {
            results.append(result)
            if let value = iterator.next() {
                group.addTask { await process(value) }
            }
        }

        return results
    }
}
```

항상 `limit`개 이하만 실행된다. 실제 코드에서는 `limit > 0`인지 검증하고 결과 순서가 필요한지도 결정해야 한다.

## async let과 TaskGroup 선택 기준

| 상황 | 선택 |
| --- | --- |
| 작업 종류와 개수가 코드에 고정 | `async let` |
| 컬렉션 크기에 따라 작업 수가 달라짐 | TaskGroup |
| 각 작업의 반환형이 서로 다름 | `async let` |
| 같은 반환형을 완료 순서대로 처리 | TaskGroup |
| 동시 실행 개수를 직접 제한 | TaskGroup |

## 정리

- 순차 `await`는 작업을 하나씩 실행한다.
- 독립적이고 개수가 정해진 작업은 `async let`으로 함께 시작한다.
- 동적 개수의 동일한 작업은 TaskGroup으로 관리한다.
- 그룹 결과는 완료 순서로 나오므로 입력 순서가 필요하면 직접 보존한다.
- 작업이 아주 많으면 동시 실행 수를 제한한다.

## 다음 편

여러 Task가 같은 변경 가능한 값을 건드리면 데이터 경쟁이 생길 수 있다. 다음 편에서는 actor가 이 상태를 어떻게 격리하는지 살펴본다.

→ [5. actor: 여러 곳에서 같은 데이터를 건드릴 때]({{ '/swift/concurrency/actor/' | relative_url }})

## 참고

- [The Swift Programming Language: Tasks and Task Groups](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/#Tasks-and-Task-Groups)
- [Swift Evolution SE-0304: Structured Concurrency](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0304-structured-concurrency.md)
- [Swift Evolution SE-0317: async let](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0317-async-let.md)
- [Swift 6 Migration Guide: Limiting concurrency](https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/runtimebehavior/)
