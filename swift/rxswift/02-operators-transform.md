---
title: "Operator — 변환"
description: "RxSwift의 map, flatMap, flatMapLatest, concatMap, compactMap, filter, scan, take, skip, distinctUntilChanged, debounce, throttle을 마블 다이어그램과 실행 결과로 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 2
permalink: /swift/rxswift/operators-transform/
last_modified_at: 2026-11-26
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-26
tags: [Swift, RxSwift, Operator, map, flatMap, filter]
---

# Operator — 변환
{: .no_toc }

{% include article-toc.md %}

Operator는 Observable이 내보내는 이벤트를 가공하는 함수다. 여러 Operator를 체인으로 연결해 데이터 변환 파이프라인을 선언적으로 표현할 수 있다. 이 글에서는 가장 자주 쓰이는 변환·필터링 Operator를 다룬다.

{: .tip }
Operator는 공장의 컨베이어 벨트 위에 놓인 기계다. 물건(값)이 지나갈 때마다 모양을 바꾸거나(map), 불량품을 빼거나(filter), 잠시 모았다가 내보낸다(debounce). 각 Operator는 원본을 바꾸지 않고 **새 Observable**을 돌려준다.

이 글의 출력은 RxSwift 6.9.1에서 실행한 결과다. 짧게 보이려고 받은 이벤트를 한 줄로 찍는 작은 함수를 썼다. 값은 그대로, completed는 `|`로 적는다.

UIKit 코드를 제외한 일반 예제는 명령줄 프로그램에서 개별로 실행한다. 공통 코드를 각 예제 앞에 둔다. XCTest 예제는 테스트 타깃에 넣는다.

```swift
import Foundation
import RxSwift

let disposeBag = DisposeBag()
```

```swift
func run<T>(_ name: String, _ o: Observable<T>) {
    var out: [String] = []
    o.subscribe { e in
        switch e {
        case .next(let v): out.append("\(v)")
        case .error(let err): out.append("error(\(err))")
        case .completed: out.append("|")
        }
    }.disposed(by: disposeBag)
    print(name + ":", out.joined(separator: " "))
}
```

## map

Swift의 `Array.map`과 같다. 각 `next` 이벤트의 값을 변환한다.

```text
--1--2--3--|
  map { $0 * 10 }
--10-20-30-|
```

```swift
run("map", Observable.of(1, 2, 3).map { $0 * 10 })
```

```text
map: 10 20 30 |
```

UI 작업에서 자주 쓰이는 패턴 — 모델을 뷰 텍스트로 변환:

```swift
// 실행하지 않음 (UIKit 코드)
viewModel.user       // Observable<User>
    .map { $0.name } // Observable<String>
    .bind(to: nameLabel.rx.text)
    .disposed(by: disposeBag)
```

## compactMap

nil을 걸러내는 map이다. 변환 결과가 nil이면 버리고, nil이 아닌 값만 꺼내서 내보낸다.

```swift
run("compactMap", Observable.of("1", "two", "3", "four", "5").compactMap { Int($0) })
```

```text
compactMap: 1 3 5 |
```

## filter

조건을 만족하는 이벤트만 통과시킨다.

```text
--1--2--3--4--5--6--|
  filter { $0 % 2 == 0 }
-----2-----4-----6--|
```

```swift
run("filter", Observable.of(1, 2, 3, 4, 5, 6).filter { $0 % 2 == 0 })
```

```text
filter: 2 4 6 |
```

## scan

값이 올 때마다 **지금까지의 결과에 새 값을 더해 가며** 중간 결과를 내보낸다. 누적 합, 상태 쌓기에 쓴다.

```text
--1--2--3--4--|
  scan(0) { sum, x in sum + x }
--1--3--6--10-|
```

```swift
run("scan", Observable.of(1, 2, 3, 4).scan(0) { sum, x in sum + x })
run("reduce", Observable.of(1, 2, 3, 4).reduce(0) { sum, x in sum + x })
```

```text
scan: 1 3 6 10 |
reduce: 10 |
```

`reduce`는 같은 계산을 하지만 **completed가 온 뒤에 최종값 하나만** 내보낸다. 끝나지 않는 흐름(버튼 탭 등)에 `reduce`를 쓰면 영원히 값이 나오지 않는다. 그래서 앱에서는 `scan`을 훨씬 자주 쓴다.

장바구니처럼 "동작(action)이 올 때마다 상태를 바꾸는" 코드를 scan으로 쓰면 이렇다.

