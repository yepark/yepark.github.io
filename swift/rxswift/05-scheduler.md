---
title: "Scheduler"
description: "subscribe(on:)과 observe(on:)이 구독과 이벤트를 어느 큐에서 실행하는지 비교하고, TestScheduler의 가상 시간과 iOS 화면 업데이트를 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 5
permalink: /swift/rxswift/scheduler/
last_modified_at: 2026-11-26
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-26
tags: [Swift, RxSwift, Scheduler, Thread, MainScheduler]
---

# Scheduler
{: .no_toc }

{% include article-toc.md %}

검색 결과를 받은 뒤 JSON을 읽는 일과 테이블을 그리는 일은 서로 다른 큐에 맡길 수 있다. RxSwift에서 **스케줄러(Scheduler)**는 구독이나 이벤트 알림을 어느 실행 맥락에 보낼지 정한다. 같은 코드를 어디서 실행했는지 구독 클로저와 연산자마다 출력해 보자.

{: .note }
아래 예제는 RxSwift 6.9.1, Swift 6.0.3, macOS 15.6에서 실행했다. 명령줄 프로그램에 넣을 때 공통 코드와 이어지는 예제를 순서대로 붙인다. `wait`는 명령줄에서 메인 큐에 예약한 작업이 끝날 시간을 주는 실습용 함수다.

```swift
import Foundation
import RxSwift

let disposeBag = DisposeBag()
func here() -> String {
    let label = String(cString: __dispatch_queue_get_label(nil))
    return Thread.isMainThread ? "main" : label
}
func wait(_ s: Double) { RunLoop.main.run(until: Date().addingTimeInterval(s)) }

let io = SerialDispatchQueueScheduler(internalSerialQueueName: "io")
let work = SerialDispatchQueueScheduler(internalSerialQueueName: "work")

func source(_ name: String = "source") -> Observable<Int> {
    Observable.create { observer in
        print("  create 클로저:", here())
        observer.onNext(1)
        observer.onCompleted()
        return Disposables.create()
    }
}
```

## 구독이 시작되는 곳과 값이 도착하는 곳

`subscribe(on:)`은 위쪽 소스를 구독하고 해제하는 동작을 지정한 스케줄러에 맡긴다. `observe(on:)`은 자기 위치 이후로 전달하는 이벤트를 지정한 스케줄러에 보낸다.

`source()`는 구독 클로저 안에서 즉시 값을 내보낸다. 첫 번째 구독은 메인 스레드에서 시작한다. 두 번째는 구독을 `io` 큐에 맡기고 받은 값을 메인 스레드에 전달한다.

```swift
print("--- 1. 스케줄러를 안 쓰면: 구독한 스레드에서 그대로")
source()
    .map { v -> Int in print("  map:", here()); return v }
    .subscribe(onNext: { _ in print("  subscribe:", here()) })
    .disposed(by: disposeBag)

print("--- 2. subscribe(on:) + observe(on:)")
source()
    .map { v -> Int in print("  map(앞):", here()); return v }
    .subscribe(on: io)
    .observe(on: MainScheduler.instance)
    .map { v -> Int in print("  map(뒤):", here()); return v }
    .subscribe(onNext: { _ in print("  subscribe:", here()) })
    .disposed(by: disposeBag)
wait(0.2)
```

```text
--- 1. 스케줄러를 안 쓰면: 구독한 스레드에서 그대로
  create 클로저: main
  map: main
  subscribe: main
--- 2. subscribe(on:) + observe(on:)
  create 클로저: io
  map(앞): io
  map(뒤): main
  subscribe: main
```

두 번째 구독에서 `create`와 앞쪽 `map`은 `io`에서 실행됐다. `observe(on:)`을 통과한 뒤에는 `map`과 결과 수신이 메인 스레드에서 실행됐다.

{: .warning }
소스가 자체 큐에서 응답하는 경우에는 그 큐에서 이벤트가 출발한다. 예를 들어 네트워크 응답 콜백의 큐는 네트워크 API가 정한다. 파싱을 특정 큐에 맡기려면 `map` 앞에 `observe(on:)`을 둔다. `source()` 호출 자체에 부수 효과가 있으면 Observable을 만들 때 그 효과가 실행된다. 구독마다 실행하려면 `Observable.deferred` 또는 `create` 클로저 안에 둔다.

## 스케줄러를 여러 번 지정하면

소스에 가까운 `subscribe(on: io)`가 원본 구독을 다시 `io`에 예약한다. `observe(on:)`은 여러 번 붙여 값의 전달 위치를 단계마다 바꿀 수 있다.

