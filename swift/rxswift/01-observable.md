---
title: "Observable과 Subscribe"
description: "RxSwift의 핵심인 Observable 생성과 구독, next·error·completed 이벤트 흐름, Dispose와 DisposeBag, [weak self]로 메모리 누수를 막는 방법을 실행 결과와 함께 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 1
permalink: /swift/rxswift/observable/
last_modified_at: 2026-11-27
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-27
tags: [Swift, RxSwift, Observable, Reactive]
---

# Observable과 Subscribe
{: .no_toc }

{% include article-toc.md %}

RxSwift는 비동기 이벤트를 **값의 흐름(stream)**으로 다룬다. 버튼 탭, 네트워크 응답, 타이머, 텍스트 변경을 모두 같은 방식으로 처리할 수 있다. 이 흐름을 표현하는 핵심 타입이 `Observable`이다.

{: .note }
이 연재의 코드는 **RxSwift 6.9.1**, Swift 6.0.3(Xcode 16.2), macOS 15.6에서 SwiftPM 실행 파일로 직접 실행했다. 코드 아래의 출력은 실제로 나온 결과다. UIKit 화면 코드처럼 Mac 명령줄에서 돌릴 수 없는 코드는 "실행하지 않음"이라고 따로 적었다.

UIKit 예제를 제외한 명령줄 코드에서는 먼저 공통 import와 DisposeBag을 둔다. 같은 이름을 다시 쓰는 예제는 따로 실행한다.

```swift
import Foundation
import RxSwift

let disposeBag = DisposeBag()
```

## Observable이란

`Observable<T>`는 T 타입의 이벤트를 시간 순서대로 내보내는 시퀀스다. 세 종류의 이벤트를 방출한다.

```text
next(value)    — 값을 하나 전달한다
error(Error)   — 오류가 발생하고 시퀀스가 종료된다
completed      — 정상적으로 시퀀스가 끝난다
```

타임라인으로 그리면 이렇다. 이런 그림을 **마블 다이어그램**이라고 부른다. 왼쪽에서 오른쪽으로 시간이 흐르고, `|`는 completed, `X`는 error다.

```text
--1--2--3--|        정상 종료 (next × 3, completed)
--1--2--X          오류 종료 (next × 2, error)
--1--2--3--4--...  무한 시퀀스 (completed 없음)
```

{: .tip }
Observable은 "물이 흐르는 수도관"이고, 구독자는 "수도꼭지 끝에 댄 컵"이다. 물(next)은 여러 번 나올 수 있지만, 수도관이 터지거나(error) 잠기면(completed) 그 뒤로는 물이 한 방울도 나오지 않는다.

### 규칙: 끝난 뒤의 이벤트는 버려진다

RxSwift 공식 문서는 이 규칙을 `next* (error | completed)?`로 적는다. next가 0번 이상 오고, 그 뒤에 error나 completed가 **최대 한 번** 온다는 뜻이다.

정말 그런지 끝난 뒤에 이벤트를 억지로 더 보내 보자.

```swift
Observable<Int>.create { observer in
    observer.onNext(1)
    observer.onCompleted()
    observer.onNext(2)          // 이미 끝났으므로 전달되지 않는다
    observer.onError(URLError(.badURL))
    return Disposables.create { print("정리(cleanup) 실행") }
}
.subscribe(
    onNext: { print("next:", $0) },
    onError: { print("error:", $0) },
    onCompleted: { print("completed") }
)
.disposed(by: disposeBag)
```

```text
next: 1
completed
정리(cleanup) 실행
```

`onCompleted()` 뒤에 보낸 `2`와 error는 구독자에게 닿지 않았다. 그리고 시퀀스가 끝나자 `Disposables.create { }` 안의 정리 코드가 실행됐다.

## Observable 생성

```swift
import RxSwift

// 1. just: 값 하나를 내보내고 completed
let single = Observable.just("Hello")

// 2. of: 여러 값을 순서대로
let sequence = Observable.of(1, 2, 3)

// 3. from: 배열의 각 요소를
let fromArray = Observable.from([10, 20, 30])

// 4. create: 직접 이벤트 제어
let custom = Observable<Int>.create { observer in
    observer.onNext(1)
    observer.onNext(2)
    observer.onCompleted()
    return Disposables.create()
}

// 5. error: 즉시 오류 종료
let failed = Observable<Int>.error(URLError(.badURL))

// 6. never: 아무 이벤트도 보내지 않는 무한 시퀀스
let silent = Observable<Void>.never()
```

