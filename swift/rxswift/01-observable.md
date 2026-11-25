---
title: "Observable과 Subscribe"
description: "RxSwift의 핵심인 Observable 생성과 구독, next·error·completed 이벤트 흐름, Dispose를 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 1
permalink: /swift/rxswift/observable/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [Swift, RxSwift, Observable, Reactive]
---

# Observable과 Subscribe
{: .no_toc }

{% include article-toc.md %}

RxSwift는 비동기 이벤트를 **값의 흐름(stream)**으로 다룬다. 버튼 탭, 네트워크 응답, 타이머, 텍스트 변경을 모두 같은 방식으로 처리할 수 있다. 이 흐름을 표현하는 핵심 타입이 `Observable`이다.

## Observable이란

`Observable<T>`는 T 타입의 이벤트를 시간 순서대로 내보내는 시퀀스다. 세 종류의 이벤트를 방출한다.

```text
next(value)    — 값을 하나 전달한다
error(Error)   — 오류가 발생하고 시퀀스가 종료된다
completed      — 정상적으로 시퀀스가 끝난다
```

타임라인으로 그리면 이렇다.

```text
--1--2--3--|        정상 종료 (next × 3, completed)
--1--2--X          오류 종료 (next × 2, error)
--1--2--3--4--...  무한 시퀀스 (completed 없음)
```

구독(subscribe)하기 전까지 Observable은 아무것도 하지 않는다. 콜드 옵저버블은 구독할 때마다 처음부터 시작한다.

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

## Subscribe

구독이 있어야 Observable이 실행된다.

```swift
let disposeBag = DisposeBag()

Observable.of("A", "B", "C")
    .subscribe(
        onNext: { value in
            print("next:", value)
        },
        onError: { error in
            print("error:", error)
        },
        onCompleted: {
            print("completed")
        }
    )
    .disposed(by: disposeBag)

// 출력:
// next: A
// next: B
// next: C
// completed
```

`onError`와 `onCompleted`는 생략할 수 있다. 필요한 이벤트만 처리해도 된다.

```swift
Observable.of(1, 2, 3)
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
```

## Dispose와 메모리 관리

구독은 리소스를 소모한다. 타이머, 네트워크 요청, UI 바인딩이 구독으로 살아 있으면 화면을 떠난 뒤에도 계속 실행된다.

`Disposable`을 직접 dispose하거나 `DisposeBag`에 담으면 된다.

```swift
// DisposeBag: 뷰컨트롤러가 해제될 때 담긴 구독을 함께 해제
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

`DisposeBag`은 보통 뷰컨트롤러나 뷰모델의 프로퍼티로 선언한다. 해당 객체가 메모리에서 해제될 때 담긴 Disposable이 모두 dispose된다.

{: .warning }
`disposed(by:)` 없이 구독만 하면 completed나 error가 올 때까지 구독이 유지된다. 무한 시퀀스(타이머, 버튼 탭 등)는 반드시 Dispose 처리를 해야 메모리 누수를 막을 수 있다.

## 이벤트를 값으로 받기

`subscribe(onNext:)` 대신 `subscribe(on:)` 형태로 이벤트 열거형 자체를 받을 수도 있다.

```swift
Observable.of(1, 2, 3)
    .subscribe { event in
        switch event {
        case .next(let value):   print("next:", value)
        case .error(let error):  print("error:", error)
        case .completed:         print("completed")
        }
    }
    .disposed(by: disposeBag)
```

## 실습: 커스텀 Observable로 네트워크 요청 흉내내기

```swift
enum FetchError: Error { case notFound }

func fetchUser(id: Int) -> Observable<String> {
    return Observable.create { observer in
        // 비동기 작업 시뮬레이션
        DispatchQueue.global().asyncAfter(deadline: .now() + 0.5) {
            if id == 1 {
                observer.onNext("yep")
                observer.onCompleted()
            } else {
                observer.onError(FetchError.notFound)
            }
        }
        return Disposables.create()
    }
}

fetchUser(id: 1)
    .subscribe(
        onNext:      { print("user:", $0) },
        onError:     { print("error:", $0) },
        onCompleted: { print("done") }
    )
    .disposed(by: disposeBag)

// 출력 (0.5초 뒤):
// user: yep
// done
```

`Disposables.create()`에 클린업 로직을 넣으면 구독이 dispose될 때 실행된다. 네트워크 작업이라면 `URLSessionDataTask.cancel()`을 여기에 둔다.

## 정리

`Observable`은 이벤트를 시간 순서대로 내보내는 시퀀스다. 구독 전에는 아무것도 실행되지 않는다. 구독은 `Disposable`을 반환하고, `DisposeBag`으로 수명을 객체에 묶는다. next·error·completed 세 이벤트로 모든 비동기 흐름을 표현한다.

다음에는 흐름을 가공하는 [Operator — 변환]({{ "/swift/rxswift/operators-transform/" | relative_url }})을 살펴본다.

## 참고

- [RxSwift GitHub](https://github.com/ReactiveX/RxSwift)
- [ReactiveX: Observable](https://reactivex.io/documentation/observable.html)
