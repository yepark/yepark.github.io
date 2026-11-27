---
title: "GCD와 DispatchQueue"
description: "Swift GCD의 sync와 async, Serial Queue와 Concurrent Queue 차이를 실행 순서와 데드락 예제로 자세히 설명합니다."
parent: Concurrency
grand_parent: Swift
nav_order: 0
permalink: /swift/concurrency/gcd-queue-basics/
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
date: 2026-11-16
first_written: 2026-11-16
last_modified_date: 2026-11-27
tags: [Swift, Concurrency, GCD, DispatchQueue]
---

# GCD와 DispatchQueue
{: .no_toc }

{% include article-toc.md %}

**GCD(Grand Central Dispatch)**는 실행할 작업을 큐에 넣으면 시스템이 스레드를 관리하며 실행해 주는 Apple의 동시성 라이브러리다. **DispatchQueue**는 GCD에서 작업을 받아 정해진 방식(한 번에 하나씩 또는 여러 개를 동시에)으로 실행하는 큐다. 개발자는 스레드를 직접 만들지 않고, 어떤 큐에 어떤 방식으로 작업을 보낼지만 정한다.

Swift 동시성을 공부할 때 가장 먼저 헷갈리는 조합이 있다.

- `sync`와 `async`
- `serial`과 `concurrent`

이름만 보면 `sync == serial`, `async == concurrent`처럼 느껴진다. 하지만 둘은 **서로 다른 질문에 답하는 개념**이다.

> `sync`와 `async`는 **작업을 보낸 호출자가 기다리는가**를 말한다.  
> `serial`과 `concurrent`는 **큐가 여러 작업을 어떤 방식으로 실행하는가**를 말한다.

이 두 문장만 정확히 이해하면 GCD의 큰 뼈대가 잡힌다.

## 예제를 실행하기 전에

`print`는 콘솔에 글자를 출력하는 함수다. 이 글에서는 출력 순서를 보고 어떤 작업이 먼저 끝났는지 관찰한다. `Thread.sleep`은 스레드를 실제로 붙잡는 학습용 지연이며, 앱의 비동기 대기를 구현하는 방법으로 복사하지 않는다.

명령행 프로그램은 비동기 작업이 끝나기 전에 종료될 수 있다. Playground는 실행을 유지하도록 설정하거나 앱의 버튼 동작에서 시험한다. 코드 조각마다 새 큐를 만들고 독립적으로 실행하면 앞 예제의 작업과 출력이 섞이는 일을 줄일 수 있다.

## 먼저 작업, 큐, 스레드를 구분하자

코드를 보기 전에 세 단어를 분리해 보자.

### 작업(Task)

실행하려는 코드 한 묶음이다. Swift에서는 보통 클로저로 표현한다.

```swift
{
    print("이미지 다운로드")
}
```

### 큐(Queue)

실행할 작업을 제출하는 곳이다. `DispatchQueue`는 받은 작업을 언제, 어떤 방식으로 시작할지 관리한다.

```swift
let queue = DispatchQueue(label: "com.yep.image")

queue.async {
    print("이미지 다운로드")
}
```

큐를 식당의 주문대로 생각하면 쉽다. 작업은 주문서이고, 큐는 주문서를 받아 주방에 전달하는 시스템이다.

### 스레드(Thread)

실제로 코드가 실행되는 흐름이다. 개발자는 GCD에 작업을 맡기고, GCD는 시스템 상황에 맞게 스레드를 관리한다. 메인 큐를 제외하면 특정 큐가 언제나 같은 스레드를 사용한다고 가정하면 안 된다.

{: .warning }
**큐와 스레드는 같은 것이 아니다.** Serial Queue의 작업도 매번 같은 스레드에서 실행된다고 보장되지 않는다. Serial이라는 말은 “한 번에 한 작업만 실행한다”는 뜻이다.

## sync와 async: 호출자가 기다리는가

`sync`와 `async`의 기준은 **작업 자체가 아니라 작업을 제출한 호출자**다.

### sync: 끝날 때까지 기다린다

```swift
let queue = DispatchQueue(label: "com.yep.serial")

print("A")

queue.sync {
    print("B")
}

print("C")
```