```swift
enum Action { case add(String), removeAll }
let actions = PublishSubject<Action>()

actions
    .scan([String]()) { list, action in
        switch action {
        case .add(let item): return list + [item]
        case .removeAll:     return []
        }
    }
    .subscribe(onNext: { print("장바구니:", $0) })
    .disposed(by: disposeBag)

actions.onNext(.add("사과"))
actions.onNext(.add("우유"))
actions.onNext(.removeAll)
```

```text
장바구니: ["사과"]
장바구니: ["사과", "우유"]
장바구니: []
```

`PublishSubject`는 밖에서 값을 넣을 수 있는 Observable이다. 자세한 내용은 [Subject]({{ "/swift/rxswift/subject/" | relative_url }}) 편에서 다룬다.

## flatMap

각 이벤트를 새로운 Observable로 변환하고, 그 결과를 하나의 흐름으로 합친다. 비동기 연쇄 작업에 가장 많이 쓰인다.

```swift
struct User { let id: Int; let name: String }

func fetchPosts(userId: Int) -> Observable<String> {
    Observable.of("user\(userId)-Post A", "user\(userId)-Post B")  // 실제로는 네트워크 요청
}

let users = Observable.of(User(id: 1, name: "yep"), User(id: 2, name: "bob"))
run("flatMap", users.flatMap { fetchPosts(userId: $0.id) })
```

```text
flatMap: user1-Post A user1-Post B user2-Post A user2-Post B |
```

**map vs flatMap:** 같은 클로저를 map에 넣으면 "Observable 안에 Observable"이 생긴다. 아래 두 줄은 타입을 적어 두고 컴파일해서 확인했다.

```swift
let nested: Observable<Observable<String>> = users.map { fetchPosts(userId: $0.id) }
let flat: Observable<String>               = users.flatMap { fetchPosts(userId: $0.id) }
```

`flatMap`은 안쪽 Observable을 구독해서 그 값들을 바깥 흐름으로 꺼내 준다. 이것을 **평탄화(flatten)**라고 한다. 상자 안의 상자를 열어 내용물만 한 줄로 늘어놓는 것과 같다.

## flatMap 4형제: 새 이벤트가 올 때 이전 작업은?

안쪽 작업에 시간이 걸리면 문제가 생긴다. 이전 작업이 끝나기 전에 새 이벤트가 오면 어떻게 할까? 답에 따라 네 가지 연산자가 있다.

| Operator | 이전 내부 Observable | 주요 용도 |
| --- | --- | --- |
| `flatMap` | 시작한 작업을 모두 유지 | 순서 무관한 병렬 요청 |
| `flatMapLatest` | 취소 | 검색, 자동완성 |
| `flatMapFirst` | 새 것을 무시 | 버튼 탭 중복 방지 |
| `concatMap` | 끝날 때까지 기다렸다가 다음 | 순서 보장 직렬 요청 |

말로만 보면 헷갈린다. 버튼을 100, 110, 120 시점에 A, B, C로 세 번 누르고, 누를 때마다 **15만큼 걸리는 요청**을 보내는 상황을 실제로 돌려 봤다.

시간을 정확히 재기 위해 `RxTest`의 `TestScheduler`를 썼다. 이것은 진짜 시계 대신 **가상 시계**로 도는 스케줄러다. 아래 코드는 XCTest 타깃에 넣는다. 숫자 하나가 "1틱"이고, 기다리지 않고 즉시 결과가 나온다. 자세한 사용법은 [MVVM + RxSwift]({{ "/swift/rxswift/mvvm/" | relative_url }}) 편의 테스트 부분에서 다룬다.

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

final class P2Tests: XCTestCase {
    // 버튼을 100, 110, 120틱에 누른다. 요청은 15틱 뒤 응답한다.
    func flatten(_ name: String,
                 _ op: @escaping (Observable<String>, @escaping (String) -> Observable<String>) -> Observable<String>) {
        let scheduler = TestScheduler(initialClock: 0)
        let taps = scheduler.createHotObservable([
            .next(100, "A"), .next(110, "B"), .next(120, "C"), .completed(200)
        ])
        let request: (String) -> Observable<String> = { tap in
            Observable.just("\(tap)완료")
                .delay(.seconds(15), scheduler: scheduler)
        }
        let res = scheduler.start(created: 0, subscribed: 0, disposed: 1000) {
            op(taps.asObservable(), request)
        }
        print(name.padding(toLength: 14, withPad: " ", startingAt: 0), describe(res.events))
    }

