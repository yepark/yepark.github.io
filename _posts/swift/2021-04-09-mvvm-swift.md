---
layout: single
title: "[Swift] MVVM의 역할과 데이터 흐름"
date: 2021-04-09
last_modified_at: 2026-11-01
comments: true
categories:
  - Swift
tags: [Swift, iOS, MVVM, Architecture]
toc: true
toc_sticky: true
toc_label: "목차"
---

MVVM(Model–View–ViewModel)은 화면 표시와 비즈니스 로직을 분리하는 설계 방식이다. 중요한 점은 세 글자의 순서가 호출 순서를 뜻하지 않는다는 것이다. `Model → View → ViewModel`처럼 한 방향으로만 흐르는 구조가 아니라, 각 구성 요소의 책임과 의존 관계를 정리하는 패턴에 가깝다.

## 각 구성 요소의 역할

- **Model**: 앱의 데이터와 비즈니스 규칙을 표현한다. 네트워크·데이터베이스 같은 서비스 계층을 포함하거나 별도로 둘 수 있다.
- **View**: 사용자에게 상태를 보여 주고 입력을 받는다. UIKit에서는 주로 `UIView`와 `UIViewController`, SwiftUI에서는 `View`가 이 역할을 맡는다.
- **ViewModel**: Model의 데이터를 화면에 맞는 형태로 가공하고, 사용자의 동작을 처리할 명령이나 메서드를 제공한다.

ViewModel은 구체적인 버튼이나 레이블을 직접 조작하지 않는 편이 좋다. 대신 View가 표시할 상태를 노출하고, View는 그 상태를 관찰해 UI를 갱신한다. 이렇게 하면 ViewModel을 UI 없이 테스트하기 쉬워진다.

## 간단한 예제

```swift
struct User {
    let name: String
    let isPremium: Bool
}

final class ProfileViewModel {
    private let user: User

    init(user: User) {
        self.user = user
    }

    var displayName: String {
        user.isPremium ? "⭐️ \(user.name)" : user.name
    }
}
```

`User`는 화면 표현을 알지 못하고, `ProfileViewModel`이 이름을 표시할 형태로 변환한다. View는 `displayName`만 사용하므로 표시 규칙이 화면 코드 곳곳에 흩어지지 않는다.

## 데이터는 어떻게 연결할까

MVVM 자체는 바인딩 기술을 정하지 않는다. UIKit에서는 클로저, delegate, KVO, Combine 등을 선택할 수 있고, SwiftUI에서는 Observation이나 상태 프로퍼티를 사용할 수 있다. 즉 MVVM과 데이터 바인딩은 같은 개념이 아니다. MVVM은 책임을 나누는 구조이고, 바인딩은 상태 변화를 전달하는 구현 방법이다.

## 화면 상태를 하나의 타입으로 모델링하기

`isLoading`, `errorMessage`, `items`를 서로 독립된 프로퍼티로 두면 모순된 상태가 만들어질 수 있다. 예를 들어 로딩 중인데 오류 메시지와 목록이 동시에 표시될 수 있다. 가능한 화면 상태를 `enum`으로 제한하면 View가 처리해야 할 경우가 명확해진다.

```swift
enum ProfileState {
    case idle
    case loading
    case loaded(name: String)
    case failed(message: String)
}

@MainActor
final class ProfileViewModel {
    private(set) var state: ProfileState = .idle

    func load() async {
        state = .loading

        do {
            let user = try await fetchUser()
            state = .loaded(name: user.name)
        } catch {
            state = .failed(message: "프로필을 불러오지 못했습니다.")
        }
    }
}
```

View는 상태에 따라 로딩 표시, 콘텐츠, 오류 화면 중 하나를 렌더링한다. `@MainActor`는 UI가 관찰하는 상태 변경이 메인 액터에서 일어나도록 경계를 명시한다.

## ViewModel 테스트하기

ViewModel의 장점은 화면 없이 입력과 출력을 검증할 수 있다는 점이다. 네트워크 서비스를 프로토콜로 추상화하고 테스트용 구현을 주입하면 성공과 실패를 빠르게 재현할 수 있다.

```swift
func testPremiumUserHasStarPrefix() {
    let user = User(name: "yep", isPremium: true)
    let viewModel = ProfileViewModel(user: user)

    XCTAssertEqual(viewModel.displayName, "⭐️ yep")
}
```

테스트가 어렵다면 ViewModel이 현재 시간, 전역 싱글턴, 네트워크 같은 외부 환경에 직접 의존하고 있지 않은지 먼저 확인한다.

## 주의할 점

화면의 모든 코드를 ViewModel로 옮기면 오히려 거대한 ViewModel이 생긴다. 다음 기준이 실용적이다.

- 색상·오토 레이아웃처럼 순수한 화면 표현은 View에 둔다.
- 검증, 형식 변환, 화면 상태 결정은 ViewModel이 담당한다.
- 저장·통신은 별도 서비스나 저장소에 위임한다.
- 화면 이동은 작은 앱에서는 View Controller가, 복잡한 앱에서는 Coordinator가 맡을 수 있다.

MVVM은 Apple이 강제하는 단일 정답이 아니다. 앱의 규모와 테스트 요구에 맞춰 경계를 정하고, 의존 방향을 단순하게 유지하는 것이 핵심이다.

## 참고

- [Apple Observation](https://developer.apple.com/documentation/observation)
