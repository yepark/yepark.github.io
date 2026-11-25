---
title: "Operator — 변환"
description: "RxSwift의 map, flatMap, compactMap, filter, take, skip으로 Observable 흐름을 변환하고 가공하는 방법을 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 2
permalink: /swift/rxswift/operators-transform/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [Swift, RxSwift, Operator, map, flatMap, filter]
---

# Operator — 변환
{: .no_toc }

{% include article-toc.md %}

Operator는 Observable이 내보내는 이벤트를 가공하는 함수다. 여러 Operator를 체인으로 연결해 데이터 변환 파이프라인을 선언적으로 표현할 수 있다. 이 글에서는 가장 자주 쓰이는 변환·필터링 Operator를 다룬다.

## map

Swift의 `Array.map`과 같다. 각 `next` 이벤트의 값을 변환한다.

```swift
Observable.of(1, 2, 3)
    .map { $0 * 10 }
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)

// 10
// 20
// 30
```

UI 작업에서 자주 쓰이는 패턴 — 모델을 뷰 텍스트로 변환:

```swift
viewModel.user       // Observable<User>
    .map { $0.name } // Observable<String>
    .bind(to: nameLabel.rx.text)
    .disposed(by: disposeBag)
```

## compactMap

nil을 걸러내는 map이다. `Optional` 값의 흐름에서 nil을 제거하고 언래핑된 값만 내보낸다.

```swift
Observable.of("1", "two", "3", "four", "5")
    .compactMap { Int($0) }   // 변환 실패(nil)는 제거
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)

// 1
// 3
// 5
```

## filter

조건을 만족하는 이벤트만 통과시킨다.

```swift
Observable.of(1, 2, 3, 4, 5, 6)
    .filter { $0 % 2 == 0 }
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)

// 2
// 4
// 6
```

## flatMap

각 이벤트를 새로운 Observable로 변환하고, 그 결과를 하나의 흐름으로 합친다. 비동기 연쇄 작업에 가장 많이 쓰인다.

```swift
struct User {
    let id: Int
    let name: String
}

func fetchPosts(userId: Int) -> Observable<String> {
    return Observable.of("Post A", "Post B")  // 실제로는 네트워크 요청
}

Observable.of(User(id: 1, name: "yep"), User(id: 2, name: "bob"))
    .flatMap { user in fetchPosts(userId: user.id) }
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)

// Post A
// Post B
// Post A
// Post B
```

**map vs flatMap:**

```text
map:     Observable<User>  → 변환 → Observable<Observable<[Post]>>
flatMap: Observable<User>  → 변환 → Observable<[Post]>  (평탄화)
```

flatMap은 내부 Observable이 완료되기 전에 새 이벤트가 오면 이전 내부 Observable도 살려 둔다. 버튼을 연속으로 탭할 때 이전 요청이 완료되기 전에 새 요청이 시작된다.

## flatMapLatest

가장 최근 이벤트로 만든 내부 Observable만 유지한다. 이전 내부 Observable은 자동으로 dispose된다.

```swift
// 검색창 — 입력할 때마다 이전 검색 취소 후 새 검색
searchField.rx.text.orEmpty
    .flatMapLatest { query in search(query: query) }
    .bind(to: resultsTableView.rx.items(...))
    .disposed(by: disposeBag)
```

사용자가 "swift"를 타이핑할 때 "s", "sw", "swi"... 각 단계의 검색 요청 중 마지막 것만 살아남는다.

| Operator | 이전 내부 Observable | 주요 용도 |
| --- | --- | --- |
| `flatMap` | 유지 | 순서 무관한 병렬 요청 |
| `flatMapLatest` | 취소 | 검색, 자동완성 |
| `flatMapFirst` | 무시 | 버튼 탭 중복 방지 |
| `concatMap` | 완료 대기 | 순서 보장 직렬 요청 |

## take / skip

앞에서 n개만 받거나, n개를 건너뛴다.

```swift
Observable.of(1, 2, 3, 4, 5)
    .take(3)
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
// 1, 2, 3

Observable.of(1, 2, 3, 4, 5)
    .skip(2)
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
// 3, 4, 5
```

`take(until:)`을 쓰면 특정 Observable이 이벤트를 내보낼 때까지만 받는다. 뷰가 사라질 때 자동으로 구독을 끊는 패턴에 활용된다.

```swift
Observable<Int>.interval(.seconds(1), scheduler: MainScheduler.instance)
    .take(until: self.rx.deallocated)  // VC가 해제될 때 종료
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
```

## distinctUntilChanged

연속으로 같은 값이 오면 중복을 제거한다. UI 업데이트 최적화에 유용하다.

```swift
Observable.of(1, 1, 2, 2, 3, 1)
    .distinctUntilChanged()
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
// 1, 2, 3, 1
```

## debounce / throttle

빠르게 연속으로 오는 이벤트를 제어한다.

```swift
// debounce: 마지막 이벤트 후 0.3초가 지나면 한 번만 내보낸다 (검색 최적화)
searchField.rx.text.orEmpty
    .debounce(.milliseconds(300), scheduler: MainScheduler.instance)
    .flatMapLatest { search(query: $0) }
    .bind(to: results)
    .disposed(by: disposeBag)

// throttle: 일정 간격으로 첫 이벤트만 내보낸다 (버튼 중복 탭 방지)
button.rx.tap
    .throttle(.seconds(1), scheduler: MainScheduler.instance)
    .subscribe(onNext: { print("탭") })
    .disposed(by: disposeBag)
```

## 실습: 검색 필터 파이프라인

```swift
let items = ["Swift", "SwiftUI", "RxSwift", "Combine", "Objective-C"]

searchField.rx.text.orEmpty          // Observable<String>
    .debounce(.milliseconds(300), scheduler: MainScheduler.instance)
    .distinctUntilChanged()           // 같은 쿼리 중복 제거
    .map { query in                   // 필터링
        query.isEmpty
            ? items
            : items.filter { $0.localizedCaseInsensitiveContains(query) }
    }
    .bind(to: tableView.rx.items(cellIdentifier: "Cell")) { _, item, cell in
        cell.textLabel?.text = item
    }
    .disposed(by: disposeBag)
```

debounce로 타이핑 중 과도한 필터링을 막고, distinctUntilChanged로 같은 쿼리 재실행을 방지하고, map으로 결과를 변환한다. 세 Operator의 조합이 선언적으로 의도를 드러낸다.

## 정리

| Operator | 역할 |
| --- | --- |
| `map` | 값 변환 |
| `compactMap` | nil 제거 + 변환 |
| `filter` | 조건으로 걸러내기 |
| `flatMap` | 비동기 연쇄, 병렬 |
| `flatMapLatest` | 최신 요청만 유지 |
| `take` / `skip` | 개수 제한 |
| `distinctUntilChanged` | 중복 연속값 제거 |
| `debounce` / `throttle` | 이벤트 속도 제어 |

다음에는 여러 Observable을 하나로 합치는 [Operator — 결합]({{ "/swift/rxswift/operators-combine/" | relative_url }})을 살펴본다.

## 참고

- [RxSwift: Transforming Operators](https://reactivex.io/documentation/operators.html#transforming)
- [RxMarbles: 연산자 시각화](https://rxmarbles.com/)