    func testFlatteningOperators() {
        flatten("flatMap") { $0.flatMap($1) }
        flatten("flatMapLatest") { $0.flatMapLatest($1) }
        flatten("flatMapFirst") { $0.flatMapFirst($1) }
        flatten("concatMap") { $0.concatMap($1) }
    }
}
```

```text
flatMap        115:A완료  125:B완료  135:C완료  200:|
flatMapLatest  135:C완료  200:|
flatMapFirst   115:A완료  135:C완료  200:|
concatMap      115:A완료  131:B완료  147:C완료  200:|
```

마블로 그리면 이렇다.

```text
탭        A(100) B(110) C(120)
flatMap        ── A완료(115) ── B완료(125) ── C완료(135)   겹쳐서 실행할 수 있음
flatMapLatest  ─────────────────────────── C완료(135)   B가 오면 A 취소, C가 오면 B 취소
flatMapFirst   ── A완료(115) ───────────── C완료(135)   A 진행 중 온 B는 버림, C는 A가 끝난 뒤라 받음
concatMap      ── A완료(115) ── B완료(131) ── C완료(147)  A가 끝나야 B 시작, B가 끝나야 C 시작
```

{: .note }
`concatMap`의 131, 147이 130, 145가 아닌 이유: `TestScheduler`는 "지금 당장" 하라고 예약된 일을 1틱 뒤에 실행한다(`simulateProcessingDelay` 기본값 `true`). A가 끝난 115에 B를 시작하라는 예약이 116에 실행되고, 116 + 15 = 131이 된 것이다. 진짜 앱에서는 이런 1틱 차이가 없다.

`flatMapLatest`는 검색에 딱 맞다. 사용자가 "swift"를 타이핑할 때 "s", "sw", "swi"... 각 단계의 검색 요청 중 마지막 것만 살아남는다.

```swift
// 실행하지 않음 (UIKit 코드)
searchField.rx.text.orEmpty
    .flatMapLatest { query in search(query: query) }
    .bind(to: resultsTableView.rx.items(...))
    .disposed(by: disposeBag)
```

{: .question }
회원가입 버튼을 빠르게 두 번 눌렀을 때 요청이 두 번 가면 안 된다. 네 형제 중 무엇을 쓸까? 진행 중인 요청이 있으면 새 탭을 버리는 `flatMapFirst`다.

## take / skip

앞에서 n개만 받거나, n개를 건너뛴다. `take(n)`은 n개를 받으면 바로 completed를 보낸다.

```swift
run("take(3)", Observable.of(1, 2, 3, 4, 5).take(3))
run("skip(2)", Observable.of(1, 2, 3, 4, 5).skip(2))
run("take(while:)", Observable.of(1, 2, 5, 1, 2).take(while: { $0 < 3 }))
run("skip(while:)", Observable.of(1, 2, 5, 1, 2).skip(while: { $0 < 3 }))
```

```text
take(3): 1 2 3 |
skip(2): 3 4 5 |
take(while:): 1 2 |
skip(while:): 5 1 2 |
```

`take(while:)`은 조건이 처음 거짓이 되는 순간(5) 끝난다. 뒤에 다시 1, 2가 와도 받지 않는다. `skip(while:)`도 마찬가지로, 조건이 한 번 거짓이 된 뒤로는 모두 통과시킨다.

`take(until:)`을 쓰면 다른 Observable이 이벤트를 내보낼 때까지만 받는다.

```swift
let source = PublishSubject<Int>()
let stop = PublishSubject<Void>()
source.take(until: stop)
    .subscribe(onNext: { print("next:", $0) }, onCompleted: { print("completed") })
    .disposed(by: disposeBag)
source.onNext(1)
source.onNext(2)
stop.onNext(())
source.onNext(3)
```

```text
next: 1
next: 2
completed
```

`stop`이 값을 내보내자 흐름이 completed로 끝났고, 그 뒤의 `3`은 오지 않았다. 뷰가 사라질 때 자동으로 구독을 끊는 패턴에 활용된다.

```swift
// 실행하지 않음 (RxCocoa의 NSObject.rx.deallocated 사용)
Observable<Int>.interval(.seconds(1), scheduler: MainScheduler.instance)
    .take(until: self.rx.deallocated)  // self가 해제될 때 종료
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
```

## distinctUntilChanged

**바로 앞 값과** 같으면 버린다. UI 업데이트 최적화에 유용하다.

```text
--1--1--2--2--3--1--|
  distinctUntilChanged()
--1-----2-----3--1--|
```

```swift
run("distinctUntilChanged", Observable.of(1, 1, 2, 2, 3, 1).distinctUntilChanged())
```

```text
distinctUntilChanged: 1 2 3 1 |
```

마지막 `1`은 통과했다. 앞 값(3)과만 비교하기 때문이다. "전체에서 중복 제거"가 아니다.

구조체 전체가 아니라 특정 프로퍼티만 비교하고 싶으면 키 경로를 넘긴다.

```swift
struct Profile { let id: Int; let nickname: String }
run("distinctUntilChanged(\\.id)",
    Observable.of(Profile(id: 1, nickname: "a"), Profile(id: 1, nickname: "b"), Profile(id: 2, nickname: "c"))
        .distinctUntilChanged(\.id)
        .map { "\($0.id)/\($0.nickname)" })
