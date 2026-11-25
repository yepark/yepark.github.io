---
title: "Subject"
description: "PublishSubject, BehaviorSubject, ReplaySubject, AsyncSubject의 차이와 뷰모델 바인딩 패턴을 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 4
permalink: /swift/rxswift/subject/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [Swift, RxSwift, Subject, BehaviorSubject, PublishSubject]
---

# Subject
{: .no_toc }

{% include article-toc.md %}

`Observable`은 이벤트를 내보내기만 한다. 외부에서 이벤트를 주입할 수 없다. `Subject`는 Observable이면서 동시에 Observer다. 이벤트를 받아서 구독자에게 전달할 수 있다.

뷰모델이 뷰에 데이터를 전달하거나, 사용자 입력을 처리하는 중간 다리 역할을 주로 맡는다.

## PublishSubject

구독 **이후**에 오는 이벤트만 전달한다. 과거 이벤트를 기억하지 않는다.

```swift
let subject = PublishSubject<String>()

subject.onNext("A")  // 아직 구독자 없음 — 무시됨

let sub1 = subject.subscribe(onNext: { print("sub1:", $0) })

subject.onNext("B")  // sub1: B

let sub2 = subject.subscribe(onNext: { print("sub2:", $0) })

subject.onNext("C")  // sub1: C, sub2: C

sub1.dispose()

subject.onNext("D")  // sub2: D
```

버튼 탭, 알림처럼 과거 값이 필요 없는 이벤트에 적합하다.

## BehaviorSubject

초깃값을 가지며, 구독 시 **가장 최근 값**을 즉시 내보낸다.

```swift
let subject = BehaviorSubject<Int>(value: 0)

subject.subscribe(onNext: { print("sub1:", $0) })
// sub1: 0  ← 초깃값 즉시 받음

subject.onNext(1)  // sub1: 1
subject.onNext(2)  // sub1: 2

subject.subscribe(onNext: { print("sub2:", $0) })
// sub2: 2  ← 최근 값 즉시 받음

subject.onNext(3)  // sub1: 3, sub2: 3
```

현재 상태를 항상 가져야 하는 UI — 로딩 여부, 에러 메시지, 현재 사용자 등에 자주 쓰인다.

현재 값을 명령적으로 읽을 수 있다.

```swift
let isLoading = BehaviorSubject<Bool>(value: false)

// 현재 값 읽기
let current = try? isLoading.value()
print(current)  // Optional(false)
```

## ReplaySubject

지정한 개수만큼의 과거 이벤트를 버퍼에 저장한다. 새 구독자가 오면 버퍼를 즉시 재생한다.

```swift
let subject = ReplaySubject<String>.create(bufferSize: 2)

subject.onNext("1")
subject.onNext("2")
subject.onNext("3")

// 구독 시작 — 최근 2개를 즉시 받음
subject.subscribe(onNext: { print($0) })
// 2
// 3
```

채팅 앱에서 최근 메시지 N개를 새로운 화면에 즉시 보여 줄 때처럼, 일정 개수의 최근 이벤트가 필요한 경우에 사용한다.

## AsyncSubject

completed 이벤트가 올 때 **마지막 값 하나만** 내보낸다. 완료되기 전까지는 아무것도 내보내지 않는다.

```swift
let subject = AsyncSubject<Int>()

subject.subscribe(onNext: { print($0) })

subject.onNext(1)
subject.onNext(2)
subject.onNext(3)
subject.onCompleted()
// 3  ← 마지막 값만
```

여러 중간 결과 중 최종 결과만 필요한 경우에 쓰인다. 실무에서 가장 적게 사용된다.

## 네 Subject 비교

| Subject | 초깃값 | 새 구독자에게 | 주요 용도 |
| --- | --- | --- | --- |
| `PublishSubject` | 없음 | 구독 이후 이벤트만 | 버튼 탭, 알림 |
| `BehaviorSubject` | 필요 | 최근 값 1개 즉시 | 현재 상태 (로딩, 에러) |
| `ReplaySubject` | 없음 | 최근 N개 즉시 | 최근 로그, 채팅 |
| `AsyncSubject` | 없음 | 완료 시 마지막 1개 | 최종 결과만 필요 |

## Relay: completed·error 없는 Subject

`RxCocoa`의 `PublishRelay`와 `BehaviorRelay`는 `completed`와 `error`를 내보내지 않는다. UI 바인딩에서 Subject가 error나 completed로 종료되면 바인딩이 끊어지는 문제를 방지한다.

```swift
import RxCocoa

// PublishRelay: PublishSubject와 같지만 error·completed 없음
let tapRelay = PublishRelay<Void>()
tapRelay.accept(())  // onNext 대신 accept

// BehaviorRelay: BehaviorSubject와 같지만 error·completed 없음
let textRelay = BehaviorRelay<String>(value: "")
textRelay.accept("hello")
print(textRelay.value)  // "hello" ← value 프로퍼티로 직접 접근
```

{: .tip }
UI 바인딩에는 Subject 대신 Relay를 쓰는 것이 일반적이다. Subject는 error나 completed로 종료될 수 있어 바인딩이 예상치 않게 끊길 수 있다.

## 뷰모델에서의 패턴

Subject와 Relay를 뷰모델 입출력으로 구조화하는 방식이다.

```swift
class LoginViewModel {
    // Input: 뷰에서 뷰모델로
    let username = BehaviorRelay<String>(value: "")
    let password = BehaviorRelay<String>(value: "")
    let loginTap  = PublishRelay<Void>()

    // Output: 뷰모델에서 뷰로
    let isLoginEnabled: Observable<Bool>
    let loginResult: Observable<Result<User, Error>>

    private let disposeBag = DisposeBag()

    init() {
        isLoginEnabled = Observable.combineLatest(username, password) {
            $0.count >= 4 && $1.count >= 8
        }

        loginResult = loginTap
            .withLatestFrom(Observable.combineLatest(username, password))
            .flatMapLatest { u, p in
                AuthService.login(username: u, password: p)
                    .map { Result.success($0) }
                    .catch { .just(.failure($0)) }
            }
            .share()
    }
}

// ViewController에서
viewModel.username <~ usernameField.rx.text.orEmpty   // 입력 바인딩
viewModel.isLoginEnabled ~> loginButton.rx.isEnabled  // 출력 바인딩
viewModel.loginTap <~ loginButton.rx.tap
```

Input과 Output을 명시적으로 분리하면 테스트할 때 Input에 Subject로 값을 주입하고 Output을 검증하는 구조를 만들기 쉽다.

## 정리

Subject는 Observable과 Observer를 겸한다. 외부에서 이벤트를 주입해야 할 때 쓴다. UI 바인딩에서는 종료 없는 Relay가 더 안전하다. 뷰모델에서 Input/Output 구조로 쓰면 테스트와 바인딩이 명확해진다.

다음에는 어떤 스레드에서 작업을 실행하고 결과를 받을지 제어하는 [Scheduler]({{ "/swift/rxswift/scheduler/" | relative_url }})를 살펴본다.

## 참고

- [RxSwift: Subjects](https://reactivex.io/documentation/subject.html)
- [RxCocoa: Relay](https://github.com/ReactiveX/RxSwift/blob/main/RxCocoa/Common/Relays/PublishRelay.swift)
