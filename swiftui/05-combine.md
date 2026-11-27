---
title: "Combine과 SwiftUI"
description: "Publisher, 연산자, 구독의 역할과 @Published·objectWillChange의 차이, 검색 흐름에서 자주 쓰는 Combine 연산자를 설명합니다."
parent: SwiftUI
nav_order: 5
permalink: /swiftui/combine/
date: 2026-11-26
first_written: 2026-11-26
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [SwiftUI, iOS, Combine]
---

# Combine과 SwiftUI
{: .no_toc }

{% include article-toc.md %}

**Combine**은 Apple이 iOS 13과 함께 내놓은 프레임워크로, 검색어 입력이나 네트워크 응답처럼 시간에 따라 들어오는 값을 Publisher(값을 내보내는 쪽)와 연산자로 처리한다. RxSwift와 개념이 거의 같다. 이 글에서는 Combine의 기본 구성과 SwiftUI의 `ObservableObject`가 Combine과 어떻게 이어지는지 확인한다. 다음 글에서 이것으로 검색 화면을 만든다.

## Combine과 SwiftUI를 연결하기 {#combine}

SwiftUI는 `body`로 화면을 설명하고, **Combine**은 시간에 따라 들어오는 값을 처리한다. 검색어, 위치 업데이트, 네트워크 응답을 하나씩 받아 걸러내거나 합칠 때 Combine을 쓸 수 있다. `ObservableObject`에서 SwiftUI가 사용하는 변경 알림도 Combine Publisher다. Combine으로 검색 입력과 응답을 처리하고 SwiftUI로 결과를 화면에 표시하는 식으로 두 역할을 나눌 수 있다.

### Publisher, 연산자, 구독의 역할 {#combine-publisher-subscription}

| 이름 | 맡는 일 | 검색에서 하는 일 |
| --- | --- | --- |
| `Publisher` | `Output` 값을 보내고 종료 시 완료나 `Failure`를 전달한다 | 새 검색어 또는 서버 응답을 보낸다 |
| 연산자(operator) | Publisher를 받아 다른 Publisher로 변환한다 | 공백을 빼거나 검색 요청으로 바꾼다 |
| `Subscriber` | 구독을 통해 값을 받는다 | 결과를 모델 상태에 쓴다 |
| `AnyCancellable` | `sink` 등이 반환하는 구독 취소 핸들 | 모델의 수명 동안 구독을 보관한다 |