```

```text
distinctUntilChanged(\.id): 1/a 2/c |
```

id가 같은 `1/b`는 닉네임이 달라도 버려졌다.

## debounce / throttle

빠르게 연속으로 오는 이벤트를 제어한다. 둘 다 "덜 보내기"지만 방식이 다르다.

- `debounce(t)`: 이벤트가 오고 **t 동안 조용하면** 마지막 값을 내보낸다. 계속 입력 중이면 아무것도 안 내보낸다.
- `throttle(t)`: 첫 이벤트를 바로 내보내고, t 동안 오는 것은 모아 둔다. 기본값(`latest: true`)이면 t가 끝날 때 **그 사이의 마지막 값**도 내보낸다.

사용자가 100, 110, 120에 "s", "sw", "swi"를 빠르게 치고, 쉬었다가 300, 305에 "swif", "swift"를 친 상황을 `TestScheduler`로 돌렸다. 기다리는 시간은 50틱이다.

같은 테스트 파일에 다음 메서드를 추가한다.

```swift
extension P2Tests {
    func rateLimit(_ name: String, _ op: @escaping (Observable<String>, TestScheduler) -> Observable<String>) {
        let scheduler = TestScheduler(initialClock: 0)
        // 사용자가 s, sw, swi를 빠르게 치고, 잠깐 쉬었다가 swif, swift를 친다.
        let typing = scheduler.createHotObservable([
            .next(100, "s"), .next(110, "sw"), .next(120, "swi"),
            .next(300, "swif"), .next(305, "swift"),
            .completed(600)
        ])
        let res = scheduler.start(created: 0, subscribed: 0, disposed: 1000) {
            op(typing.asObservable(), scheduler)
        }
        print(name.padding(toLength: 27, withPad: " ", startingAt: 0), describe(res.events))
    }

    func testDebounceThrottle() {
        rateLimit("원본") { o, _ in o }
        rateLimit("debounce(50)") { $0.debounce(.seconds(50), scheduler: $1) }
        rateLimit("throttle(50)") { $0.throttle(.seconds(50), scheduler: $1) }
        rateLimit("throttle(50,latest:false)") { $0.throttle(.seconds(50), latest: false, scheduler: $1) }
    }
}
```

```text
원본                          100:s  110:sw  120:swi  300:swif  305:swift  600:|
debounce(50)                170:swi  355:swift  600:|
throttle(50)                100:s  150:swi  300:swif  350:swift  600:|
throttle(50,latest:false)   100:s  300:swif  600:|
```

- `debounce`: 마지막 입력(120) 후 50 동안 조용하자 170에 `swi`, 305 후 50이 지난 355에 `swift`를 내보냈다.
- `throttle`: 100에 `s`를 바로 보내고, 50이 지난 150에 그 사이 마지막 값 `swi`를 보냈다.
- `throttle(latest: false)`: 창(50) 안에 온 값은 그냥 버린다. 첫 값만 남는다.

{: .warning }
`throttle`의 `latest` 기본값은 `true`다(RxSwift 소스: `throttle(_ dueTime:, latest: Bool = true, scheduler:)`). "버튼 중복 탭 방지"를 위해 `throttle`을 썼는데 창이 끝날 때 탭이 한 번 더 처리된다면 이 때문이다. 첫 탭만 받으려면 `latest: false`를 넘긴다.

| 상황 | 고를 연산자 |
| --- | --- |
| 검색창: 다 칠 때까지 기다렸다가 한 번 | `debounce` |
| 버튼 연타: 첫 탭만, 일정 시간 무시 | `throttle(_, latest: false)` |
| 스크롤 위치: 일정 간격으로 최신 값 | `throttle` (기본값) |

```swift
// 실행하지 않음 (UIKit 코드)
button.rx.tap
    .throttle(.seconds(1), latest: false, scheduler: MainScheduler.instance)
    .subscribe(onNext: { print("탭") })
    .disposed(by: disposeBag)
