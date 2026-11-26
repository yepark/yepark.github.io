---
title: "Subject"
description: "PublishSubject, BehaviorSubject, ReplaySubject, AsyncSubject와 Relay의 차이, hot·cold Observable, share와 share(replay:scope:)로 구독을 나눠 쓰는 방법을 실행 결과로 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 4
permalink: /swift/rxswift/subject/
last_modified_at: 2026-11-26
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-26
tags: [Swift, RxSwift, Subject, BehaviorSubject, PublishSubject]
---

# Subject
{: .no_toc }

{% include article-toc.md %}

`Observable`은 이벤트를 내보내기만 한다. 밖에서 이벤트를 넣을 수 없다. `Subject`는 Observable이면서 동시에 Observer다. 밖에서 `onNext`로 이벤트를 받아서 구독자들에게 전달할 수 있다.

{: .tip }
Subject는 "방송국의 마이크"다. 누구든 마이크에 대고 말하면(onNext), 그때 라디오를 켜 둔 사람들(구독자)이 모두 듣는다. 네 종류의 Subject는 "늦게 라디오를 켠 사람에게 무엇을 들려줄까"가 다르다.

뷰모델이 뷰에 데이터를 전달하거나, 사용자 입력을 받는 중간 다리 역할을 주로 맡는다. 이 글의 출력은 RxSwift 6.9.1에서 실행한 결과다.

UIKit 코드를 제외한 일반 예제는 명령줄 프로그램에서 개별로 실행한다. 공통 코드를 각 예제 앞에 둔다.

```swift
import Foundation
import RxSwift
import RxRelay

let disposeBag = DisposeBag()
```

## PublishSubject

구독 **이후**에 오는 이벤트만 전달한다. 과거 이벤트를 기억하지 않는다.

```text
subject:  --A-----B-----C-----D---
sub1:           [구독]B----C   (dispose)
sub2:                 [구독]C----D
```

```swift
let subject = PublishSubject<String>()

subject.onNext("A")  // 아직 구독자 없음 — 아무도 못 받음

let sub1 = subject.subscribe(onNext: { print("sub1:", $0) })
subject.onNext("B")

let sub2 = subject.subscribe(onNext: { print("sub2:", $0) })
subject.onNext("C")

sub1.dispose()
subject.onNext("D")
```

```text
sub1: B
sub1: C
sub2: C
sub2: D
```

버튼 탭, 알림처럼 과거 값이 필요 없는 이벤트에 적합하다.

## BehaviorSubject

초깃값을 가지며, 구독 시 **가장 최근 값**을 즉시 내보낸다.

```swift
let subject = BehaviorSubject<Int>(value: 0)

subject.subscribe(onNext: { print("sub1:", $0) }).disposed(by: disposeBag)
subject.onNext(1)
subject.onNext(2)

subject.subscribe(onNext: { print("sub2:", $0) }).disposed(by: disposeBag)
subject.onNext(3)

print("value():", try subject.value())
```

```text
sub1: 0
sub1: 1
sub1: 2
sub2: 2
sub1: 3
sub2: 3
value():, 3
```

`sub1`은 구독하자마자 초깃값 `0`을, 늦게 온 `sub2`는 그때의 최신 값 `2`를 바로 받았다. 현재 상태를 항상 가져야 하는 UI — 로딩 여부, 현재 사용자 등에 자주 쓰인다.

`value()`로 현재 값을 바로 읽을 수 있다. 그런데 이 메서드는 `throws`다. 왜일까?

```swift
let subject = BehaviorSubject<Int>(value: 0)
subject.onError(URLError(.timedOut))
do {
    _ = try subject.value()
} catch {
    print("value()가 던진 에러:", (error as! URLError).code == .timedOut)
}
subject.subscribe(onNext: { print("next:", $0) },
                  onError: { _ in print("새 구독자: error를 바로 받음") })
    .disposed(by: disposeBag)
```

```text
value()가 던진 에러: true
새 구독자: error를 바로 받음
```

error로 끝난 BehaviorSubject는 더 이상 "현재 값"이 없다. 그래서 `value()`가 그 에러를 던지고, 새 구독자도 값 대신 에러를 받는다.