출력은 항상 다음과 같다.

```text
A
B
C
```

`queue.sync`를 호출한 실행 흐름은 클로저의 작업이 끝날 때까지 그 자리에서 기다린다. 따라서 `B`가 끝난 뒤에야 `C`로 갈 수 있다.

여기서 중요한 점은 `sync`가 “메인 스레드에서 실행한다”는 뜻도, “Serial Queue를 사용한다”는 뜻도 아니라는 것이다. 오직 **호출한 쪽이 완료를 기다린다**는 뜻이다.

### async: 맡기고 바로 돌아온다

```swift
let queue = DispatchQueue(label: "com.yep.serial")

print("A")

queue.async {
    print("B")
}

print("C")
```

가능한 출력 중 하나는 다음과 같다.

```text
A
C
B
```

호출자는 `B`가 끝날 때까지 기다리지 않는다. 작업을 큐에 맡기고 다음 줄인 `C`로 진행한다. 별도 큐의 `B`는 그 사이 시작될 수 있으므로 `B`와 `C`의 출력 순서는 보장되지 않는다. `A → B → C`도 가능한 결과다.

Serial Queue가 보장하는 것은 같은 큐에 제출한 작업 사이의 순서다. 호출자가 실행하는 `print("C")`까지 자동으로 그 큐에 들어가는 것은 아니다. 그래서 위 코드에서 ‘큐가 직렬이니 반드시 C가 먼저’라고 결론 내릴 수 없다.

{: .note }
`async`는 “지금 당장 동시에 실행한다”가 아니라 **호출자가 완료를 기다리지 않는다**는 뜻이다. 시스템 상황에 따라 작업이 실제로 시작되는 시점은 달라질 수 있다.

## Serial과 Concurrent: 큐가 작업을 처리하는 방식

이번에는 작업을 받는 큐의 관점이다.

### Serial Queue: 한 번에 하나씩

Serial Queue는 먼저 들어온 작업이 끝나야 다음 작업을 시작한다.

```text
시간 ─────────────────────────────▶

작업 1  [ 실행 중 ]
작업 2           [ 실행 중 ]
작업 3                    [ 실행 중 ]
```

별도 속성을 주지 않고 만든 `DispatchQueue`는 기본적으로 Serial Queue다.

```swift
let serialQueue = DispatchQueue(label: "com.yep.serial")
```

세 작업을 비동기로 넣어 보자.

```swift
let serialQueue = DispatchQueue(label: "com.yep.serial")

for number in 1...3 {
    serialQueue.async {
        print("작업 \(number) 시작")
        Thread.sleep(forTimeInterval: 1)
        print("작업 \(number) 끝")
    }
}
```

각 작업을 `async`로 제출했지만 큐는 Serial이므로 한 번에 하나만 처리한다.

```text
작업 1 시작
작업 1 끝
작업 2 시작
작업 2 끝
작업 3 시작
작업 3 끝
```

바로 이 예제가 **async와 concurrent는 같은 말이 아니다**라는 것을 보여 준다. 호출자는 기다리지 않지만, 큐 안의 작업은 하나씩 실행된다.

### Concurrent Queue: 앞 작업의 완료를 기다리지 않고 다음 작업 시작

Concurrent Queue는 앞 작업이 아직 실행 중이어도 다음 작업을 시작할 수 있다.

```text
시간 ─────────────────────────────▶

작업 1  [──────── 실행 중 ────────]
작업 2     [──── 실행 중 ────]
작업 3        [── 실행 중 ──]
```

직접 만들 때는 `.concurrent` 속성을 지정한다.

```swift
let concurrentQueue = DispatchQueue(
    label: "com.yep.concurrent",
    attributes: .concurrent
)
```

```swift
for number in 1...3 {
    concurrentQueue.async {
        print("작업 \(number) 시작")
        Thread.sleep(forTimeInterval: 1)
        print("작업 \(number) 끝")
    }
}
```

가능한 출력 중 하나는 다음과 같다.

```text
작업 1 시작
작업 2 시작
작업 3 시작
작업 2 끝
작업 1 끝
작업 3 끝
```