각각을 구독해서 받은 이벤트를 한 줄로 찍어 봤다. 값은 그대로, completed는 `|`로 적었다.

```swift
func show<T>(_ name: String, _ o: Observable<T>) {
    var events: [String] = []
    o.subscribe { event in
        switch event {
        case .next(let v): events.append("\(v)")
        case .error: events.append("error")
        case .completed: events.append("|")
        }
    }
    .disposed(by: disposeBag)
    print(name.padding(toLength: 8, withPad: " ", startingAt: 0), events.joined(separator: " "))
}
show("just", Observable.just("Hello"))
show("of", Observable.of(1, 2, 3))
show("from", Observable.from([10, 20, 30]))
show("empty", Observable<Int>.empty())
show("error", Observable<Int>.error(URLError(.badURL)))
show("never", Observable<Int>.never())
show("range", Observable.range(start: 1, count: 3))
```

```text
just     Hello |
of       1 2 3 |
from     10 20 30 |
empty    |
error    error
never
range    1 2 3 |
```

- `empty`는 값 없이 바로 completed만 보낸다.
- `never`는 아무것도 보내지 않는다. 끝나지도 않는다.
- `range(start: 1, count: 3)`은 1부터 3개의 정수를 보낸다.

## Subscribe

구독이 있어야 Observable이 실행된다.

```swift
let disposeBag = DisposeBag()

Observable.of("A", "B", "C")
    .subscribe(
        onNext: { value in print("next:", value) },
        onError: { error in print("error:", error) },
        onCompleted: { print("completed") },
        onDisposed: { print("disposed") }
    )
    .disposed(by: disposeBag)
```

```text
next: A
next: B
next: C
completed
disposed
```

`onDisposed`는 구독이 정리될 때 한 번 불린다. completed나 error로 끝났을 때도, 직접 `dispose()`를 불렀을 때도 불린다.

`onError`, `onCompleted`, `onDisposed`는 생략할 수 있다. 필요한 이벤트만 처리해도 된다.

```swift
Observable.of(1, 2, 3)
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
```

{: .warning }
`onError`를 생략했는데 error가 오면 어떻게 될까? 직접 실행해 보니 `Unhandled error happened: server`라는 줄이 출력되고 프로그램은 계속 돌았다. 공식 문서에 따르면 이것은 `Hooks.defaultErrorHandler`의 기본 동작으로, DEBUG 빌드에서는 에러를 출력하고 RELEASE 빌드에서는 아무것도 하지 않는다. 릴리스 앱에서는 에러가 조용히 사라진다는 뜻이다. 에러가 올 수 있는 흐름이면 반드시 처리한다. 방법은 [Error Handling]({{ "/swift/rxswift/error-handling/" | relative_url }})에서 다룬다.

## 구독할 때마다 처음부터 실행된다

`create`로 만든 Observable은 **구독할 때마다** 클로저를 새로 실행한다. 만들기만 하고 구독하지 않으면 아무 일도 일어나지 않는다.

```swift
let numbers = Observable<Int>.create { observer in
    print("  create 클로저 실행")
    observer.onNext(7)
    observer.onCompleted()
    return Disposables.create()
}
print("Observable을 만들었다")
numbers.subscribe(onNext: { print("구독1:", $0) }).disposed(by: disposeBag)
numbers.subscribe(onNext: { print("구독2:", $0) }).disposed(by: disposeBag)
```

```text
Observable을 만들었다
  create 클로저 실행
구독1: 7
  create 클로저 실행
구독2: 7
```

"만들었다"가 먼저 찍히고, 클로저는 구독할 때마다 한 번씩 총 두 번 실행됐다. 이렇게 구독해야 비로소 일을 시작하는 Observable을 **cold Observable**이라고 부른다.

{: .question }
`create` 안에서 네트워크 요청을 보낸다면, 같은 Observable을 화면 두 곳에서 구독할 때 요청은 몇 번 갈까? 답은 두 번이다. 이것을 한 번으로 줄이는 `share`는 [Subject]({{ "/swift/rxswift/subject/" | relative_url }}) 편에서 실행해 본다.

