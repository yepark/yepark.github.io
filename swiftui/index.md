---
title: "SwiftUI"
description: "선언형 UI가 화면을 갱신하는 순서, 레이아웃, State·Binding·Observation의 소유권, 뷰 정체성, Combine 검색 실습, UIKit 연동까지 SwiftUI를 차례로 다루는 연재입니다."
nav_order: 5
has_children: true
has_toc: false
permalink: /swiftui/
redirect_from:
  - /ios/swiftui/
last_modified_date: 2026-11-27
---

# SwiftUI

**SwiftUI**는 화면을 "어떻게 그릴지"를 명령하는 대신 "지금 상태에서 화면이 어떤 모습이어야 하는지"를 선언하는 Apple의 UI 프레임워크다. 상태가 바뀌면 SwiftUI가 화면 설명(`body`)을 다시 읽어 필요한 부분만 갱신한다. **Combine**은 입력, 네트워크 응답, 타이머처럼 시간에 따라 들어오는 값을 Publisher와 연산자로 처리하는 Apple의 프레임워크로, SwiftUI 화면 상태와 자주 함께 쓰인다.

이 연재는 선언형 UI의 갱신 순서에서 출발해 레이아웃, 상태 소유권, 뷰 정체성을 거쳐 Combine으로 검색 화면을 만들고, 마지막으로 UIKit과 섞어 쓰는 방법까지 다룬다. 앞에서부터 차례로 읽는 것을 권하지만, 필요한 주제부터 골라 읽어도 된다.

{% include series-list.html heading="연재 목차" %}

## 정리
{: id="정리" }

| 개념 | 한 줄 요약 |
| --- | --- |
| 선언형 UI | 상태만 바꾸면 SwiftUI가 `body`를 다시 읽어 화면을 맞춘다 |
| View | 현재 상태에서 `body`가 뷰 구조를 설명한다 |
| ViewBuilder | 여러 뷰와 분기를 하나의 화면 구조로 모은다 |
| 수정자 | 뷰를 한 겹씩 감싼다. 순서가 결과를 바꾼다 |
| 레이아웃 | `VStack`/`HStack`/`ZStack`으로 쌓고 `Spacer`로 민다 |
| `@State` | 뷰가 가진 값. `private`, 저장은 SwiftUI가 한다 |
| `@Binding` | 남의 값을 빌려 읽고 고친다 (`$` 붙여 넘김) |
| `@Observable` | iOS 17. `body`에서 실제로 읽은 모델 속성을 관찰한다 |
| `ObservableObject` | SwiftUI가 객체 단위의 `objectWillChange` 알림을 관찰한다 |
| Combine | Publisher와 연산자로 입력, 요청, 응답처럼 시간에 따라 들어오는 값을 처리한다 |
| `@Bindable` / `@Environment` | iOS 17. 모델 바인딩 / 멀리 있는 뷰에 전달 |
| 정체성 | `.id`나 `if` 분기가 바뀌면 `@State`가 초기화된다 |
| UIKit 연동 | `UIHostingController`, `UIViewRepresentable` |

## 실행 환경과 확인 범위
{: id="실행-환경과-확인-범위" }

- macOS 15.6, Apple M4, Xcode 16.2, Swift 6.0.3, macOS 15.2 SDK
- SwiftPM 실행 파일(배포 대상 macOS 14)에서 `NSHostingView`를 창에 띄우고 값을 바꿔 `body` 출력을 기록했다.
- 그림은 `ImageRenderer`(iOS 16, macOS 13)로 macOS에서 그렸다. 같은 코드를 iOS에서 그려 보지는 않았다.
- iOS 코드와 설정·검색 화면은 iOS 18.2 시뮬레이터 SDK로 컴파일을 확인했다. 설정 화면과 검색 화면은 iOS 16 배포 대상으로 검사했다. 화면에서 사용자 입력을 직접 재생하지는 않았다.
- `@Published` 출력과 검색 모델의 취소·오류·복구는 macOS 명령줄에서 실행했다.

## 이어서 읽기
{: id="이어서-읽기" }

- [MVVM의 역할과 데이터 흐름]({{ '/swift/mvvm-swift/' | relative_url }}): SwiftUI에서 `@Observable` 모델을 ViewModel처럼 나눌 때 기준이 된다.
- [클로저 기반 데이터 바인딩과 Box]({{ '/swift/data-binding/' | relative_url }}): 바인딩을 직접 만들어 보면 SwiftUI가 대신해 주는 일이 보인다.
- [RxSwift 연재]({{ '/swift/rxswift/' | relative_url }}): Swift에서 값을 구독하고 가공하는 흐름을 다른 라이브러리 예제로 따라간다.
- [Auto Layout]({{ '/ios/auto-layout/' | relative_url }}): UIKit 레이아웃과 SwiftUI 스택 방식을 비교해 볼 수 있다.

## 참고
{: id="참고" }

- [Apple: SwiftUI](https://developer.apple.com/documentation/swiftui)
- [Apple: View](https://developer.apple.com/documentation/swiftui/view)
- [Apple: Configuring views](https://developer.apple.com/documentation/swiftui/configuring-views)
- [Apple: State](https://developer.apple.com/documentation/swiftui/state)
- [Apple: Binding](https://developer.apple.com/documentation/swiftui/binding)
- [Apple: Migrating from the Observable Object protocol to the Observable macro](https://developer.apple.com/documentation/swiftui/migrating-from-the-observable-object-protocol-to-the-observable-macro)
- [Apple: Bindable](https://developer.apple.com/documentation/swiftui/bindable)
- [Apple: Environment](https://developer.apple.com/documentation/swiftui/environment)
- [Apple: StateObject](https://developer.apple.com/documentation/swiftui/stateobject)
- [Apple: ForEach](https://developer.apple.com/documentation/swiftui/foreach)
- [Apple: NavigationStack](https://developer.apple.com/documentation/swiftui/navigationstack)
- [Apple: id(_:)](https://developer.apple.com/documentation/swiftui/view/id(_:))
- [Apple: UIHostingController](https://developer.apple.com/documentation/swiftui/uihostingcontroller)
- [Apple: UIViewRepresentable](https://developer.apple.com/documentation/swiftui/uiviewrepresentable)
- [Apple: Previews in Xcode](https://developer.apple.com/documentation/swiftui/previews-in-xcode)
- [Apple: ImageRenderer](https://developer.apple.com/documentation/swiftui/imagerenderer)
- [WWDC21: Demystify SwiftUI](https://developer.apple.com/videos/play/wwdc2021/10022/)
- [Apple · ViewBuilder](https://developer.apple.com/documentation/swiftui/viewbuilder)
- [Apple · Laying out a simple view](https://developer.apple.com/documentation/swiftui/laying-out-a-simple-view)
- [WWDC23 · Demystify SwiftUI performance](https://developer.apple.com/videos/play/wwdc2023/10160/)
- [WWDC19 · Combine in Practice](https://developer.apple.com/videos/play/wwdc2019/721/)