작업은 큐에 들어간 순서대로 **시작할 수 있도록 꺼내지만**, 완료 순서는 보장되지 않는다. 실제로 몇 개가 동시에 실행될지는 CPU 코어 수, 다른 프로세스의 부하, 작업 우선순위 같은 시스템 상태에 따라 달라진다.

{: .tip }
Concurrent Queue는 “반드시 동시에 실행”이 아니라 **동시에 실행할 수 있음**을 뜻한다.

## 두 축을 합치면 네 가지 조합이 된다

이제 두 기준을 합쳐 보자.

| 조합 | 호출자는 기다리는가? | 큐는 한 번에 몇 작업을 실행할 수 있는가? |
| --- | --- | --- |
| Serial + sync | 기다림 | 하나 |
| Serial + async | 기다리지 않음 | 하나 |
| Concurrent + sync | 기다림 | 여러 개 가능 |
| Concurrent + async | 기다리지 않음 | 여러 개 가능 |

표에서 가장 중요한 것은 **호출 방식과 큐의 종류가 독립적**이라는 점이다.

### 1. Serial Queue + sync

```swift
serialQueue.sync { print("1") }
serialQueue.sync { print("2") }
serialQueue.sync { print("3") }
```

호출자는 각 작업이 끝날 때까지 기다리고, 큐도 한 번에 하나만 실행한다. 출력은 `1 → 2 → 3`이다.

### 2. Serial Queue + async

```swift
serialQueue.async { runTask(1) }
serialQueue.async { runTask(2) }
serialQueue.async { runTask(3) }
```

호출자는 세 작업을 빠르게 맡기고 자기 일을 계속한다. 하지만 Serial Queue 안에서는 `1 → 2 → 3` 순서로 하나씩 처리한다. 파일 쓰기나 공유 상태 변경처럼 순서를 지켜야 하는 작업에 유용하다.

### 3. Concurrent Queue + sync

```swift
concurrentQueue.sync { runTask(1) }
concurrentQueue.sync { runTask(2) }
concurrentQueue.sync { runTask(3) }
```

큐 자체는 여러 작업을 실행할 수 있지만, 위 코드를 실행하는 **한 호출자**는 첫 작업이 끝나야 두 번째 `sync` 호출로 이동한다. 그래서 이 예제만 보면 결국 하나씩 실행된다.

Concurrent + sync의 동시성을 관찰하려면 서로 다른 실행 흐름에서 같은 Concurrent Queue로 작업을 보내는 상황이 필요하다. 즉, Concurrent Queue라는 능력이 있어도 호출자가 연속해서 `sync`로 막히면 그 능력을 활용하지 못할 수 있다.

### 4. Concurrent Queue + async

```swift
concurrentQueue.async { runTask(1) }
concurrentQueue.async { runTask(2) }
concurrentQueue.async { runTask(3) }
```

호출자는 기다리지 않고, 큐도 여러 작업을 겹쳐 실행할 수 있다. 서로 독립적인 이미지 처리나 계산 작업 여러 개를 맡기는 전형적인 형태다.

## Main Queue와 Global Queue

GCD가 기본으로 제공하는 대표적인 큐도 알아 두자.

### Main Queue

```swift
DispatchQueue.main.async {
    // UI 업데이트
}
```

Main Queue는 **메인 스레드에서 작업을 하나씩 실행하는 Serial Queue**다. UIKit과 AppKit의 UI 변경은 메인 실행 문맥에서 해야 한다.

오래 걸리는 네트워크 처리나 이미지 계산을 Main Queue에서 실행하면 그동안 화면 그리기와 터치 처리도 밀린다. 그래서 무거운 작업은 백그라운드에서 처리하고 UI 반영만 메인으로 돌아오는 패턴을 많이 사용했다.

```swift
DispatchQueue.global(qos: .userInitiated).async {
    let image = makeThumbnail() // 무거운 작업

    DispatchQueue.main.async {
        imageView.image = image // UI 반영
    }
}
```

### Global Queue

```swift
DispatchQueue.global(qos: .userInitiated)
```

Global Queue는 시스템이 제공하는 Concurrent Queue다. QoS(Quality of Service)로 작업의 중요도와 사용자 체감 긴급도를 전달할 수 있다.

