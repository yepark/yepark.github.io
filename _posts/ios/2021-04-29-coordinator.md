---
layout: single
title: "[iOS] Coordinator 패턴으로 화면 전환 분리하기"
date: 2021-04-29
last_modified_at: 2026-11-01
comments: true
categories:
  - ios
tags: [iOS, Swift, UIKit, Coordinator, Architecture]
toc: true
toc_sticky: true
toc_label: "목차"
---

UIKit 앱에서 View Controller가 다음 화면 생성, 데이터 전달, `push`와 `present`까지 모두 맡기 시작하면 화면 전환 코드가 빠르게 복잡해진다. Coordinator 패턴은 이 이동 흐름을 별도 객체로 분리한다.

Coordinator는 Apple 프레임워크가 제공하는 정식 타입이 아니라 애플리케이션 설계 패턴이다. 따라서 프로젝트마다 구현이 다를 수 있으며, 모든 앱에 무거운 계층 구조가 필요한 것은 아니다.

## 가장 작은 Coordinator

```swift
protocol Coordinator: AnyObject {
    var navigationController: UINavigationController { get }
    func start()
}

final class AppCoordinator: Coordinator {
    let navigationController: UINavigationController

    init(navigationController: UINavigationController) {
        self.navigationController = navigationController
    }

    func start() {
        let viewController = HomeViewController()
        viewController.onShowDetail = { [weak self] itemID in
            self?.showDetail(itemID: itemID)
        }
        navigationController.setViewControllers(
            [viewController],
            animated: false
        )
    }

    private func showDetail(itemID: String) {
        let viewController = DetailViewController(itemID: itemID)
        navigationController.pushViewController(
            viewController,
            animated: true
        )
    }
}
```

View Controller는 “상세 화면을 보여 달라”는 사용자 의도만 클로저로 전달한다. 구체적으로 어떤 화면을 만들고 어떻게 이동할지는 Coordinator가 결정한다.

## 장점

- 화면이 다른 View Controller의 생성 방법을 알 필요가 없다.
- 로그인 여부나 딥 링크에 따라 흐름을 바꾸기 쉽다.
- 화면 전환 규칙을 한곳에서 읽고 테스트할 수 있다.
- 같은 화면을 여러 흐름에서 재사용하기 쉬워진다.

## 주의할 점

자식 Coordinator를 배열에 보관하는 구조에서는 흐름이 끝날 때 반드시 제거해야 한다. 그렇지 않으면 부모와 자식, 클로저 사이에 순환 참조가 생길 수 있다. View Controller가 Coordinator를 강하게 소유하게 만들기보다 약한 delegate나 `[weak self]` 클로저를 사용하는 편이 안전하다.

또한 화면이 두세 개뿐인 앱에 Coordinator 계층을 과하게 만들면 추적할 파일만 늘어난다. 다음 조건에서 도입 효과가 크다.

- 인증, 온보딩, 결제처럼 독립된 화면 흐름이 있다.
- 딥 링크나 푸시 알림이 여러 진입점을 만든다.
- 하나의 View Controller가 여러 다음 화면을 직접 생성한다.

`UINavigationController`는 화면 스택을 관리하고, Coordinator는 앱의 이동 규칙을 관리한다. 두 역할을 구분하면 구현을 단순하게 유지할 수 있다.

## 참고

- [Apple UINavigationController](https://developer.apple.com/documentation/uikit/uinavigationcontroller)
- [Soroush Khanlou: Coordinators Redux](https://khanlou.com/2015/10/coordinators-redux/)
