---
title: "Operator — 결합"
description: "merge, combineLatest, zip, withLatestFrom, startWith, concat으로 여러 Observable을 하나의 흐름으로 합치는 방법과 완료·에러 규칙을 마블 다이어그램과 실행 결과로 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 3
permalink: /swift/rxswift/operators-combine/
last_modified_at: 2026-11-26
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-26
tags: [Swift, RxSwift, Operator, merge, combineLatest, zip]
---

# Operator — 결합
{: .no_toc }

{% include article-toc.md %}

앱 화면은 여러 소스의 이벤트를 한꺼번에 다룬다. 두 텍스트필드가 모두 채워졌을 때 버튼을 켜거나, 두 API 응답을 기다려 화면을 그리거나, 버튼을 누른 순간 입력창의 값을 가져가야 한다. 이럴 때 결합 Operator를 쓴다.

이 글의 출력은 RxSwift 6.9.1에서 실행한 결과다.

UIKit 코드를 제외한 일반 예제는 명령줄 프로그램에서 개별로 실행한다. 공통 코드를 각 예제 앞에 둔다. XCTest 예제는 테스트 타깃에 넣는다.

```swift
import Foundation
import RxSwift

let disposeBag = DisposeBag()
```

## 한눈에 비교하기

먼저 같은 두 흐름 `a`, `b`를 각 연산자에 넣고 결과를 나란히 놓아 보자. `TestScheduler`(가상 시계, [변환]({{ "/swift/rxswift/operators-transform/" | relative_url }}) 편 참고)로 돌렸고, `시각:값` 형식이다. 아래 코드는 XCTest 타깃에 넣는다. 앞 글에서 같은 타깃에 `describe`를 추가했다면 기존 함수를 사용한다.

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

final class P3Tests: XCTestCase {
    func testCombining() {
        func show(_ name: String, _ make: @escaping (TestableObservable<String>, TestableObservable<String>) -> Observable<String>) {
            let scheduler = TestScheduler(initialClock: 0)
            let a = scheduler.createHotObservable([
                .next(100, "a1"), .next(300, "a2"), .next(400, "a3"), .completed(500)
            ])
            let b = scheduler.createHotObservable([
                .next(200, "b1"), .next(250, "b2"), .completed(450)
            ])
            let res = scheduler.start(created: 0, subscribed: 0, disposed: 1000) { make(a, b) }
            print(name.padding(toLength: 15, withPad: " ", startingAt: 0), describe(res.events))
        }
        show("a") { a, _ in a.asObservable() }
        show("b") { _, b in b.asObservable() }
        show("merge") { a, b in Observable.merge(a.asObservable(), b.asObservable()) }
        show("combineLatest") { a, b in Observable.combineLatest(a, b) { "\($0)\($1)" } }
        show("zip") { a, b in Observable.zip(a, b) { "\($0)\($1)" } }
        show("a.withLatest(b)") { a, b in a.withLatestFrom(b) { "\($0)\($1)" } }
    }
}
```

```text
a               100:a1  300:a2  400:a3  500:|
b               200:b1  250:b2  450:|
merge           100:a1  200:b1  250:b2  300:a2  400:a3  500:|
combineLatest   200:a1b1  250:a1b2  300:a2b2  400:a3b2  500:|
zip             200:a1b1  300:a2b2  500:|
a.withLatest(b) 300:a2b2  400:a3b2  500:|
```

이 표 하나에 결합 연산자의 성격이 다 들어 있다. 아래에서 하나씩 풀어 본다.

## merge

여러 Observable을 하나로 합친다. 어느 쪽에서 이벤트가 오든 **온 순서대로** 내보낸다.

```text
a:      --a1--------------a2----a3----|
b:      ---------b1--b2--------|
merge:  --a1-----b1--b2---a2----a3----|
```

```swift
let a = PublishSubject<String>()
let b = PublishSubject<String>()

Observable.merge(a, b)
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)

