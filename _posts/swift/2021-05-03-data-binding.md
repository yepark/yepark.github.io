---
layout: single
title: "[Swift] 클로저 기반 데이터 바인딩과 Box"
date: 2021-05-03
last_modified_at: 2026-11-01
comments: true
categories:
  - Swift
tags: [Swift, Data-Binding, MVVM, Observation]
toc: true
toc_sticky: true
toc_label: "목차"
---

데이터 바인딩은 상태가 바뀌었을 때 그 변화를 UI 같은 소비자에게 전달하는 연결 방식이다. UIKit에서는 delegate, KVO, NotificationCenter, Combine, 클로저 등 여러 선택지가 있다. 작은 MVVM 예제에서는 `Box`라는 단순한 래퍼로 동작 원리를 이해할 수 있다.

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
