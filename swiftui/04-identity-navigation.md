---
title: "뷰의 정체성과 목록·화면 이동"
description: ".id와 if/else가 뷰 정체성과 @State 수명에 주는 영향, List·ForEach의 식별자, NavigationStack을 설명합니다."
parent: SwiftUI
nav_order: 4
permalink: /swiftui/identity-navigation/
date: 2026-11-26
first_written: 2026-11-26
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [SwiftUI, iOS]
---

# 뷰의 정체성과 목록·화면 이동
{: .no_toc }

{% include article-toc.md %}

앞 글에서 `@State` 값은 뷰 struct가 새로 만들어져도 유지된다고 했다. 이 글은 그 값이 언제 사라지는지, 즉 SwiftUI가 "같은 뷰"를 어떻게 알아보는지(정체성)를 실험으로 확인한다. 이어서 정체성이 중요한 목록(`List`, `ForEach`)과 화면 이동(`NavigationStack`)을 다룬다.

## 뷰의 정체성과 수명
{: id="뷰의-정체성과-수명" }

앞에서 "View struct는 자주 새로 만들어지지만 `@State`는 남는다"고 했다. 그럼 `@State`는 **언제** 사라질까? 답은 뷰의 **정체성(identity)** 이 바뀔 때다.

{: .tip }
정체성은 SwiftUI가 붙이는 이름표다. struct 값이 새로 만들어져도 이름표가 같으면 "같은 뷰"로 보고 상태를 이어 준다. 이름표가 바뀌면 "다른 뷰"로 보고 상태를 새로 만든다.

실험용으로 `@State`의 초깃값을 만들 때마다 번호를 하나씩 올리는 함수 `nextSerial()`을 만들었다.

```swift
struct Child: View {
    @State private var serial = nextSerial()
    var body: some View {
        let _ = print("Child.body serial=\(serial)")
        Text("serial \(serial)")
    }
}
```

### .id로 정체성을 바꾸기
{: id="id로-정체성을-바꾸기" }

`.id(_:)` 수정자는 정체성을 직접 정한다. Apple 문서는 "`id` 값이 바뀌면 뷰의 정체성, 예를 들어 상태가 초기화된다"고 설명한다.

```swift
struct IdScreen: View {
    // Root: version, other를 가진 @Observable 모델
    let root: Root
    var body: some View {
        let _ = print("IdScreen.body other=\(root.other)")
        Child()
            .id(root.version)
    }
}
```

`other`(관계없는 값)를 바꾼 다음, `version`(`.id`에 쓴 값)을 바꿨다.

```text
IdScreen.body other=0
  nextSerial() -> 1
Child.body serial=1
--- other += 1
IdScreen.body other=1
  nextSerial() -> 2
Child.body serial=1
--- version += 1
IdScreen.body other=1
  nextSerial() -> 3
Child.body serial=3
```

- `other`를 바꾸자 부모가 다시 계산되며 `Child()`도 새로 만들어졌다(`nextSerial() -> 2`). 그런데 화면의 `serial`은 **여전히 1**이다. 정체성이 같으니 SwiftUI가 기존 상태를 이어 주고, 새로 만든 2는 버렸다.
- `version`을 바꾸자 `serial`이 **3**이 됐다. 정체성이 바뀌어 상태가 새로 만들어졌다.

{: .note }
목록 화면에서 "필터를 바꾸면 스크롤 위치와 입력 상태를 처음부터 시작"하고 싶을 때 `.id`를 쓴다. 반대로 상태가 이유 없이 초기화된다면, 어딘가에서 정체성이 바뀌고 있는지 의심해 본다.

### if/else도 정체성을 바꾼다
{: id="ifelse도-정체성을-바꾼다" }

`.id`를 쓰지 않아도 정체성이 바뀌는 경우가 있다. SwiftUI는 **코드 구조 속 위치**도 이름표로 쓴다. 이것을 구조적 정체성(structural identity)이라고 한다. `if`의 참 쪽과 거짓 쪽은 서로 다른 자리다.

```swift
// 방법 1: 분기로 나누기
if root.flag {
    Child().padding()
} else {
    Child()
}

// 방법 2: 수정자 값만 바꾸기
Child()
    .padding(root.flag ? 20 : 0)
```