a.onNext("A1")
b.onNext("B1")
a.onNext("A2")
```

```text
A1
B1
A2
```

타입이 같아야 한다. "당겨서 새로고침"과 "다시 시도 버튼"처럼 출처는 다르지만 같은 일을 시키는 이벤트를 하나로 묶을 때 쓴다.

**끝나는 규칙:** 위 비교표에서 b는 450에 끝났지만 merge는 a까지 끝난 500에 completed됐다. merge는 **모두 끝나야** 끝난다. 반대로 에러는 **하나만 나도** 전체가 끝난다.

```swift
extension P3Tests {
    func testErrorPropagation() {
        let scheduler = TestScheduler(initialClock: 0)
        let a = scheduler.createHotObservable([.next(100, "a1"), .next(300, "a2")])
        let b = scheduler.createHotObservable([.next(150, "b1"), .error(200, URLError(.timedOut))] as [Recorded<Event<String>>])
        let res = scheduler.start(created: 0, subscribed: 0, disposed: 1000) {
            Observable.merge(a.asObservable(), b.asObservable())
        }
        print("merge + 한쪽 error:", describe(res.events))
    }
}
```

```text
merge + 한쪽 error: 100:a1  150:b1  200:error
```

300에 a가 보낸 `a2`는 오지 않았다. b의 에러로 merge 전체가 끝났기 때문이다.

## combineLatest

여러 Observable 각각의 **최신 값**을 묶어 내보낸다. 어느 한쪽이라도 바뀌면 다시 내보낸다. 단, **모두가 최소 한 번씩** 값을 내보낸 뒤부터 동작한다.

```text
a:             --a1--------------a2----a3----|
b:             ---------b1--b2--------|
combineLatest: ---------a1b1-a1b2-a2b2--a3b2-|
```

비교표에서 a1(100)은 혼자서는 나가지 못하고, b1이 온 200에 처음으로 `a1b1`이 나갔다. 끝나는 시점은 merge와 같이 **모두 끝난** 500이다.

폼 검사에 가장 많이 쓰인다. `BehaviorSubject`는 초깃값을 가진 Subject라서, 구독하자마자 빈 문자열을 하나씩 내보낸다.

```swift
let username = BehaviorSubject<String>(value: "")
let password = BehaviorSubject<String>(value: "")

Observable.combineLatest(username, password) { u, p in
    "(\(u), \(p)) → \(u.count >= 4 && p.count >= 8)"
}
.subscribe(onNext: { print($0) })
.disposed(by: disposeBag)

username.onNext("yep")
username.onNext("yepa")
password.onNext("pass")
password.onNext("password")
```

```text
(, ) → false
(yep, ) → false
(yepa, ) → false
(yepa, pass) → false
(yepa, password) → true
```

두 초깃값이 이미 있어서 구독하자마자 `(, ) → false`가 나왔다. 그다음부터는 어느 쪽이 바뀌든 매번 다시 계산했다.

버튼의 `isEnabled`에 연결할 때는 같은 값이 반복되지 않도록 `distinctUntilChanged()`를 붙인다.

```swift
Observable.combineLatest(user2, pass2) { $0.count >= 4 && $1.count >= 8 }
    .distinctUntilChanged()
    .subscribe(onNext: { print("버튼 활성화:", $0) })
    .disposed(by: disposeBag)
// 위와 같은 순서로 입력한 뒤 "password1"을 한 번 더 넣었다
```

```text
버튼 활성화: false
버튼 활성화: true
```

다섯 번 바뀌었지만 버튼 상태가 실제로 바뀐 두 번만 나갔다.

{: .warning }
`PublishSubject`나 텍스트필드처럼 **처음 값이 없는** 흐름을 combineLatest에 넣으면, 둘 다 한 번씩 값이 올 때까지 아무것도 나오지 않는다. "버튼이 처음에 켜져 있다"는 버그가 이때 생긴다. 초깃값이 필요하면 `startWith`를 붙인다.

## zip

여러 Observable의 값을 **순서대로 짝지어** 내보낸다. 첫 번째끼리, 두 번째끼리 묶는다. 한쪽이 빠르면 느린 쪽의 짝을 기다린다.

```text
a:    --a1--------------a2----a3----|
b:    ---------b1--b2--------|
zip:  ---------a1b1-----a2b2--------|
```

비교표에서 `a1b1`(200), `a2b2`(300)가 나왔고 `a3`는 짝(b3)이 없어서 버려졌다.

```swift
let names  = Observable.of("Alice", "Bob", "Carol")
let scores = Observable.of(90, 85)

Observable.zip(names, scores) { "\($0): \($1)" }
    .subscribe(onNext: { print($0) }, onCompleted: { print("completed") })
    .disposed(by: disposeBag)
```

```text
Alice: 90
Bob: 85
completed
```

점수가 두 개뿐이라 Carol은 짝이 없어 나오지 않았다.

두 API 요청을 동시에 보내고 **둘 다 도착하면** 화면을 그릴 때 쓴다. 각 요청이 값 하나를 내보내고 끝나는 경우, zip은 "둘 다 기다리기"가 된다.

**combineLatest vs zip:**

```text
combineLatest: 한쪽이 바뀌면 상대방의 최신 값과 즉시 결합 (값을 재사용한다)
zip:           n번째끼리만 결합. 한 번 쓴 값은 다시 쓰지 않는다
```

## withLatestFrom

왼쪽 Observable이 이벤트를 내보낼 때 **그 순간** 오른쪽의 최신 값을 가져온다. 오른쪽이 바뀌는 것은 트리거가 되지 않는다.

```text
a:               --a1--------------a2----a3----|
b:               ---------b1--b2--------|
a.withLatest(b): ------------------a2b2--a3b2--|
```

비교표에서 a1(100)은 그때 b에 값이 없어서 버려졌다. b가 바뀐 200, 250에는 아무것도 나가지 않았다. b가 450에 끝난 뒤에도 a3(400)는 마지막 값 b2를 썼고, 전체는 왼쪽(a)이 끝난 500에 끝났다.

버튼 탭으로 확인해 보자.

```swift
let tap = PublishSubject<Void>()
let text = BehaviorSubject<String>(value: "")