## ReplaySubject

지정한 개수만큼의 과거 이벤트를 버퍼에 저장한다. 새 구독자가 오면 버퍼를 즉시 재생한다.

```swift
let subject = ReplaySubject<String>.create(bufferSize: 2)
subject.onNext("1")
subject.onNext("2")
subject.onNext("3")

subject.subscribe(onNext: { print("sub1:", $0) }).disposed(by: disposeBag)
subject.onNext("4")
subject.onCompleted()

subject.subscribe(onNext: { print("sub2:", $0) }, onCompleted: { print("sub2: completed") })
    .disposed(by: disposeBag)
```

```text
sub1: 2
sub1: 3
sub1: 4
sub2: 3
sub2: 4
sub2: completed
```

`sub1`은 최근 2개(2, 3)를 받고 이어서 4를 받았다. **completed 뒤에** 구독한 `sub2`도 최근 2개(3, 4)와 completed를 받았다.

{: .warning }
`ReplaySubject.createUnbounded()`는 모든 값을 끝없이 저장한다. 끝나지 않는 흐름에 쓰면 메모리가 계속 늘어난다. 필요한 만큼만 `bufferSize`를 정한다.

## AsyncSubject

completed가 올 때 **마지막 값 하나만** 내보낸다. 완료되기 전까지는 아무것도 내보내지 않는다.

```swift
let subject = AsyncSubject<Int>()
subject.subscribe(onNext: { print("next:", $0) }, onCompleted: { print("completed") })
    .disposed(by: disposeBag)

subject.onNext(1)
subject.onNext(2)
subject.onNext(3)
print("(아직 completed 전)")
subject.onCompleted()
```

```text
(아직 completed 전)
next: 3
completed
```

여러 중간 결과 중 최종 결과만 필요한 경우에 쓴다. 앱 코드에서는 이 역할을 다음 편들에서 다룰 `Single`이 더 자주 맡는다.

## 끝난 Subject에 늦게 구독하면

Subject가 끝난 뒤의 동작도 알아 두자. PublishSubject를 completed한 뒤 구독해 봤다.

```swift
let subject = PublishSubject<Int>()
subject.onCompleted()
subject.onNext(1)      // 이미 끝나서 무시
subject.subscribe(onNext: { print("next:", $0) },
                  onCompleted: { print("늦은 구독자: completed만 받음") })
    .disposed(by: disposeBag)
```

```text
늦은 구독자: completed만 받음
```

끝난 Subject는 되살릴 수 없다. 새 구독자도 종료 이벤트만 받는다. UI 바인딩에 쓰는 Subject가 한 번 error나 completed를 받으면 화면이 그 뒤로 영영 갱신되지 않는 이유다.

## 네 Subject 비교

| Subject | 초깃값 | 새 구독자에게 | 주요 용도 |
| --- | --- | --- | --- |
| `PublishSubject` | 없음 | 구독 이후 이벤트만 | 버튼 탭, 알림 |
| `BehaviorSubject` | 필요 | 최근 값 1개 즉시 | 현재 상태 (로딩, 사용자) |
| `ReplaySubject` | 없음 | 최근 N개 즉시 | 최근 로그, 채팅 |
| `AsyncSubject` | 없음 | 완료 시 마지막 1개 | 최종 결과만 필요 |

## Relay: 끝나지 않는 Subject

`PublishRelay`, `BehaviorRelay`, `ReplayRelay`는 Subject를 감싼 타입이다. **completed와 error를 보낼 방법이 아예 없다.** 그래서 위에서 본 "끝나서 바인딩이 죽는" 일이 생기지 않는다.

Relay는 `RxRelay` 모듈에 있다. `RxCocoa`가 `RxRelay`를 다시 내보내므로(`@_exported import RxRelay`) `import RxCocoa`만 해도 쓸 수 있다.