```swift
print("--- 3. subscribe(on:)을 두 번 쓰면")
source()
    .subscribe(on: io)
    .subscribe(on: work)
    .subscribe(onNext: { _ in print("  subscribe:", here()) })
    .disposed(by: disposeBag)
wait(0.2)

print("--- 4. observe(on:)을 여러 번 쓰면")
source()
    .observe(on: io)
    .map { v -> Int in print("  map1:", here()); return v }
    .observe(on: work)
    .map { v -> Int in print("  map2:", here()); return v }
    .observe(on: MainScheduler.instance)
    .subscribe(onNext: { _ in print("  subscribe:", here()) })
    .disposed(by: disposeBag)
wait(0.2)
```

```text
--- 3. subscribe(on:)을 두 번 쓰면
  create 클로저: io
  subscribe: io
--- 4. observe(on:)을 여러 번 쓰면
  create 클로저: main
  map1: io
  map2: work
  subscribe: main
```

두 번째 예제에서 소스는 `main`에서 구독됐고, 이벤트는 `io`, `work`, `main` 순서로 이동했다. 큐를 옮기는 지점이 실제 이벤트 경계다.

## MainScheduler.instance와 asyncInstance

메인 큐에서 `MainScheduler.instance`에 작업을 맡기면 현재 호출 안에서 바로 실행될 수 있다. `asyncInstance`는 메인 큐에 비동기로 예약한다. 구독 호출 다음 줄과 수신 출력의 순서를 확인한다.

```swift
print("--- 5. 메인에서 MainScheduler.instance vs asyncInstance")
print("  지금:", here())
Observable.just("instance")
    .observe(on: MainScheduler.instance)
    .subscribe(onNext: { print("  받음:", $0) })
    .disposed(by: disposeBag)
Observable.just("asyncInstance")
    .observe(on: MainScheduler.asyncInstance)
    .subscribe(onNext: { print("  받음:", $0) })
    .disposed(by: disposeBag)
print("  subscribe 호출 다음 줄")
wait(0.2)

print("--- 6. 백그라운드에서 MainScheduler.instance로 보내기")
Observable.just("from io")
    .subscribe(on: io)
    .observe(on: MainScheduler.instance)
    .subscribe(onNext: { print("  받음:", $0, here()) })
    .disposed(by: disposeBag)
print("  subscribe 호출 다음 줄")
wait(0.2)
```

```text
--- 5. 메인에서 MainScheduler.instance vs asyncInstance
  지금: main
  받음: instance
  subscribe 호출 다음 줄
  받음: asyncInstance
--- 6. 백그라운드에서 MainScheduler.instance로 보내기
  subscribe 호출 다음 줄
  받음: from io main
```

이미 처리 중인 상태를 구독 콜백에서 곧바로 다시 변경하면, 바깥 함수가 끝나기 전에 같은 로직이 한 번 더 들어올 수 있다. 다음 호출로 넘겨야 할 때 `asyncInstance`를 쓴다.

## 시간 연산자의 스케줄러

`interval`은 전달한 스케줄러에서 매 주기 값을 낸다. `take(2)`로 두 값만 받으면 구독이 끝난다.

```swift
print("--- 7. interval 같은 시간 연산자도 스케줄러에서 돈다")
Observable<Int>.interval(.milliseconds(50), scheduler: io)
    .take(2)
    .subscribe(onNext: { print("  tick", $0, here()) }, onCompleted: { print("  completed") })
    .disposed(by: disposeBag)
wait(0.3)
```

```text
--- 7. interval 같은 시간 연산자도 스케줄러에서 돈다
  tick 0 io
  tick 1 io
  completed
```

| 스케줄러 | 실행 맥락 | 쓰는 곳 |
| --- | --- | --- |
| `MainScheduler.instance` | 메인 큐 | 화면에 전달 |
| `MainScheduler.asyncInstance` | 메인 큐에 비동기 예약 | 현재 호출 이후에 화면에 전달 |
| `SerialDispatchQueueScheduler` | 지정한 직렬 큐 | 순서대로 실행할 파싱이나 상태 처리 |
| `ConcurrentDispatchQueueScheduler` | 지정한 동시 큐 | 여러 독립 구독이 하는 작업 |
| `OperationQueueScheduler` | `OperationQueue` | 작업 큐의 실행 조건을 관리할 때 |
| `TestScheduler` | 가상 시간 | 시간 연산자와 이벤트 순서 검증 |

## TestScheduler에서 1틱의 크기

`TestScheduler`는 실제로 기다리지 않고 정수 시각을 앞으로 움직인다. 기본 `resolution`은 1초다. 50ms를 1초 단위 가상 시각으로 바꾸면 50틱이 되지 않는다. 밀리초 단위로 테스트할 때는 `resolution: 0.001`을 지정한다.