두 방법 모두 `flag`를 `false`에서 `true`로 바꿨다.

```text
[방법 1: if/else]
  nextSerial() -> 1
Child.body serial=1
--- flag = true
  nextSerial() -> 2
Child.body serial=2

[방법 2: 수정자 값]
  nextSerial() -> 1
Child.body serial=1
--- flag = true
  nextSerial() -> 2
Child.body serial=1
```

보기에는 둘 다 "여백이 생긴다"로 같다. 하지만 방법 1은 상태가 초기화됐고(`serial=2`), 방법 2는 유지됐다(`serial=1`).

{: .question }
토글 스위치를 켤 때마다 화면 안의 입력값이 지워지는 버그가 있다. 위 두 방법 중 어느 쪽으로 코드가 짜여 있을 가능성이 높을까?

{: .warning }
위 출력에서 `nextSerial()`이 뷰를 만들 때마다 불린 것은 Xcode 16.2의 `@State` 프로퍼티 래퍼 동작이다. Apple 문서도 `State`가 뷰를 만들 때마다 기본값을 만든다고 설명하며, 무거운 객체를 기본값으로 만들지 말라고 한다. 한편 2026년 11월 27일 확인한 Apple 문서는 **Xcode 27 이상으로 빌드하면 `@State`가 `State()` 매크로로 바뀌고, 기본값을 처음 한 번만 만든다**고 적고 있다. 이 동작은 직접 실행해 보지 않았다.

## 목록과 화면 이동
{: id="목록과-화면-이동" }

### List와 ForEach는 "누가 누구인지"를 알아야 한다
{: id="list와-foreach는-누가-누구인지를-알아야-한다" }

`List`나 `ForEach`에 배열을 주면 항목마다 뷰를 만든다. Apple 문서는 이때 요소가 `Identifiable`을 따르거나, `id:` 인자로 구분할 값을 알려 줘야 한다고 설명한다. `Identifiable`은 `id` 프로퍼티 하나만 있으면 되는 프로토콜이다.

```swift
struct Mail: Identifiable, Hashable {
    let id: Int
    var title: String
}
```

`id`가 필요한 이유는 배열이 바뀔 때 SwiftUI가 "3번 메일이 삭제됐다", "1번 메일은 그대로다"를 구분하기 위해서다. `UITableView`의 diffable data source에 식별자를 주던 것과 비슷한 역할이다.

### NavigationStack (iOS 16)
{: id="navigationstack-ios-16" }

화면 이동은 `NavigationStack`(iOS 16)으로 한다. `UINavigationController`처럼 화면을 쌓는다.

```swift
struct MailListView: View {
    let mails = [
        Mail(id: 1, title: "회의 일정"),
        Mail(id: 2, title: "청구서"),
    ]

    var body: some View {
        NavigationStack {
            List(mails) { mail in
                NavigationLink(mail.title, value: mail)
            }
            .navigationDestination(for: Mail.self) { mail in
                Text(mail.title)
            }
            .navigationTitle("메일")
        }
    }
}
```

`NavigationLink`는 "어디로 갈지(뷰)"가 아니라 **"무슨 값을 보여 줄지(`mail`)"** 만 넘긴다. 그 값을 받아 어떤 화면을 띄울지는 `.navigationDestination(for:)`이 정한다. Apple 문서의 설명대로, 링크를 누르면 상세 화면이 스택 위에 올라가고 뒤로 가면 빠진다.

{: .warning }
이 코드는 iOS 16 배포 대상으로 컴파일만 확인했고 실제로 화면을 눌러 보지는 않았다. iOS 15 대상으로 컴파일하면 `'NavigationStack' is only available in iOS 16.0 or newer` 오류가 난다. iOS 15 이하는 예전 `NavigationView`를 써야 한다.

## 이어서 읽기

- 이전 글: [상태와 데이터 흐름]({{ '/swiftui/state/' | relative_url }})
- 다음 글: [Combine과 SwiftUI]({{ '/swiftui/combine/' | relative_url }})
- [SwiftUI 연재 목차]({{ '/swiftui/' | relative_url }})