```swift
import RxRelay

// PublishRelay: PublishSubject와 같지만 error·completed 없음
let tapRelay = PublishRelay<Void>()
tapRelay.subscribe(onNext: { print("탭") }).disposed(by: disposeBag)
tapRelay.accept(())  // onNext 대신 accept

// BehaviorRelay: BehaviorSubject와 같지만 error·completed 없음
let textRelay = BehaviorRelay<String>(value: "")
textRelay.subscribe(onNext: { print("text: '\($0)'") }).disposed(by: disposeBag)
textRelay.accept("hello")
print("value:", textRelay.value)   // throws 없이 바로 읽는다

// ReplayRelay: ReplaySubject와 같지만 error·completed 없음
let replayRelay = ReplayRelay<Int>.create(bufferSize: 1)
replayRelay.accept(1); replayRelay.accept(2)
replayRelay.subscribe(onNext: { print("replayRelay:", $0) }).disposed(by: disposeBag)
```

```text
탭
text: ''
text: 'hello'
value: hello
replayRelay: 2
```

`BehaviorRelay.value`는 `throws`가 아니다. 에러로 끝날 일이 없으니 현재 값이 항상 있기 때문이다.

{: .tip }
UI 바인딩에는 Subject 대신 Relay를 쓰는 것이 일반적이다. Subject는 error나 completed로 종료될 수 있어 바인딩이 예상치 않게 끊길 수 있다.

## Subject를 밖에 그대로 드러내지 않기

뷰모델이 `BehaviorRelay`를 `public`으로 열어 두면, 뷰컨트롤러도 `accept`로 값을 바꿀 수 있다. 누가 값을 바꿨는지 추적하기 어려워진다. 안에서는 Relay로 쓰고, 밖에는 `Observable`로만 보여 준다.

```swift
final class CounterViewModel {
    private let countRelay = BehaviorRelay<Int>(value: 0)
    var count: Observable<Int> { countRelay.asObservable() }   // 밖에서는 읽기만
    func increase() { countRelay.accept(countRelay.value + 1) }
}

let vm = CounterViewModel()
vm.count.subscribe(onNext: { print("count:", $0) }).disposed(by: disposeBag)
vm.increase()
vm.increase()
```

```text
count: 0
count: 1
count: 2
```

## Hot과 Cold

[Observable]({{ "/swift/rxswift/observable/" | relative_url }}) 편에서 `create`로 만든 Observable은 구독할 때마다 처음부터 실행됐다. Subject는 다르다. 구독자가 있든 없든 `onNext`를 부르면 그 순간 값이 흐른다(PublishSubject에 처음 넣은 "A"는 아무도 못 받았다).

RxSwift 공식 문서는 ReactiveX의 정의를 인용해 이렇게 설명한다.

| | Hot | Cold |
| --- | --- | --- |
| 언제 일하나 | 구독자가 없어도 값을 만든다 | 구독해야 일을 시작한다 |
| 늦게 온 구독자 | 중간부터 본다 | 처음부터 본다 |
| 자원 | 구독자들이 함께 쓴다 | 구독자마다 따로 만든다 |
| 예 | Subject, UI 이벤트, 현재 시각 | 네트워크 요청, `create`, `just` |

{: .tip }
Hot은 "라디오 생방송"이다. 늦게 켜면 앞부분은 못 듣는다. Cold는 "주문형 영상"이다. 누를 때마다 처음부터 나오고, 사람마다 따로 재생된다.

## share: Cold를 여러 곳에서 같이 쓰기

Cold Observable을 두 곳에서 구독하면 일이 두 번 일어난다. 네트워크 요청이라면 **요청이 두 번** 간다. 실제로 확인하려고, 요청을 받아 두었다가 `respond()`를 부르면 응답하는 가짜 서버를 만들었다.

```swift
final class FakeServer {
    private var pending: [AnyObserver<String>] = []
    private(set) var requestCount = 0
    func request() -> Observable<String> {
        Observable.create { [unowned self] observer in
            self.requestCount += 1
            print("  요청 #\(self.requestCount) 시작")
            self.pending.append(observer)
            return Disposables.create { print("  요청 정리") }
        }
    }
    func respond(_ text: String) {
        let list = pending; pending = []
        list.forEach { $0.onNext(text); $0.onCompleted() }
    }
}
```

### share 없이