tap.withLatestFrom(text)
    .subscribe(onNext: { print("탭 순간의 값:", $0) })
    .disposed(by: disposeBag)

text.onNext("a")
text.onNext("ab")
tap.onNext(())
text.onNext("abc")
tap.onNext(())
tap.onNext(())
```

```text
탭 순간의 값: ab
탭 순간의 값: abc
탭 순간의 값: abc
```

글자를 칠 때는 아무 일도 없고, 탭할 때만 그 순간의 값이 나갔다.

{: .question }
"로그인" 버튼에 `combineLatest(tap, text)`를 쓰면 무슨 일이 생길까? 한 번 탭한 뒤부터는 글자를 칠 때마다 로그인 요청이 나간다. 탭이 트리거여야 하는 곳에는 `withLatestFrom`을 쓴다.

## startWith

구독 시작 시 첫 번째로 내보낼 값을 앞에 끼워 넣는다.

```swift
Observable.of(2, 3, 4)
    .startWith(0, 1)
    .subscribe(onNext: { print($0, terminator: " ") }, onCompleted: { print("|") })
    .disposed(by: disposeBag)
```

```text
0 1 2 3 4 |
```

테이블뷰에 로딩 전 빈 배열을 먼저 보여 줄 때, combineLatest에 들어갈 흐름에 초깃값을 줄 때 쓴다.

## concat

여러 Observable을 순서대로 이어 붙인다. 앞의 Observable이 completed되어야 다음 Observable을 **구독하기 시작한다.**

캐시 → 네트워크 순으로 데이터를 불러오는 패턴을 흉내 냈다.

```swift
func cache() -> Observable<String> {
    Observable.create { o in
        print("  캐시 읽기 시작"); o.onNext("캐시 데이터"); o.onCompleted()
        return Disposables.create()
    }
}
func network() -> Observable<String> {
    Observable.create { o in
        print("  네트워크 요청 시작"); o.onNext("서버 데이터"); o.onCompleted()
        return Disposables.create()
    }
}

Observable.concat([cache(), network()])
    .subscribe(onNext: { print("화면 갱신:", $0) }, onCompleted: { print("completed") })
    .disposed(by: disposeBag)
```

```text
  캐시 읽기 시작
화면 갱신: 캐시 데이터
  네트워크 요청 시작
화면 갱신: 서버 데이터
completed
```

앞쪽이 끝나지 않으면 뒤쪽은 시작도 하지 않는다.

```swift
let endless = PublishSubject<String>()
Observable.concat([endless.asObservable(), network()])
    .subscribe(onNext: { print("화면 갱신:", $0) })
    .disposed(by: disposeBag)
endless.onNext("첫 번째 값")
print("  (endless가 completed를 보내기 전)")
endless.onCompleted()
```

```text
화면 갱신: 첫 번째 값
  (endless가 completed를 보내기 전)
  네트워크 요청 시작