## 이벤트를 enum으로 받기

`subscribe(onNext:onError:...)` 대신, 클로저 하나로 `Event` 열거형 자체를 받을 수도 있다.

```swift
Observable.of(1, 2)
    .subscribe { event in
        switch event {
        case .next(let value): print("next:", value)
        case .error(let error): print("error:", error)
        case .completed:        print("completed")
        }
    }
    .disposed(by: disposeBag)
```

```text
next: 1
next: 2
completed
```

{: .warning }
이 형태의 실제 이름은 `subscribe(_ on:)`이라서 `subscribe { event in }`처럼 쓴다. RxSwift 6에는 스레드를 정하는 `subscribe(on:)`이라는 전혀 다른 연산자가 있다. 이름이 비슷해서 헷갈리기 쉽다. `subscribe(on:)`은 [Scheduler]({{ "/swift/rxswift/scheduler/" | relative_url }}) 편에서 다룬다.

## debug()로 생명주기 들여다보기

흐름이 언제 구독되고, 무슨 이벤트가 오고, 언제 정리되는지 궁금하면 `debug()`를 끼워 넣는다.

```swift
Observable.of(1, 2)
    .debug("nums", trimOutput: false)
    .subscribe()
    .disposed(by: disposeBag)
```

```text
2026-11-27 00:02:48.119: nums -> subscribed
2026-11-27 00:02:48.124: nums -> Event next(1)
2026-11-27 00:02:48.124: nums -> Event next(2)
2026-11-27 00:02:48.124: nums -> Event completed
2026-11-27 00:02:48.124: nums -> isDisposed
```

구독(subscribed) → 값 두 개 → completed → 정리(isDisposed) 순서가 그대로 보인다. "왜 값이 안 오지?" 싶을 때 가장 먼저 꺼내 보는 도구다.

## Dispose와 메모리 관리

구독은 리소스를 소모한다. 타이머, 네트워크 요청, UI 바인딩이 구독으로 살아 있으면 화면을 떠난 뒤에도 계속 실행된다.

`subscribe`는 `Disposable`을 돌려준다. 이것을 직접 `dispose()`하거나 `DisposeBag`에 담으면 구독이 끝난다.

### dispose()로 직접 끊기

100ms마다 숫자를 보내는 타이머를 0.33초 뒤에 끊어 봤다.

```swift
let timerQueue = SerialDispatchQueueScheduler(qos: .default)
let start = Date()
func ms() -> Int {
    Int((Date().timeIntervalSince(start) * 10).rounded()) * 100
}

let subscription = Observable<Int>.interval(.milliseconds(100), scheduler: timerQueue)
    .subscribe(
        onNext: { print("\(ms())ms tick:", $0) },
        onDisposed: { print("\(ms())ms disposed") }
    )
Thread.sleep(forTimeInterval: 0.33)
subscription.dispose()
Thread.sleep(forTimeInterval: 0.3)
print("dispose 뒤에는 tick이 더 오지 않는다")
```

```text
100ms tick: 0
200ms tick: 1
300ms tick: 2
300ms disposed
dispose 뒤에는 tick이 더 오지 않는다
```

(`ms()`는 시작부터 지난 시간을 100ms 단위로 반올림해서 돌려주는 작은 함수다.)

`interval`은 끝나지 않는 Observable이다. `dispose()`를 부르지 않았다면 프로그램이 끝날 때까지 tick이 계속 왔을 것이다.

### DisposeBag

구독마다 `dispose()`를 부르는 것은 번거롭다. `DisposeBag`은 Disposable을 모아 두는 가방이다. **가방이 메모리에서 사라질 때** 안에 든 구독을 모두 dispose한다.

```swift
var bag = DisposeBag()
Observable<Int>.interval(.milliseconds(100), scheduler: timerQueue)
    .subscribe(onNext: { print("tick:", $0) }, onDisposed: { print("disposed") })
    .disposed(by: bag)
Thread.sleep(forTimeInterval: 0.25)
bag = DisposeBag()   // 이전 bag이 해제되면서 안의 구독도 dispose
Thread.sleep(forTimeInterval: 0.3)
```

