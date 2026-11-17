---
title: "클로저 기반 데이터 바인딩과 Box"
parent: "Swift"
nav_order: 6
permalink: /swift/data-binding/
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
date: 2021-05-03
description: "클로저 기반 Box의 상태 전달, 구독 해제, 참조 수명과 UI 실행 문맥을 구현 예제로 분석합니다."
first_written: 2021-05-03
last_modified_date: 2026-11-17
tags: [Swift, Data-Binding, MVVM, Observation]
---

# 클로저 기반 데이터 바인딩과 Box
{: .no_toc }

{% include article-toc.md %}

데이터 바인딩은 상태가 바뀌었을 때 그 변화를 UI 같은 소비자에게 전달하는 연결 방식이다. UIKit에서는 delegate, KVO, NotificationCenter, Combine, 클로저 등 여러 선택지가 있다. 작은 MVVM 예제에서는 `Box`라는 단순한 래퍼로 동작 원리를 이해할 수 있다.

## 값과 화면을 연결하는 이유

서버에서 사용자 이름을 받아도 화면의 레이블이 저절로 바뀌지는 않는다. 값이 바뀌었다는 사실을 화면에 알리고, 화면이 새 값을 표시하는 연결이 필요하다.

아래 `Box`는 값을 담는 상자이며 `listener`는 변경을 전달받는 함수다. `bind`는 함수를 등록하고, `value` 변경은 등록한 함수를 호출한다. 처음에는 ‘등록 → 값 변경 → 호출 → 화면 반영’ 순서만 따라가면 된다.

## 기본 Box 구현

```swift
final class Box<Value> {
    typealias Listener = (Value) -> Void

    private var listener: Listener?

    var value: Value {
        didSet {
            listener?(value)
        }
    }

    init(_ value: Value) {
        self.value = value
    }

    func bind(_ listener: Listener?) {
        self.listener = listener
        listener?(value)
    }
}
```

`value`가 바뀌면 `didSet`이 listener를 호출한다. `bind` 직후 현재 값도 한 번 전달하므로 View는 초기 상태와 이후 변경을 같은 경로로 받을 수 있다.

UIKit 화면을 만들기 전에 콘솔에서 연결을 확인할 수 있다.

```swift
let name = Box("불러오는 중…")
name.bind { value in
    print("화면에 표시할 값:", value)
}
name.value = "yep"
```

등록 직후에는 `불러오는 중…`, 값을 바꾼 뒤에는 `yep`이 출력된다. 함수가 두 번 실행되는 이유는 `bind`의 초기 전달과 `didSet`의 변경 전달이 각각 한 번씩 있기 때문이다.

```swift
final class ProfileViewModel {
    let name = Box("불러오는 중…")

    func update(name: String) {
        self.name.value = name
    }
}

final class ProfileViewController: UIViewController {
    private let viewModel = ProfileViewModel()

    override func viewDidLoad() {
        super.viewDidLoad()

        viewModel.name.bind { [weak self] name in
            self?.title = name
        }
    }
}
```

## 단순한 Box의 한계

이 구현은 listener를 하나만 저장한다. 새 listener를 연결하면 기존 listener가 사라지고, 구독 취소나 오류·완료 개념도 없다. 어느 스레드에서 값이 바뀌든 그 스레드에서 UI 클로저가 실행되므로 메인 스레드 보장도 직접 해야 한다.

또한 `Box`가 listener를 강하게 보관하므로 View Controller를 캡처할 때 `[weak self]`를 빠뜨리면 순환 참조가 생길 수 있다. 값 변경이 동시에 일어날 수 있는 코드에서는 동기화도 필요하다.

## 구독 해제를 지원하는 형태

화면이 사라진 뒤에도 listener가 남지 않도록 바인딩 결과로 취소 토큰을 반환할 수 있다. 여러 구독자를 지원한다면 각 listener에 식별자를 부여하고 토큰이 해제될 때 제거한다.

```swift
final class ObservationToken {
    private var cancellation: (() -> Void)?

    init(_ cancellation: @escaping () -> Void) {
        self.cancellation = cancellation
    }

    func cancel() {
        cancellation?()
        cancellation = nil
    }

    deinit {
        cancel()
    }
}
```

View Controller가 토큰을 프로퍼티로 보관하면 화면의 수명과 구독 수명이 자연스럽게 맞춰진다. 실제 구현에서는 listener 컬렉션 변경과 값 전달이 동시에 일어날 수 있으므로 직렬 실행 컨텍스트나 actor 같은 동기화 전략도 필요하다.

위 `ObservationToken`만 추가한다고 앞의 `Box`에 구독 해제가 연결되지는 않는다. 여러 listener를 ID별로 저장하는 Box를 별도로 만들고, 토큰의 취소 클로저가 해당 ID를 제거하도록 연결해야 한다. 이 절은 토큰의 수명 관리 원리를 설명하는 조각이다.

## UI 갱신과 실행 컨텍스트

네트워크 콜백에서 `value`를 변경하면 listener도 백그라운드 스레드에서 호출될 수 있다. UIKit UI 갱신은 메인 스레드에서 해야 하므로 ViewModel 전체를 `@MainActor`로 격리하거나 전달 시점을 명시적으로 전환한다.

```swift
Task { @MainActor in
    viewModel.name.value = response.name
}
```

Box 내부가 무조건 메인 스레드로 전환하도록 만들 수도 있지만, 그러면 범용 값 래퍼가 UI 정책까지 갖게 된다. UI 전용 바인딩인지 범용 관찰 도구인지 먼저 정한 뒤 실행 규칙을 문서화하는 편이 좋다.

## 언제 사용할까

한 화면과 하나의 상태를 잇는 작은 UIKit 코드나 바인딩의 원리를 학습할 때는 충분하다. 다음 요구가 생기면 더 구조화된 도구를 고려한다.

- 여러 구독자와 구독 해제가 필요하다.
- 비동기 스트림을 조합하거나 오류를 전달해야 한다.
- SwiftUI 상태와 자동으로 연결해야 한다.
- 동시성과 실행 스레드를 명확히 제어해야 한다.

현재 Swift에서는 Observation의 `@Observable`, SwiftUI의 상태 도구, Combine 같은 선택지가 있다. 이들은 단순한 `Box`보다 많은 수명 주기와 관찰 기능을 제공한다. 반대로 UIKit의 작은 레거시 화면에 전체 반응형 프레임워크를 넣는 것이 항상 정답은 아니다. 요구 사항에 맞는 가장 단순한 수단을 선택하면 된다.

## MVVM과의 관계

데이터 바인딩은 MVVM의 필수 구현체가 아니다. ViewModel이 콜백, delegate 또는 명시적 메서드로 View에 상태를 전달해도 MVVM을 구성할 수 있다. 핵심은 ViewModel이 구체적인 UI 객체를 직접 조작하지 않고, View가 사용할 상태와 동작을 제공하는 것이다.

## 참고

- [Apple Observation](https://developer.apple.com/documentation/observation)