```

## 실습: 검색창 파이프라인

검색창의 전형적인 조합은 `debounce → distinctUntilChanged → flatMapLatest`다. 세 연산자가 각각 어떤 일을 하는지 `TestScheduler`로 확인했다. 서버는 응답에 80틱이 걸린다고 가정했다.

```swift
extension P2Tests {
    func testSearchPipeline() {
        let scheduler = TestScheduler(initialClock: 0)
        var requested: [String] = []
        func search(_ q: String) -> Observable<[String]> {
            requested.append(q)
            let all = ["Swift", "SwiftUI", "RxSwift", "Combine"]
            return Observable.just(all.filter { $0.localizedCaseInsensitiveContains(q) })
                .delay(.seconds(80), scheduler: scheduler)  // 서버가 80틱 걸린다
        }
        let typing = scheduler.createHotObservable([
            .next(100, "s"), .next(110, "sw"),          // 빠르게 입력
            .next(200, "sw"),                            // 지웠다 다시 써서 같은 값
            .next(300, "co"),
            .next(360, "rx"),                            // co 응답이 오기 전에 바뀜
        ])
        let res = scheduler.start(created: 0, subscribed: 0, disposed: 1000) {
            typing.asObservable()
                .debounce(.seconds(50), scheduler: scheduler)
                .distinctUntilChanged()
                .flatMapLatest { search($0) }
        }
        print("요청한 검색어:", requested)
        print("화면에 그린 결과:", describe(res.events))
    }
}
```

```text
요청한 검색어: ["sw", "co", "rx"]
화면에 그린 결과: 240:["Swift", "SwiftUI", "RxSwift"]  490:["RxSwift"]
```

하나씩 따라가 보자.

1. `debounce`: "s"는 10틱 뒤 "sw"가 와서 버려졌다. 160에 "sw"가 나간다.
2. `distinctUntilChanged`: 250에 debounce를 통과한 "sw"는 직전 값과 같아서 버려졌다. 요청 목록에 "sw"가 한 번만 있다.
3. `flatMapLatest`: 350에 "co" 요청이 나갔다(응답 예정 430). 410에 "rx"가 오자 "co" 요청은 취소됐다. 그래서 `["Combine"]`은 화면에 그려지지 않았다.

{: .tip }
`flatMapLatest` 대신 `flatMap`을 쓰면 "co" 응답이 늦게 도착해서 "rx" 결과를 덮어쓸 수 있다. 사용자는 "rx"를 쳤는데 화면에는 Combine이 보이는, 찾기 어려운 버그가 된다.

실제 앱에서는 이렇게 연결한다.

```swift
// 실행하지 않음 (UIKit 코드)
searchField.rx.text.orEmpty
    .debounce(.milliseconds(300), scheduler: MainScheduler.instance)
    .distinctUntilChanged()
    .flatMapLatest { query in
        api.search(query)
            .catchAndReturn([])          // 에러가 나도 검색창은 살아 있게
    }
    .observe(on: MainScheduler.instance)
    .bind(to: tableView.rx.items(cellIdentifier: "Cell")) { _, item, cell in
        cell.textLabel?.text = item
    }
    .disposed(by: disposeBag)
```

`catchAndReturn`을 `flatMapLatest` **안쪽**에 둔 이유는 [Error Handling]({{ "/swift/rxswift/error-handling/" | relative_url }}) 편에서 실행해 본다.

## 정리

| Operator | 역할 |
| --- | --- |
| `map` | 값 변환 |
| `compactMap` | nil 제거 + 변환 |
| `filter` | 조건으로 걸러내기 |
| `scan` | 누적값을 매번 내보내기 (상태 쌓기) |
| `flatMap` | 새 안쪽 Observable을 시작하고 진행 중인 구독도 유지 |
| `flatMapLatest` | 최신 것만 유지, 이전 것 취소 |
| `flatMapFirst` | 진행 중이면 새 것 무시 |
| `concatMap` | 하나씩 순서대로 |
| `take` / `skip` | 개수·조건으로 자르기 |
| `distinctUntilChanged` | 직전 값과 같으면 버리기 |
| `debounce` | 조용해지면 마지막 값 |
| `throttle` | 일정 간격으로 제한 (`latest` 기본값 `true`) |

다음에는 여러 Observable을 하나로 합치는 [Operator — 결합]({{ "/swift/rxswift/operators-combine/" | relative_url }})을 살펴본다.

## 참고

- [ReactiveX: Operators](https://reactivex.io/documentation/operators.html)
- [ReactiveX: FlatMap](https://reactivex.io/documentation/operators/flatmap.html)
- [ReactiveX: Debounce](https://reactivex.io/documentation/operators/debounce.html)
- [RxSwift 소스: Throttle.swift](https://github.com/ReactiveX/RxSwift/blob/main/RxSwift/Observables/Throttle.swift)
- [RxSwift ObservableType 연산자 문서](https://docs.rxswift.org/protocols/observabletype)