화면 갱신: 서버 데이터
```

{: .warning }
버튼 탭, 텍스트 변경처럼 **끝나지 않는 흐름**을 concat의 앞쪽에 두면 뒤쪽은 영원히 실행되지 않는다.

## 끝나는 규칙 정리

에러 규칙도 확인했다. a는 `100:a1 300:a2 500:|`, b는 `150:b1 200:error`로 두고 돌렸다.

```swift
final class P3ErrorTests: XCTestCase {
    func testErrorsEverywhere() {
        func show(_ name: String, _ make: @escaping (TestableObservable<String>, TestableObservable<String>) -> Observable<String>) {
            let scheduler = TestScheduler(initialClock: 0)
            let a = scheduler.createHotObservable([.next(100, "a1"), .next(300, "a2"), .completed(500)])
            let b = scheduler.createHotObservable([.next(150, "b1"), .error(200, URLError(.timedOut))] as [Recorded<Event<String>>])
            let res = scheduler.start(created: 0, subscribed: 0, disposed: 1000) { make(a, b) }
            print("ERR", name.padding(toLength: 15, withPad: " ", startingAt: 0), describe(res.events))
        }
        show("combineLatest") { a, b in Observable.combineLatest(a, b) { "\($0)\($1)" } }
        show("zip") { a, b in Observable.zip(a, b) { "\($0)\($1)" } }
        show("a.withLatest(b)") { a, b in a.withLatestFrom(b) { "\($0)\($1)" } }
        show("concat(b, a)") { a, b in b.asObservable().concat(a.asObservable()) }
    }
}
```

```text
ERR combineLatest   150:a1b1  200:error
ERR zip             150:a1b1  200:error
ERR a.withLatest(b) 200:error
ERR concat(b, a)    150:b1  200:error
```

넷 모두 b의 에러가 난 200에 끝났다. `withLatestFrom`은 오른쪽(b)이 트리거가 아닌데도 오른쪽의 에러는 그대로 전달했다.

위에서 실행한 결과를 모으면 이렇다.

| Operator | 값이 나가는 때 | completed | error |
| --- | --- | --- | --- |
| `merge` | 아무 쪽에서 값이 올 때 | 모두 끝나면 | 하나라도 나면 즉시 |
| `combineLatest` | 모두 값이 하나씩 생긴 뒤, 아무 쪽이 바뀔 때 | 모두 끝나면 | 하나라도 나면 즉시 |
| `zip` | n번째 짝이 모두 모였을 때 | 비교표에서는 a가 끝난 500 | 하나라도 나면 즉시 |
| `withLatestFrom` | 왼쪽이 값을 낼 때만 | 왼쪽이 끝나면 | 어느 쪽이든 나면 즉시 |
| `concat` | 앞 순서대로 | 마지막까지 끝나면 | 하나라도 나면 즉시 |

## 실습: 로그인 버튼 활성화 + 탭 처리

UIKit 화면에서는 이렇게 조합한다. 입력값으로 버튼을 켜고 끄는 일은 `combineLatest`, 탭한 순간 값을 가져가는 일은 `withLatestFrom`이 맡는다.

```swift
// 실행하지 않음 (UIKit 코드)
let usernameStream = usernameField.rx.text.orEmpty.asObservable()
let passwordStream = passwordField.rx.text.orEmpty.asObservable()
let credentials = Observable.combineLatest(usernameStream, passwordStream)

// 유효성 — 두 필드 모두 감시
credentials
    .map { u, p in u.count >= 4 && p.count >= 8 }
    .distinctUntilChanged()
    .bind(to: loginButton.rx.isEnabled)
    .disposed(by: disposeBag)

// 버튼 탭 — 탭 순간의 값만 가져가기
loginButton.rx.tap
    .withLatestFrom(credentials)
    .flatMapFirst { username, password in        // 요청 중 연타는 무시
        viewModel.login(username: username, password: password)
            .catch { error in                      // 실패해도 버튼은 계속 동작하게
                print("실패:", error)
                return .empty()
            }
    }
    .subscribe(onNext: { print("로그인 성공:", $0) })
    .disposed(by: disposeBag)
```

`rx.text.orEmpty`는 텍스트필드의 현재 값을 구독하자마자 하나 내보낸다. 그래서 combineLatest가 처음부터 동작한다.

`flatMapFirst`는 요청이 진행 중일 때 들어온 탭을 버린다. `catch`를 `flatMapFirst` **안쪽**에 둔 것도 중요하다. 바깥에 두면 한 번 실패한 뒤로 버튼이 더 이상 반응하지 않는다. 이유는 [Error Handling]({{ "/swift/rxswift/error-handling/" | relative_url }})에서 실행해 본다.

## 정리

| Operator | 동작 | 적합한 상황 |
| --- | --- | --- |
| `merge` | 도착 순서대로 합침 | 같은 타입의 여러 소스 |
| `combineLatest` | 최신 값끼리 결합 | 폼 유효성, 복합 상태 |
| `zip` | n번째끼리 짝지어 결합 | 두 요청을 모두 기다리기 |
| `withLatestFrom` | 트리거 시 상대방 최신값 | 버튼 탭 + 입력값 |
| `concat` | 완료 후 다음으로 | 캐시 → 네트워크 |
| `startWith` | 초깃값 삽입 | 초기 상태 보장 |

다음에는 외부에서 이벤트를 주입할 수 있는 [Subject]({{ "/swift/rxswift/subject/" | relative_url }})와, 구독을 나눠 쓰는 `share`를 살펴본다.

## 참고

- [ReactiveX: Combining Operators](https://reactivex.io/documentation/operators.html#combining)
- [ReactiveX: CombineLatest](https://reactivex.io/documentation/operators/combinelatest.html)
- [ReactiveX: Zip](https://reactivex.io/documentation/operators/zip.html)
- [RxSwift ObservableType 연산자 문서](https://docs.rxswift.org/protocols/observabletype)
