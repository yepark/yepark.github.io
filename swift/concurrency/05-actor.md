---
title: "5. actor: 여러 곳에서 같은 데이터를 건드릴 때"
parent: Concurrency
grand_parent: Swift
nav_order: 5
permalink: /swift/concurrency/actor/
first_written: 2026-11-16
last_modified_date: 2026-11-17
tags: [Swift, Concurrency, Actor, Data-Race]
---

# actor: 여러 곳에서 같은 데이터를 건드릴 때
{: .no_toc }

{% include article-toc.md %}

## 읽고 더하고 저장하는 사이

잔액 100에서 두 작업이 동시에 10씩 인출한다고 하자. 둘 다 100을 읽고 각각 90을 쓰면 한 번의 인출이 사라진다. 값 읽기와 쓰기의 순서가 겹친 것이 문제다.

actor는 상태에 접근하는 경계를 만든다. 외부에서 접근할 때 `await`가 필요한 이유는 그 경계에서 실행을 기다릴 수 있기 때문이다. 다만 actor 메서드가 다른 작업을 `await`하는 동안에는 다른 요청이 들어올 수 있으므로, 재개한 뒤에도 예전 조건이 유효한지 확인해야 한다.

여러 Task가 같은 값을 동시에 읽고 수정하면 실행 순서에 따라 결과가 달라지는 **데이터 경쟁(data race)** 이 생길 수 있다. actor는 공유하는 가변 상태를 한 격리 영역에 넣어, 그 상태를 한 번에 하나의 작업만 다루도록 만드는 참조 타입이다.

## 일반 클래스에서 생기는 문제

아래 클래스의 `increment()`는 단순해 보이지만, 읽기와 쓰기가 하나의 원자적 동작은 아니다.

```swift
final class Counter {
    private var value = 0

    func increment() {
        value += 1
    }
}
```

두 스레드가 동시에 `value`를 읽으면 둘 다 같은 값을 기준으로 1을 더할 수 있다. 호출 횟수와 최종 값이 달라지는 이유다. 직접 lock을 정확하게 걸 수도 있지만, 상태가 커질수록 보호 범위를 빠뜨리기 쉽다.

## actor로 상태 격리하기

`class`를 `actor`로 바꾸면 저장 프로퍼티와 메서드가 actor에 격리된다.

```swift
actor Counter {
    private var value = 0

    func increment() {
        value += 1
    }

    func currentValue() -> Int {
        value
    }
}
```

actor 바깥에서 격리된 메서드를 부를 때는 `await`가 필요하다.

```swift
let counter = Counter()

await counter.increment()
let value = await counter.currentValue()
```

호출한 Task는 actor에 접근할 차례가 올 때까지 중단될 수 있다. actor 내부에서 자기 상태를 다루는 동기 메서드는 `await` 없이 접근한다.

> actor는 전용 스레드가 아니다. Swift 런타임이 actor의 격리된 상태에 대한 접근을 직렬화하는 모델이다.

## actor 안의 await는 경계다

actor는 한 시점에 격리된 코드 하나만 실행하지만, 메서드가 `await`에서 중단되면 다른 작업이 actor에 들어올 수 있다. 이를 **재진입(reentrancy)** 이라고 한다.

```swift
actor ImageCache {
    private var images: [URL: Data] = [:]

    func image(for url: URL) async throws -> Data {
        if let cached = images[url] {
            return cached
        }

        let (downloaded, _) = try await URLSession.shared.data(from: url)

        // 기다리는 동안 다른 Task가 같은 이미지를 저장했을 수 있다.
        if let cached = images[url] {
            return cached
        }

        images[url] = downloaded
        return downloaded
    }
}
```

첫 번째 캐시 확인과 다운로드 완료 사이에는 시간이 흐른다. 그동안 actor의 상태가 바뀔 수 있으므로, `await` 뒤에서 이전 가정이 여전히 맞는지 다시 확인해야 한다.

실무에서는 다음처럼 생각하면 안전하다.

1. `await` 전에 필요한 값을 지역 상수로 복사한다.
2. `await`를 격리 상태 변경의 중간에 두지 않는다.
3. `await` 뒤에는 공유 상태를 다시 읽고 조건을 검증한다.

## await 없는 작은 연산으로 묶기

계좌 이체처럼 여러 상태 변경이 하나의 규칙을 이뤄야 한다면, 검증과 변경을 actor의 동기 메서드 안에 묶는다.

```swift
actor BankAccount {
    enum AccountError: Error {
        case insufficientFunds
    }

    private var balance: Int

    init(balance: Int) {
        self.balance = balance
    }

    func withdraw(_ amount: Int) throws {
        guard balance >= amount else {
            throw AccountError.insufficientFunds
        }

        balance -= amount
    }
}
```

검증과 차감 사이에 `await`가 없으므로 다른 작업이 그 중간 상태를 볼 수 없다. 네트워크 요청처럼 반드시 기다려야 하는 일은 actor 밖에서 먼저 끝낸 뒤, 최종 변경만 actor 메서드에 맡기는 구조가 이해하기 쉽다.

## nonisolated로 격리 밖에 공개하기

actor의 가변 상태와 관계없는 값은 `nonisolated`로 표시할 수 있다.

```swift
actor DownloadManager {
    nonisolated let serviceName = "Image CDN"
    private var activeDownloads = 0

    func beginDownload() {
        activeDownloads += 1
    }
}

let manager = DownloadManager()
print(manager.serviceName) // await 불필요
```

`nonisolated` 코드는 actor의 격리된 가변 상태에 접근할 수 없다. 단순히 `await`를 없애기 위한 우회 수단이 아니라, actor 상태와 독립적이라는 사실을 표현할 때만 사용한다.

## actor가 잘 맞는 경우

- 여러 Task가 함께 사용하는 캐시, 세션, 연결 상태가 있다.
- 값의 읽기와 변경에 지켜야 할 규칙이 있다.
- 상태의 소유자를 한 곳으로 모으고 싶다.

반대로 단순 데이터 전달에는 `struct`, 화면 상태에는 `@MainActor`, 아예 변경되지 않는 데이터에는 불변 `Sendable` 값이 더 자연스러울 수 있다. 모든 클래스를 actor로 바꾸는 것이 목표는 아니다.

## 정리

- actor는 공유 가변 상태를 격리해 데이터 경쟁을 막는다.
- actor 밖에서 격리된 상태에 접근할 때는 보통 `await`가 필요하다.
- actor는 스레드가 아니라 격리와 실행 순서를 보장하는 언어 모델이다.
- actor 메서드도 `await`에서 재진입될 수 있으므로 이후의 상태를 다시 검증한다.
- 상태와 무관한 선언만 `nonisolated`로 격리 밖에 공개한다.

## 다음 편

다음 편에서는 UI 상태 전체를 전역 actor인 `MainActor`에 격리하고, 화면 갱신과 백그라운드 작업의 경계를 정리한다.

→ [6. @MainActor: UI 상태를 안전하게 관리하기]({{ '/swift/concurrency/main-actor/' | relative_url }})

## 참고

- [The Swift Programming Language: Actors](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/concurrency/#Actors)
- [Swift Evolution SE-0306: Actors](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0306-actors.md)
