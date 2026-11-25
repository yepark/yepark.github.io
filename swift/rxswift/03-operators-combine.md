---
title: "Operator — 결합"
description: "merge, combineLatest, zip, withLatestFrom으로 여러 Observable을 하나의 흐름으로 합치는 방법을 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 3
permalink: /swift/rxswift/operators-combine/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [Swift, RxSwift, Operator, merge, combineLatest, zip]
---

# Operator — 결합
{: .no_toc }

{% include article-toc.md %}

실제 앱에서는 여러 소스의 이벤트를 한꺼번에 다뤄야 하는 경우가 많다. 두 텍스트필드 모두 채워졌을 때 버튼을 활성화하거나, 두 API 응답을 기다려 화면을 그리거나, 하나의 이벤트가 다른 Observable의 최신 값을 함께 가져가야 할 때 결합 Operator를 쓴다.

## merge

여러 Observable을 하나로 합친다. 어느 쪽에서 이벤트가 오든 순서대로 내보낸다.

```swift
let a = PublishSubject<String>()
let b = PublishSubject<String>()

Observable.merge(a, b)
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)

a.onNext("A1")  // A1
b.onNext("B1")  // B1
a.onNext("A2")  // A2
```

타입이 같아야 한다. 에러 알림, 로그 스트림처럼 출처가 다른 같은 타입의 이벤트를 하나의 구독으로 처리할 때 적합하다.

## combineLatest

여러 Observable 각각의 **최신 값**을 묶어 내보낸다. 모든 Observable이 최소 하나씩 이벤트를 내보낸 뒤부터 동작한다.

```swift
let username = BehaviorSubject<String>(value: "")
let password = BehaviorSubject<String>(value: "")

Observable.combineLatest(username, password) { u, p in
    u.count >= 4 && p.count >= 8
}
.bind(to: loginButton.rx.isEnabled)
.disposed(by: disposeBag)
```

`username`이나 `password` 중 하나라도 바뀌면 조건을 다시 계산한다. 폼 유효성 검사에 가장 많이 쓰이는 패턴이다.

```text
username: --"y"----"ye"---"yep"---"yepa"--
password: --------"pass"----------"password"
result:   --------false--false----true------
```

## zip

두 Observable이 **쌍으로** 이벤트를 내보낼 때마다 결합한다. 한쪽이 더 빠르면 느린 쪽을 기다린다.

```swift
let names   = Observable.of("Alice", "Bob", "Carol")
let scores  = Observable.of(90, 85, 92)

Observable.zip(names, scores) { "\($0): \($1)" }
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)

// Alice: 90
// Bob: 85
// Carol: 92
```

두 API 요청 결과를 1:1로 대응시킬 때 유용하다.

**combineLatest vs zip:**

```text
combineLatest: 한쪽이 바뀌면 상대방의 최신 값과 즉시 결합
zip:           쌍이 맞아야 결합. 느린 쪽을 기다림
```

## withLatestFrom

왼쪽 Observable이 이벤트를 내보낼 때 오른쪽 Observable의 **최신 값**을 가져온다. 오른쪽은 트리거가 되지 않는다.

```swift
loginButton.rx.tap           // 버튼 탭이 트리거
    .withLatestFrom(viewModel.credentials)  // 탭 순간의 최신 입력값
    .flatMapLatest { creds in login(creds) }
    .subscribe(onNext: { ... })
    .disposed(by: disposeBag)
```

버튼이 탭될 때만 텍스트필드 값을 읽는다. 텍스트필드가 바뀔 때마다 반응하지 않는다.

```text
tap:         --------T-----------T------
credentials: --"a"-----"ab"----"abc"---
result:      --------"ab"--------"abc"--
```

## startWith

구독 시작 시 첫 번째로 내보낼 초깃값을 지정한다.

```swift
Observable.of(2, 3, 4)
    .startWith(0, 1)
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
// 0, 1, 2, 3, 4
```

테이블뷰에 로딩 전 빈 배열을 먼저 내보낼 때, 혹은 BehaviorSubject 대신 PublishSubject에 초깃값을 주입할 때 사용한다.

## concat

여러 Observable을 순서대로 이어 붙인다. 앞의 Observable이 completed되어야 다음 Observable로 넘어간다.

```swift
let first  = Observable.of(1, 2, 3)
let second = Observable.of(4, 5, 6)

Observable.concat([first, second])
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
// 1, 2, 3, 4, 5, 6
```

캐시 → 네트워크 순으로 데이터를 불러오는 패턴에 활용된다.

```swift
Observable.concat([
    cache.fetch(key: id),    // 먼저 캐시에서
    network.fetch(id: id)    // 완료되면 네트워크에서
])
.subscribe(onNext: { update(ui: $0) })
.disposed(by: disposeBag)
```

## 실습: 로그인 버튼 활성화 + 탭 처리

```swift
// 입력 스트림
let usernameStream = usernameField.rx.text.orEmpty.asObservable()
let passwordStream = passwordField.rx.text.orEmpty.asObservable()

// 유효성 — combineLatest로 두 필드 모두 감시
let isValid = Observable.combineLatest(usernameStream, passwordStream) {
    u, p in u.count >= 4 && p.count >= 8
}
.distinctUntilChanged()

isValid
    .bind(to: loginButton.rx.isEnabled)
    .disposed(by: disposeBag)

// 버튼 탭 — withLatestFrom으로 탭 순간 값만 가져가기
loginButton.rx.tap
    .withLatestFrom(Observable.combineLatest(usernameStream, passwordStream))
    .flatMapLatest { username, password in
        viewModel.login(username: username, password: password)
    }
    .subscribe(
        onNext:  { print("로그인 성공:", $0) },
        onError: { print("실패:", $0) }
    )
    .disposed(by: disposeBag)
```

combineLatest로 버튼 활성화를, withLatestFrom으로 탭 순간의 값 추출을 담당한다. 두 Operator의 역할이 분리되어 있다.

## 정리

| Operator | 동작 | 적합한 상황 |
| --- | --- | --- |
| `merge` | 도착 순서대로 합침 | 같은 타입의 여러 소스 |
| `combineLatest` | 최신 값끼리 결합 | 폼 유효성, 복합 상태 |
| `zip` | 쌍으로 결합 | 두 요청의 1:1 대응 |
| `withLatestFrom` | 트리거 시 상대방 최신값 | 버튼 탭 + 입력값 |
| `concat` | 완료 후 다음으로 | 캐시 → 네트워크 |
| `startWith` | 초깃값 삽입 | 초기 상태 보장 |

다음에는 외부에서 이벤트를 주입할 수 있는 [Subject]({{ "/swift/rxswift/subject/" | relative_url }})를 살펴본다.

## 참고

- [ReactiveX: Combining Operators](https://reactivex.io/documentation/operators.html#combining)
- [RxMarbles: combineLatest](https://rxmarbles.com/#combineLatest)
