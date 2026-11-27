---
title: "UIKit 연동과 미리보기"
description: "UIHostingController와 UIViewRepresentable로 UIKit과 SwiftUI를 섞어 쓰는 방법과 #Preview를 설명합니다."
parent: SwiftUI
nav_order: 7
permalink: /swiftui/uikit-preview/
date: 2026-11-26
first_written: 2026-11-26
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [SwiftUI, iOS]
---

# UIKit 연동과 미리보기
{: .no_toc }

{% include article-toc.md %}

이미 UIKit으로 만든 앱도 SwiftUI를 조금씩 섞어 쓸 수 있다. 이 글은 UIKit 화면 안에 SwiftUI 뷰를 넣는 방법과 그 반대 방향, 그리고 코드를 실행하지 않고 Xcode에서 화면을 바로 확인하는 `#Preview`를 다룬다.

## UIKit과 함께 쓰기
{: id="uikit과-함께-쓰기" }

기존 UIKit 앱을 한 번에 바꿀 필요는 없다. 두 방향 모두 연결할 수 있다.

### UIKit 화면 안에 SwiftUI 넣기: UIHostingController
{: id="uikit-화면-안에-swiftui-넣기-uihostingcontroller" }

`UIHostingController`(iOS 13)는 SwiftUI 뷰를 담은 `UIViewController`다. Apple 문서 설명대로 다른 뷰 컨트롤러처럼 push, present, 자식 뷰 컨트롤러로 쓸 수 있다.

```swift
final class HomeViewController: UIViewController {
    func showSettings() {
        let vc = UIHostingController(
            rootView: SettingsView()
        )
        navigationController?
            .pushViewController(vc, animated: true)
    }
}
```

### SwiftUI 안에 UIKit 뷰 넣기: UIViewRepresentable
{: id="swiftui-안에-uikit-뷰-넣기-uiviewrepresentable" }

반대로 SwiftUI에 아직 없는 UIKit 뷰를 쓰고 싶으면 `UIViewRepresentable`(iOS 13)로 감싼다. 메서드 두 개가 핵심이다.

- `makeUIView`: UIKit 뷰를 **처음 한 번** 만든다.
- `updateUIView`: SwiftUI 상태가 바뀌면 불린다. 여기서 UIKit 뷰를 **새 상태에 맞춘다.**

```swift
struct ActivityIndicator: UIViewRepresentable {
    var isAnimating: Bool

    func makeUIView(context: Context)
        -> UIActivityIndicatorView {
        UIActivityIndicatorView(style: .large)
    }

    func updateUIView(
        _ view: UIActivityIndicatorView,
        context: Context
    ) {
        if isAnimating {
            view.startAnimating()
        } else {
            view.stopAnimating()
        }
    }
}
```

위 두 iOS 코드는 iOS 17 배포 대상으로 컴파일만 확인했다. 대신 같은 구조인 macOS의 `NSViewRepresentable`로 `NSTextField`를 감싸서 호출 순서를 찍었다.

```swift
struct LabelBox: NSViewRepresentable {
    var text: String
    func makeNSView(context: Context) -> NSTextField {
        print("makeNSView")
        return NSTextField(labelWithString: text)
    }
    func updateNSView(_ v: NSTextField,
                      context: Context) {
        print("updateNSView text=\(text)")
        v.stringValue = text
    }
}
```

`text`에 연결된 `@Observable` 모델의 `name`을 두 번 바꿨다.

```text
makeNSView
updateNSView text=Kim
--- name = Lee
updateNSView text=Lee
--- name = Park
updateNSView text=Park
```

이 실행에서는 정체성이 유지되는 동안 AppKit 뷰를 한 번 만들고, `updateNSView`에서 내용을 반영했다. UIKit의 `UIViewRepresentable`도 뷰 생성과 값 반영을 분리한다.

{: .warning }
Apple 문서에 따르면 SwiftUI가 감싼 UIKit 뷰의 `frame`, `bounds`, `center`, `transform`을 직접 바꾸면 안 된다. 레이아웃은 SwiftUI가 맡는다. 또 UIKit 뷰 안에서 생긴 변화(delegate, target-action)는 자동으로 SwiftUI에 전달되지 않는다. 전달하려면 `Coordinator`를 만들어야 한다.

## 미리보기: #Preview
{: id="미리보기-preview" }

Xcode는 코드 옆 캔버스에 뷰를 바로 그려 준다. 파일 아래에 `#Preview` 매크로를 쓰면 된다.

```swift
#Preview {
    MailListView()
}
```

Apple 문서에 따르면 한 파일에 미리보기를 여러 개 둘 수 있고, `#Preview("이름")`처럼 이름을 붙여 캔버스에서 구분할 수 있다. 단순한 뷰를 사용하는 별도 `#Preview`는 iOS 13 배포 대상으로도 컴파일했다. 위의 `MailListView` 미리보기는 내부 `NavigationStack` 때문에 iOS 16 이상이 필요하며, iOS 16으로 타입 검사를 확인했다.

{: .note }
이 글을 쓴 환경에서는 Xcode 캔버스를 열어 보지 않았다. `#Preview`는 컴파일만 확인했다.

## 이어서 읽기

- 이전 글: [Combine 실습: 검색 화면]({{ '/swiftui/combine-search/' | relative_url }})
- 다음 글: [SwiftData로 데이터 저장하기]({{ '/swiftui/swiftdata/' | relative_url }})
- [SwiftUI 연재 목차]({{ '/swiftui/' | relative_url }})