| QoS | 적합한 예 |
| --- | --- |
| `.userInteractive` | 애니메이션처럼 즉시 끝나야 하는 작업 |
| `.userInitiated` | 사용자가 시작하고 결과를 기다리는 작업 |
| `.utility` | 다운로드, 긴 계산처럼 시간이 걸리는 작업 |
| `.background` | 사용자에게 바로 보이지 않는 유지보수 작업 |

QoS는 실행 순서를 확정하는 값이 아니라 시스템 스케줄러에 전달하는 **우선순위 힌트**다.

## 가장 위험한 실수: 같은 Serial Queue에 sync

메인 스레드에서 Main Queue에 `sync`로 작업을 보내면 데드락(교착 상태: 두 쪽이 서로 상대가 끝나기를 기다리느라 둘 다 영원히 멈춘 상태)이 발생한다.

```swift
// 메인 스레드에서 실행 중
DispatchQueue.main.sync {
    print("실행되지 못함")
}
```

왜 멈출까?

1. 메인 스레드는 `sync`로 보낸 작업이 끝나기를 기다린다.
2. Main Queue는 Serial Queue이고, 현재 메인 스레드가 실행 중인 작업이 끝나야 새 작업을 시작할 수 있다.
3. 현재 작업은 새 작업을 기다리고, 새 작업은 현재 작업이 끝나기를 기다린다.
4. 서로 영원히 기다리는 데드락이 된다.

이 문제는 Main Queue에만 한정되지 않는다. 어떤 Serial Queue 안에서 **바로 그 큐에 다시 `sync`**해도 같은 원리로 데드락이 발생한다.

```swift
let queue = DispatchQueue(label: "com.yep.serial")

queue.async {
    queue.sync { // 데드락
        print("실행되지 못함")
    }
}
```

{: .warning }
현재 실행 중인 Serial Queue와 같은 큐에 `sync`로 다시 들어가지 말자. 특히 메인 스레드에서 `DispatchQueue.main.sync`를 호출하면 안 된다.

## Serial Queue로 공유 상태 보호하기

여러 작업이 같은 값을 동시에 수정하면 데이터 경쟁이 생긴다.

```swift
var count = 0

DispatchQueue.concurrentPerform(iterations: 1_000) { _ in
    count += 1
}
```

`count += 1`은 읽기, 더하기, 쓰기가 합쳐진 연산이다. 여러 실행 흐름이 같은 값을 동시에 읽고 쓰면 일부 증가가 사라질 수 있으므로 결과가 항상 1,000이라고 보장할 수 없다.

Serial Queue를 상태의 유일한 접근 통로로 만들면 한 번에 한 작업만 값을 건드리게 할 수 있다.

```swift
final class Counter {
    private var value = 0
    private let queue = DispatchQueue(label: "com.yep.counter")

    func increment() {
        queue.async {
            self.value += 1
        }
    }

    func currentValue() -> Int {
        queue.sync {
            value
        }
    }
}
```

변경 작업은 `async`로 순서대로 맡기고, 값을 읽을 때는 `sync`로 결과를 받아 온다. 다만 `currentValue()`를 이미 같은 큐 안에서 호출하면 데드락이 될 수 있으므로 API 설계 단계에서 접근 경로를 명확히 해야 한다.

Swift Concurrency에서는 이런 공유 상태를 actor로 더 직접적으로 표현할 수 있다.

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

actor도 격리된 상태에 한 번에 하나의 Task만 접근하게 한다는 점에서 Serial Queue와 비슷한 목적을 갖지만, 컴파일러가 격리 규칙을 검사하고 `await`를 통해 접근 지점을 드러낸다는 차이가 있다.

## GCD의 async와 Swift의 async는 같은 말일까

이름은 같지만 문맥이 다르다.

```swift
DispatchQueue.global().async {
    // GCD: 클로저를 큐에 맡기고 호출자는 즉시 돌아감
}
```

```swift
func loadImage() async throws -> Image {
    // Swift Concurrency: 함수가 중단될 수 있음
}
```