```swift
let server = FakeServer()
let user = server.request()
user.subscribe(onNext: { print("이름 라벨:", $0) }).disposed(by: disposeBag)
user.subscribe(onNext: { print("프로필 사진:", $0) }).disposed(by: disposeBag)
server.respond("yep")
print("요청 횟수:", server.requestCount)
```

```text
  요청 #1 시작
  요청 #2 시작
이름 라벨: yep
  요청 정리
프로필 사진: yep
  요청 정리
요청 횟수: 2
```

### share()

`.share()`를 붙이면 첫 구독자가 생길 때 한 번만 구독하고, 그 결과를 모든 구독자에게 나눠 준다.

```swift
let user = server.request().share()
// 나머지는 위와 같다
```

```text
  요청 #1 시작
이름 라벨: yep
프로필 사진: yep
  요청 정리
요청 횟수: 1
```

### 늦게 온 구독자

`share()`의 기본값은 `share(replay: 0, scope: .whileConnected)`다. 응답이 이미 끝난 뒤에 구독하면 어떻게 될까?

```swift
let user = server.request().share()
user.subscribe(onNext: { print("이름 라벨:", $0) }).disposed(by: disposeBag)
server.respond("yep")
user.subscribe(onNext: { print("늦은 구독자:", $0) }).disposed(by: disposeBag)
server.respond("yep(두 번째 응답)")
print("요청 횟수:", server.requestCount)
```

```text
  요청 #1 시작
이름 라벨: yep
  요청 정리
  요청 #2 시작
늦은 구독자: yep(두 번째 응답)
  요청 정리
요청 횟수: 2
```

첫 요청이 completed로 끝나면서 구독자가 0명이 됐다. `.whileConnected`는 "구독자가 있는 동안만" 공유한다는 뜻이라, 늦은 구독자는 **새 요청**을 시작했다.

### share(replay: 1, scope: .forever)

`.forever`는 구독자가 0명이 되어도 마지막 값을 계속 기억한다.

```swift
let user = server.request().share(replay: 1, scope: .forever)
user.subscribe(onNext: { print("이름 라벨:", $0) }).disposed(by: disposeBag)
server.respond("yep")
user.subscribe(onNext: { print("늦은 구독자:", $0) },
               onCompleted: { print("늦은 구독자: completed") })
    .disposed(by: disposeBag)
print("요청 횟수:", server.requestCount)
```

```text
  요청 #1 시작
이름 라벨: yep
  요청 정리
늦은 구독자: yep
늦은 구독자: completed
요청 횟수: 1
```

요청은 한 번, 늦은 구독자도 저장된 `yep`과 completed를 받았다. 한 번 받은 결과를 캐시처럼 쓰고 싶을 때다.

### share(replay: 1): 끝나지 않는 흐름

화면 상태처럼 끝나지 않는 흐름에는 `share(replay: 1)`(scope는 기본값 `.whileConnected`)을 가장 많이 쓴다.

```swift
let source = PublishSubject<Int>()
var sideEffect = 0
let shared = source
    .do(onNext: { _ in sideEffect += 1 })
    .share(replay: 1)

let s1 = shared.subscribe(onNext: { print("구독1:", $0) })
source.onNext(1)
let s2 = shared.subscribe(onNext: { print("구독2(늦게):", $0) })
source.onNext(2)
print("do(onNext:) 실행 횟수:", sideEffect)

s1.dispose(); s2.dispose()
print("구독자가 0명이 된 뒤 다시 구독")
let s3 = shared.subscribe(onNext: { print("구독3:", $0) })
source.onNext(3)
```

```text
구독1: 1
구독2(늦게): 1
구독1: 2
구독2(늦게): 2
do(onNext:) 실행 횟수: 2
구독자가 0명이 된 뒤 다시 구독
구독3: 3
```

- 늦게 온 구독2는 지난 값 `1`을 바로 받았다(replay: 1).
- 구독자가 둘인데 `do`는 값마다 한 번씩, 총 2번만 실행됐다(공유).
- 모두 dispose한 뒤 다시 구독한 구독3은 지난 값 `2`를 받지 못했다. `.whileConnected`라서 구독자가 0명이 될 때 저장해 둔 값을 버렸기 때문이다.