다음 코드를 XCTest 테스트 타깃에 넣는다. `describe`는 기록을 `시각:값`으로 표시하며 `|`는 완료를 뜻한다.

```swift
import XCTest
import RxSwift
import RxTest

func describe<T>(_ events: [Recorded<Event<T>>]) -> String {
    events.map { r -> String in
        switch r.value {
        case .next(let v): return "\(r.time):\(v)"
        case .error: return "\(r.time):error"
        case .completed: return "\(r.time):|"
        }
    }.joined(separator: "  ")
}

final class P5Tests: XCTestCase {
    func delayed(_ scheduler: TestScheduler, _ due: RxTimeInterval) -> [Recorded<Event<Int>>] {
        let observer = scheduler.createObserver(Int.self)
        let bag = DisposeBag()
        scheduler.createHotObservable([.next(100, 1), .next(200, 2), .completed(300)])
            .delay(due, scheduler: scheduler)
            .subscribe(observer)
            .disposed(by: bag)
        scheduler.start()
        return observer.events
    }

    func testDelayResolution() {
        print("기본(1틱=1초), .milliseconds(50):", describe(delayed(TestScheduler(initialClock: 0), .milliseconds(50))))
        print("기본(1틱=1초), .seconds(50):     ", describe(delayed(TestScheduler(initialClock: 0), .seconds(50))))
        print("resolution 0.001, .milliseconds(50):",
              describe(delayed(TestScheduler(initialClock: 0, resolution: 0.001), .milliseconds(50))))

        XCTAssertEqual(delayed(TestScheduler(initialClock: 0), .seconds(50)), [
            .next(150, 1),
            .next(250, 2),
            .completed(350)
        ])
    }
}
```

```text
기본(1틱=1초), .milliseconds(50): 101:1  201:2  301:|
기본(1틱=1초), .seconds(50):      150:1  250:2  350:|
resolution 0.001, .milliseconds(50): 150:1  250:2  350:|
```

첫 줄에서 100틱의 이벤트가 101틱에 도착했다. 기본 해상도에서 50ms를 0틱으로 변환한 뒤, `TestScheduler`의 기본 `simulateProcessingDelay`가 현재 시각에 예약된 작업을 1틱 뒤로 옮겼다. 마지막 줄에서는 50ms를 50틱으로 바꾸어 150틱에 전달했다.

## 실습: 이미지 비동기 로드

URLSession에서 받은 바이트를 디코딩 큐에서 이미지로 변환하고 메인 큐에서 화면에 넣는다. 구독이 끝나면 작업을 취소할 수 있도록 URLSession 작업을 Disposable에 연결한다.

```swift
// 실행하지 않음 (UIKit 화면 바인딩)
func loadBytes(_ url: URL) -> Observable<Data> {
    Observable.create { observer in
        let task = URLSession.shared.dataTask(with: url) { data, _, error in
            if let error {
                observer.onError(error)
            } else if let data {
                observer.onNext(data)
                observer.onCompleted()
            } else {
                observer.onError(URLError(.badServerResponse))
            }
        }
        task.resume()
        return Disposables.create { task.cancel() }
    }
}

let decodeQueue = SerialDispatchQueueScheduler(qos: .userInitiated)
loadBytes(imageURL)
    .observe(on: decodeQueue)
    .map { UIImage(data: $0) }
    .observe(on: MainScheduler.instance)
    .subscribe(
        onNext: { [weak self] in self?.imageView.image = $0 },
        onError: { print("이미지 로드 실패:", $0) }
    )
    .disposed(by: disposeBag)
```

## 정리

`subscribe(on:)`은 구독과 해제를, `observe(on:)`은 이벤트 전달을 옮긴다. 소스가 자체 큐에서 이벤트를 내보내면 이벤트가 나오는 위치부터 확인한다. 테스트에서는 실제 시간 대신 `TestScheduler`를 쓰고, `resolution`을 연산자 단위와 맞춘다.

다음에는 [Error Handling]({{ "/swift/rxswift/error-handling/" | relative_url }})에서 실패한 요청을 복구하거나 재시도한다.

## 참고

- [RxSwift 스케줄러 문서](https://github.com/ReactiveX/RxSwift/blob/6.9.1/Documentation/Schedulers.md)
- [RxSwift MainScheduler 구현](https://github.com/ReactiveX/RxSwift/blob/6.9.1/RxSwift/Schedulers/MainScheduler.swift)
- [RxTest TestScheduler 구현](https://github.com/ReactiveX/RxSwift/blob/6.9.1/RxTest/Schedulers/TestScheduler.swift)
- [RxSwift 테스트 문서](https://github.com/ReactiveX/RxSwift/blob/6.9.1/Documentation/UnitTests.md)