- GCD의 `queue.async`는 **큐에 작업을 제출하는 방식**이다.
- Swift Concurrency의 `async`는 **함수가 중단되었다가 나중에 이어질 수 있음**을 타입에 표시한다.
- Swift의 `await`는 스레드를 붙잡고 기다리는 `queue.sync`와 다르다. Task가 중단되는 동안 실행 자원을 다른 작업에 양보할 수 있다.

따라서 Swift Concurrency를 배울 때 GCD의 용어를 그대로 대입하면 오히려 헷갈릴 수 있다. 공통점은 “기다림과 여러 작업을 다룬다”는 것이고, 실행 모델과 표현 방식은 다르다.

## 자주 하는 오해 정리

### “async면 동시에 실행된다”

아니다. `async`는 호출자가 기다리지 않는다는 뜻이다. Serial Queue에 제출하면 작업은 하나씩 실행된다.

### “Serial Queue는 메인 스레드다”

아니다. Main Queue가 대표적인 Serial Queue일 뿐이다. 직접 만든 Serial Queue의 작업은 시스템이 관리하는 다른 스레드에서 실행될 수 있다.

### “Concurrent Queue면 항상 병렬 실행된다”

아니다. 여러 작업을 겹쳐 실행할 수 있지만, 실제 병렬 실행 여부와 개수는 시스템이 결정한다.

### “FIFO니까 Concurrent Queue도 완료 순서가 같다”

아니다. FIFO는 작업을 꺼내 **시작하는 순서**에 관한 규칙이다. 실행 시간이 다르면 완료 순서는 바뀔 수 있다.

### “백그라운드 큐에서 UI를 바꿔도 된다”

아니다. UI 상태 변경은 메인 실행 문맥에서 해야 한다. GCD에서는 Main Queue, 현대 Swift Concurrency 코드에서는 주로 `@MainActor`를 사용한다.

## 한 문장씩 다시 정리하기

- `sync`: 작업이 끝날 때까지 **호출자가 기다린다**.
- `async`: 작업을 맡기고 **호출자는 기다리지 않는다**.
- Serial Queue: 큐 안의 작업을 **한 번에 하나씩** 실행한다.
- Concurrent Queue: 큐 안의 여러 작업을 **겹쳐 실행할 수 있다**.
- Main Queue: 메인 스레드에서 실행되는 **Serial Queue**다.
- Global Queue: 시스템이 제공하는 **Concurrent Queue**다.
- `async == concurrent`, `sync == serial`이 아니다.
- 같은 Serial Queue에 `sync`로 다시 진입하면 데드락이 발생할 수 있다.

## 주요 API

| API | 역할 |
| --- | --- |
| `DispatchQueue(label:attributes:)` | 직렬 큐 생성. `.concurrent`면 동시 큐 |
| `DispatchQueue.main` | 메인 스레드에서 실행하는 직렬 큐 |
| `DispatchQueue.global(qos:)` | 시스템 전역 동시 큐 |
| `queue.async { }` | 작업을 넣고 기다리지 않는다 |
| `queue.sync { }` | 작업이 끝날 때까지 호출자가 기다린다 |
| `queue.async(flags: .barrier)` | 동시 큐에서 앞뒤 작업과 겹치지 않게 실행 |
| `DispatchQueue.concurrentPerform(iterations:execute:)` | 반복을 병렬로 실행하고 모두 끝날 때까지 기다린다 |
| `DispatchGroup` | 여러 작업이 모두 끝났는지 추적 |
| `asyncAfter(deadline:)` | 지정 시간 뒤 실행 |

## 다음 편

이제 “기다리는 동안 앱을 멈추지 않는 것”과 “여러 작업을 함께 관리하는 것”이 서로 다른 문제라는 기반이 생겼다. 다음 편에서는 콜백과 GCD 중심 코드가 Swift의 `async`/`await`, Task, actor로 어떻게 바뀌었는지 살펴본다.

→ [Swift Concurrency 실행 모델]({{ '/swift/concurrency/why-concurrency/' | relative_url }})

## 참고

- [Apple Developer Documentation: DispatchQueue](https://developer.apple.com/documentation/dispatch/dispatchqueue/)
- [Apple Concurrency Programming Guide: Dispatch Queues](https://developer.apple.com/library/archive/documentation/General/Conceptual/ConcurrencyProgrammingGuide/OperationQueues/OperationQueues.html)