| 쓰는 법 | 늦은 구독자 | 구독자 0명이 되면 |
| --- | --- | --- |
| `share()` | 이후 값만 | 연결 끊음. 다음 구독 때 새로 시작 |
| `share(replay: 1)` | 마지막 1개 먼저 | 연결 끊고 저장한 값도 버림 |
| `share(replay: 1, scope: .forever)` | 마지막 1개 먼저 | 저장한 값을 계속 기억 |

{: .warning }
`share`는 **같은 Observable 인스턴스**를 여러 번 구독할 때만 효과가 있다. `func load() -> Observable<User> { api.user().share() }`처럼 함수 안에서 share를 붙이고 `load()`를 두 번 부르면, 서로 다른 Observable 두 개가 만들어져 요청이 여전히 두 번 간다. share한 결과를 변수에 담아 두고 그 변수를 구독해야 한다.

## 뷰모델에서의 패턴

Subject와 Relay를 뷰모델 입출력으로 구조화하는 방식이다.

```swift
// 실행하지 않음 (AuthService는 예시용 가상 타입)
class LoginViewModel {
    // Input: 뷰에서 뷰모델로
    let username = BehaviorRelay<String>(value: "")
    let password = BehaviorRelay<String>(value: "")
    let loginTap  = PublishRelay<Void>()

    // Output: 뷰모델에서 뷰로
    let isLoginEnabled: Observable<Bool>
    let loginResult: Observable<Result<User, Error>>

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
            .share()   // 결과를 성공 화면·에러 화면 두 곳에서 구독해도 요청은 한 번
    }
}

// ViewController에서 (실행하지 않음, UIKit 코드)
usernameField.rx.text.orEmpty
    .bind(to: viewModel.username)       // 입력 바인딩
    .disposed(by: disposeBag)
passwordField.rx.text.orEmpty
    .bind(to: viewModel.password)
    .disposed(by: disposeBag)
loginButton.rx.tap
    .bind(to: viewModel.loginTap)
    .disposed(by: disposeBag)
viewModel.isLoginEnabled
    .bind(to: loginButton.rx.isEnabled) // 출력 바인딩
    .disposed(by: disposeBag)
```

Input과 Output을 명시적으로 분리하면 테스트할 때 Input에 값을 넣고 Output을 검증하는 구조를 만들기 쉽다. 이 구조를 더 다듬은 형태는 [MVVM + RxSwift]({{ "/swift/rxswift/mvvm/" | relative_url }})에서 다룬다.

## 정리

Subject는 Observable과 Observer를 겸한다. 외부에서 이벤트를 주입해야 할 때 쓴다. 네 Subject는 늦은 구독자에게 무엇을 주는지가 다르다. 끝난 Subject는 되살릴 수 없으므로 UI 바인딩에서는 종료 없는 Relay가 더 안전하다.

Subject는 구독자가 생기기 전에 이벤트를 받을 수 있다. 앞서 만든 서버 예제는 구독마다 새 요청이 시작되는 cold Observable이다. 여러 구독이 요청을 함께 사용하거나 마지막 값을 다시 받아야 할 때는 `share`의 replay 값과 scope를 정한다.

다음에는 어떤 스레드에서 작업을 실행하고 결과를 받을지 제어하는 [Scheduler]({{ "/swift/rxswift/scheduler/" | relative_url }})를 살펴본다.

## 참고

- [RxSwift: Subjects](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/Subjects.md)
- [RxSwift: Hot and Cold Observables](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/HotAndColdObservables.md)
- [RxSwift: Sharing subscription and share operator](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/GettingStarted.md#sharing-subscription-and-share-operator)
- [RxSwift 소스: ShareReplayScope.swift](https://github.com/ReactiveX/RxSwift/blob/main/RxSwift/Observables/ShareReplayScope.swift)
- [ReactiveX: Subject](https://reactivex.io/documentation/subject.html)
- [RxRelay 소스](https://github.com/ReactiveX/RxSwift/tree/main/RxRelay)