`Failure`가 `Never`인 Publisher는 실패로 끝나지 않는다. `sink`는 결과를 클로저에서 받는 방법이다. 실패할 수 있는 Publisher를 구독할 때는 종료를 받는 `receiveCompletion`에서도 정상 완료와 오류를 구분할 수 있다. 구독 핸들을 보관하지 않고 마지막 참조가 해제되면 `AnyCancellable`이 취소를 호출한다. 소스가 실제 작업까지 취소하는지는 해당 Publisher의 구현에 달려 있다. [Apple · Combine](https://developer.apple.com/documentation/combine)

### @Published의 값과 objectWillChange의 차이 {#combine-published}

`ObservableObject`의 `objectWillChange`는 객체가 곧 바뀐다는 알림이다. `@Published var query`의 `$query`는 해당 속성의 값을 전달한다. 아래 명령줄 예제에서는 같은 변경을 두 경로로 관찰한다. 공백만 다른 입력은 `map`으로 정리한 뒤 `removeDuplicates()`로 걸러 낸다.

```swift
import Combine
import Foundation

final class Draft: ObservableObject {
    @Published var query = ""
}

let draft = Draft()
var cancellables = Set<AnyCancellable>()

draft.objectWillChange
    .sink { print("objectWillChange: \(draft.query.debugDescription)") }
    .store(in: &cancellables)

let values = draft.$query
    .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
    .removeDuplicates()
    .sink { value in
        print("구독 값: \(value.debugDescription), 저장값: \(draft.query.debugDescription)")
    }

draft.query = "s"
draft.query = "s "
cancellables.removeAll()
values.cancel()
draft.query = "swift"
print("취소 뒤 저장값: \(draft.query.debugDescription)")
```

`swift PublishedProbe.swift`를 macOS에서 실행했다.

```text
구독 값: "", 저장값: ""
objectWillChange: ""
구독 값: "s", 저장값: ""
objectWillChange: "s"
취소 뒤 저장값: "swift"
```

1. `$query`를 구독하자 초기 값 `""`이 즉시 왔다.
2. `"s"`를 대입하자 `sink`의 인자는 새 값 `"s"`, 그 순간 다시 읽은 `draft.query`는 기존 값 `""`였다. `@Published`는 속성의 새 값을 **쓰기 직전**에 발행한다.
3. `"s "`도 객체 변경 알림을 냈다. 값 구독 쪽에서는 공백 제거 결과가 직전과 같은 `"s"`라 값이 걸러졌다.
4. 두 구독을 취소한 후에는 `query`를 바꿔도 구독 로그는 더 나오지 않았다.

필터링이나 요청에는 `sink`에 전달된 인자를 사용한다. 그 자리에서 모델 값을 다시 읽으면 이전 값일 수 있다. `@Published`에는 값 전달이, `objectWillChange`에는 관찰 중인 객체를 다시 볼 시점이 담긴다. [Apple · Published](https://developer.apple.com/documentation/combine/published) · [Apple · ObservableObject](https://developer.apple.com/documentation/combine/observableobject)

### 검색 흐름에서 자주 쓰는 연산자 {#combine-operators}

| 연산자 | 언제 쓰나 |
| --- | --- |
| `map` | 문자열을 정리하거나 응답을 화면 상태로 바꿀 때 |
| `removeDuplicates` | 바로 앞 입력과 같은 값을 한 번 더 처리할 필요가 없을 때 |
| `debounce` | 타이핑이 설정한 시간 동안 멈춘 뒤 마지막 입력만 전달할 때 |
| `combineLatest` | 검색어와 필터처럼 두 입력의 최신 값을 짝으로 처리할 때 |
| `switchToLatest` | 바깥 Publisher가 새 내부 Publisher를 보내면 이전 내부 구독을 취소하고 최신 것만 받을 때 |
| `catch` | 실패한 요청을 대체 Publisher로 바꿀 때 |
| `receive(on:)` | 지정한 실행 큐로 다음 단계의 이벤트 전달을 옮길 때 |

`subscribe(on:)`은 원본 구독과 요청, 취소를 수행할 실행 맥락에 영향을 준다. 뒤쪽 클로저가 값을 어디서 받게 할지는 `receive(on:)`이 맡는다. `@MainActor`는 컴파일러가 상태 접근을 검사하는 경계다. Combine 스케줄러는 이벤트가 실제로 전달되는 위치를 정한다. Swift 6에서는 모델에 격리된 클로저를 백그라운드에서 호출하지 않도록, 그런 클로저 **앞**에 큐 전환을 둔다. [WWDC19 · Combine in Practice](https://developer.apple.com/videos/play/wwdc2019/721/)

## 주요 API

| API | 역할 |
| --- | --- |
| `Publisher` / `Subscriber` | 값을 보내는 쪽과 받는 쪽 |
| `@Published` | 프로퍼티 값 변경을 Publisher로 보낸다. `$name`으로 Publisher에 접근 |
| `objectWillChange` | `ObservableObject`가 값이 바뀌기 직전 보내는 알림 |
| `sink(receiveCompletion:receiveValue:)` | 값과 완료를 클로저로 받는 구독 |
| `assign(to:)` | 받은 값을 `@Published` 프로퍼티에 넣는다 |
| `AnyCancellable` / `store(in:)` | 구독 핸들. 해제되면 구독이 취소된다 |
| `map`, `filter`, `removeDuplicates` | 값 변환, 걸러내기, 연속 중복 제거 |
| `debounce(for:scheduler:)` | 입력이 멈춘 뒤 마지막 값만 보낸다 |
| `flatMap` / `map` + `switchToLatest()` | 값을 새 Publisher(요청)로 바꾸고, 최신 요청만 남긴다 |
| `catch`, `replaceError(with:)` | 오류를 다른 Publisher나 값으로 바꾼다 |
| `receive(on:)` | 이후 값을 전달할 스케줄러(예: `DispatchQueue.main`) |
| `PassthroughSubject` / `CurrentValueSubject` | 직접 값을 넣는 Publisher. 후자는 현재 값을 가진다 |
| `URLSession.dataTaskPublisher(for:)` | 네트워크 요청 Publisher |

## 이어서 읽기

- 이전 글: [뷰의 정체성과 목록·화면 이동]({{ '/swiftui/identity-navigation/' | relative_url }})
- 다음 글: [Combine 실습: 검색 화면]({{ '/swiftui/combine-search/' | relative_url }})
- [SwiftUI 연재 목차]({{ '/swiftui/' | relative_url }})