```text
tick: 0
tick: 1
disposed
```

새 가방을 대입하는 순간 이전 가방이 해제되고, 타이머 구독도 끊겼다. 화면을 다시 그릴 때 이전 바인딩을 한꺼번에 끊고 싶으면 이 방법을 쓴다.

`DisposeBag`은 뷰컨트롤러나 뷰모델의 프로퍼티로 둔다. 그 객체가 해제될 때 가방도 해제되고, 담긴 구독도 함께 정리된다.

```swift
// 실행하지 않음 (UIKit 코드)
class ViewController: UIViewController {
    let disposeBag = DisposeBag()

    override func viewDidLoad() {
        super.viewDidLoad()
        Observable<Int>.interval(.seconds(1), scheduler: MainScheduler.instance)
            .subscribe(onNext: { print($0) })
            .disposed(by: disposeBag)  // VC가 deinit되면 타이머 구독도 해제
    }
}
```

{: .warning }
`disposed(by:)` 없이 구독만 하면 completed나 error가 올 때까지 구독이 유지된다. 무한 시퀀스(타이머, 버튼 탭 등)는 반드시 Dispose 처리를 해야 메모리 누수를 막을 수 있다.

### [weak self]: 가방이 영원히 안 버려지는 경우

DisposeBag은 "객체가 해제될 때" 구독을 끊는다. 그런데 구독 클로저가 `self`를 강하게 붙잡으면 객체가 **영원히 해제되지 않는다.** 그러면 가방도 안 버려지고 구독도 안 끊긴다.

두 클래스를 비교해 봤다. 차이는 `[weak self]` 한 줄뿐이다.

```swift
final class LeakyScreen {
    let disposeBag = DisposeBag()
    let tap = PublishSubject<Void>()
    var count = 0
    init() {
        tap.subscribe(onNext: { _ in
            self.count += 1            // self를 강하게 잡는다
        })
        .disposed(by: disposeBag)
    }
    deinit { print("LeakyScreen deinit") }
}

final class SafeScreen {
    let disposeBag = DisposeBag()
    let tap = PublishSubject<Void>()
    var count = 0
    init() {
        tap.subscribe(onNext: { [weak self] _ in
            self?.count += 1           // self를 약하게 잡는다
        })
        .disposed(by: disposeBag)
    }
    deinit { print("SafeScreen deinit") }
}

var leaky: LeakyScreen? = LeakyScreen()
leaky?.tap.onNext(())
leaky = nil
print("leaky = nil 했다")

var safe: SafeScreen? = SafeScreen()
safe?.tap.onNext(())
safe = nil
print("safe = nil 했다")
```

```text
leaky = nil 했다
SafeScreen deinit
safe = nil 했다
```

`LeakyScreen deinit`은 끝내 출력되지 않았다. 참조가 이렇게 동그랗게 이어져 있기 때문이다.

```text
LeakyScreen ──▶ disposeBag ──▶ 구독 ──▶ 클로저 ──▶ self(LeakyScreen)
     ▲                                                   │
     └───────────────────────────────────────────────────┘
```

`[weak self]`는 클로저가 self를 "약하게" 잡게 해서 이 고리를 끊는다. self가 사라지면 클로저 안의 `self`는 `nil`이 된다.

{: .tip }
구독 클로저 안에서 `self`를 쓰면 일단 `[weak self]`를 붙인다고 생각하면 된다. RxSwift 6에는 `subscribe(with: self, onNext: { owner, value in ... })`처럼 객체를 약하게 넘겨 주는 형태도 있다.

## 실습: 커스텀 Observable로 네트워크 요청 흉내내기

0.5초 뒤에 응답하는 가짜 요청을 만든다. 정리 코드에서 아직 안 끝난 작업을 취소하는 것이 핵심이다.

```swift
enum FetchError: Error { case notFound }

func fetchUser(id: Int) -> Observable<String> {
    return Observable.create { observer in
        print("  요청 시작 id=\(id)")
        let work = DispatchWorkItem {
            if id == 1 {
                observer.onNext("yep")
                observer.onCompleted()
            } else {
                observer.onError(FetchError.notFound)
            }
        }
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.5, execute: work)
        return Disposables.create {
            work.cancel()               // 아직 안 끝났으면 취소
            print("  정리 id=\(id)")
        }
    }
}

fetchUser(id: 1)
    .subscribe(
        onNext:      { print("user:", $0) },
        onError:     { print("error:", $0) },
        onCompleted: { print("done") }
    )
    .disposed(by: disposeBag)
Thread.sleep(forTimeInterval: 0.8)
fetchUser(id: 2)
    .subscribe(
        onNext:      { print("user:", $0) },
        onError:     { print("error:", $0) },
        onCompleted: { print("done") }
    )
    .disposed(by: disposeBag)
Thread.sleep(forTimeInterval: 0.8)
```

```text
  요청 시작 id=1
user: yep
done
  정리 id=1
  요청 시작 id=2
error: notFound
  정리 id=2
```

성공해도, 실패해도 마지막에 정리 코드가 불렸다.

이번에는 응답이 오기 전에(0.1초 뒤) 구독을 끊어 봤다.

```swift
let pending = fetchUser(id: 1)
    .subscribe(onNext: { print("user:", $0) }, onCompleted: { print("done") })
Thread.sleep(forTimeInterval: 0.1)
pending.dispose()
Thread.sleep(forTimeInterval: 0.8)
print("응답이 오지 않았다")
```

```text
  요청 시작 id=1
  정리 id=1
응답이 오지 않았다
```

dispose하자마자 정리 코드가 실행되어 작업이 취소됐다. 실제 앱에서는 여기에 `URLSessionDataTask.cancel()`을 둔다. 사용자가 화면을 닫으면(DisposeBag 해제) 진행 중이던 요청도 함께 취소된다.

## 자주 하는 실수

| 실수 | 결과 | 고치는 법 |
| --- | --- | --- |
| `subscribe`만 하고 `disposed(by:)`를 안 붙임 | 끝나지 않는 흐름이 계속 살아 있다 | DisposeBag에 담거나 필요한 시점에 해제한다 |
| 클로저에서 `self`를 강하게 캡처 | 객체·DisposeBag이 해제되지 않는다 | `[weak self]` 또는 `subscribe(with:)` |
| `create`에서 `Disposables.create()`를 비워 둠 | 구독을 끊어도 작업은 계속 돈다 | 정리 클로저에서 작업을 취소한다 |
| `onError` 생략 | 기본 오류 핸들러에 전달된다 | 에러를 처리하거나 흐름 안에서 바꾼다 |

## 주요 API

| API | 역할 |
| --- | --- |
| `Observable.just(x)` | 값 하나를 보내고 완료 |
| `Observable.of(a, b, ...)`, `Observable.from([...])` | 여러 값을 차례로 보내고 완료 |
| `Observable.range(start:count:)` | 연속 정수 |
| `Observable.create { observer in }` | 직접 이벤트를 만든다. `Disposable`을 돌려준다 |
| `observer.onNext` / `onError` / `onCompleted` | 값·오류·완료 이벤트 보내기 |
| `subscribe(onNext:onError:onCompleted:onDisposed:)` | 이벤트 받기 |
| `Disposables.create { }` | 구독이 끝날 때 정리 코드 |
| `disposed(by: bag)`, `DisposeBag` | 가방이 해제될 때 구독을 함께 해제 |
| `dispose()` | 구독 직접 해제 |

## 정리

`Observable`은 이벤트를 시간 순서대로 내보내는 시퀀스다. `create`의 구독 클로저는 구독이 시작될 때 실행된다. 같은 cold Observable을 두 번 구독하면 소스가 두 번 실행된다. 이벤트는 `next* (error | completed)?` 규칙을 따른다.

구독은 `Disposable`을 돌려주고, `DisposeBag`으로 수명을 객체에 묶는다. 이때 클로저가 `self`를 강하게 잡으면 객체가 해제되지 않으므로 `[weak self]`를 쓴다.

다음에는 흐름을 가공하는 [Operator — 변환]({{ "/swift/rxswift/operators-transform/" | relative_url }})을 살펴본다.

## 참고

- [RxSwift GitHub](https://github.com/ReactiveX/RxSwift)
- [RxSwift: Getting Started (Observable 규칙, Disposing)](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/GettingStarted.md)
- [ReactiveX: Observable](https://reactivex.io/documentation/observable.html)
