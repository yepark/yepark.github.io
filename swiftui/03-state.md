---
title: "상태와 데이터 흐름"
description: "@State, @Binding, @Observable, ObservableObject, @StateObject와 @ObservedObject, @Bindable과 @Environment로 값의 소유권과 전달을 설명합니다."
parent: SwiftUI
nav_order: 3
permalink: /swiftui/state/
date: 2026-11-26
first_written: 2026-11-26
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [SwiftUI, iOS]
---

# 상태와 데이터 흐름
{: .no_toc }

{% include article-toc.md %}

## 상태와 데이터 흐름
{: id="상태와-데이터-흐름" }

이제 핵심이다. SwiftUI에서 화면은 상태의 결과다. 상태를 어디에 두고, 누가 바꾸고, 누가 읽는지 정하는 도구가 여럿 있다.

### @State: 뷰가 직접 가진 값
{: id="state-뷰가-직접-가진-값" }

`@State`는 iOS 13부터 쓸 수 있다. Apple 문서는 `@State`를 "뷰 계층에 저장하는 값 타입의 단일 진실 공급원(single source of truth)"으로 쓰라고 하고, **`private`으로 선언하라**고 권한다.

{: .tip }
단일 진실 공급원은 "이 값의 원본은 딱 한 곳"이라는 뜻이다. 복사본이 여러 곳에 있으면 어느 것이 맞는지 헷갈린다. 원본은 하나만 두고, 나머지는 원본을 빌려 쓴다.

View는 struct라서 자주 새로 만들어진다고 했다. 그래도 `@State` 값은 사라지지 않는다. 값의 저장 공간을 **SwiftUI가 따로 관리**하기 때문이다.

`body`가 언제 다시 계산되는지 직접 찍어 보자. `body` 안에서 `let _ = print(...)`을 쓰면 계산될 때마다 출력된다.

```swift
struct CounterView: View {
    @State private var count = 0

    var body: some View {
        let _ = print("CounterView.body count=\(count)")
        VStack {
            Text("count: \(count)")
            StaticLabel()
            PlusTen(count: $count)
        }
        .task {
            count += 1
        }
    }
}

struct StaticLabel: View {
    var body: some View {
        let _ = print("StaticLabel.body")
        Text("고정 문구")
    }
}

struct PlusTen: View {
    @Binding var count: Int

    var body: some View {
        let _ = print("PlusTen.body count=\(count)")
        Button("+10") { count += 10 }
            .task {
                try? await Task.sleep(
                    for: .milliseconds(100))
                count += 10
            }
    }
}
```

실험에서는 화면이 뜨면 실행되는 `.task`(iOS 15부터)에서 값을 바꿨다. `CounterView`가 뜨면 1을 더하고, 0.1초 뒤 `PlusTen`이 10을 더한다.

```text
CounterView.body count=0
StaticLabel.body
PlusTen.body count=0
CounterView.body count=1
PlusTen.body count=1
CounterView.body count=11
PlusTen.body count=11
```

출력에서 세 가지를 읽을 수 있다.

1. `count`가 바뀔 때마다 `CounterView.body`가 다시 계산됐다.
2. `count`를 받는 `PlusTen`도 다시 계산됐다.
3. `StaticLabel.body`는 처음 한 번만 찍혔다. 받는 값이 없으니 다시 계산할 이유가 없었다.

이 실행에서 변경된 상태에 의존하는 두 뷰의 `body`가 다시 평가됐다. 같은 뷰라도 부모의 입력, 환경, 정체성이 달라지면 다른 이유로 다시 평가될 수 있다. 출력은 의존성을 설명하는 실험 결과다.

### @Binding: 남의 값을 빌려 쓰고 고치기
{: id="binding-남의-값을-빌려-쓰고-고치기" }

`PlusTen`은 `count`를 직접 갖지 않는다. `@Binding`으로 **`CounterView`의 `count`를 빌려** 왔다. 부모가 `$count`처럼 `$`를 붙여 넘기면 바인딩이 된다.

위 출력의 마지막 두 줄을 보자. 자식인 `PlusTen`이 `count += 10`을 했는데, 부모 `CounterView`의 값이 `11`이 됐다. 자식이 고친 것이 원본에 반영됐다.

{: .note }
Apple 문서 기준 정리다. 자식이 값을 **읽기만** 하면 그냥 값으로 넘긴다. 자식이 값을 **고쳐야** 하면 `$`를 붙여 바인딩으로 넘긴다.

UIKit에서 delegate나 클로저로 "값 바뀌었어요"를 부모에게 알리던 일을 바인딩 한 줄이 대신한다. 클로저로 직접 바인딩을 만드는 방식은 [클로저 기반 데이터 바인딩과 Box]({{ '/swift/data-binding/' | relative_url }})에서 다뤘다.

### 원본과 바인딩을 어디에 둘까 {#state-ownership}

화면마다 값을 고칠 책임이 있는 곳을 먼저 정한다. 예를 들어 결제 화면의 주소 원본이 뷰모델에 있다면 팝업의 입력 필드에는 원본에 쓰는 바인딩을 주거나, 확인을 누를 때만 원본에 반영하는 **임시 초안**을 만든다. 임시 초안의 저장 시점까지 정해 두면 화면이 두 개여도 담당이 분명하다.

| 필요한 일 | 값 또는 모델의 원본 | 받는 쪽 |
| --- | --- | --- |
| 화면의 토글이나 텍스트 입력을 소유 | 해당 뷰의 `@State private` | 읽기만 하면 값, 수정하면 `@Binding` |
| 기존 Combine 모델을 소유 | 생성하는 뷰의 `@StateObject` | 인자로 받은 `@ObservedObject` |
| 같은 Combine 모델을 여러 단계에 전달 | 상위에서 `.environmentObject(model)` | `@EnvironmentObject` |
| Observation 모델을 소유 | 생성하는 뷰의 `@State private` | 읽기만 하면 평범한 프로퍼티, 모델 속성의 바인딩을 만들면 `@Bindable` |
| 같은 Observation 모델을 여러 단계에 전달 | 상위에서 `.environment(model)` | `@Environment(Model.self)` |
| 시스템 색상 모드처럼 환경 값을 읽기 | 부모나 시스템이 공급한 환경 값 | `@Environment(\.colorScheme)` |

`@Binding`은 저장 공간을 그대로 유지하면서 읽기와 쓰기를 전달하는 통로다. `@State`의 `$name`과 `@Bindable`의 `$profile.name`을 `TextField`에 전달하는 이유다. `$`의 결과 타입은 프로퍼티 래퍼가 정한다. 뒤에서 `@Published`의 `$query`가 Publisher인 경우를 확인한다.

### 무엇 때문에 다시 계산됐는지 묻기
{: id="무엇-때문에-다시-계산됐는지-묻기" }

`Self._printChanges()`를 `body`에 넣으면 SwiftUI가 다시 계산한 이유를 출력한다. 이름이 밑줄로 시작하는 디버깅용 메서드라서, 확인할 때만 넣고 지운다. iOS 15부터 쓸 수 있다.

```swift
struct ChangesView: View {
    @State private var count = 0

    var body: some View {
        let _ = Self._printChanges()
        Text("\(count)")
            .task { count += 1 }
    }
}
```

```text
ChangesView: @self, @identity, _count changed.
ChangesView: _count changed.
```

첫 줄은 처음 나타났을 때다. 두 번째 줄은 `count`(내부 이름 `_count`)가 바뀌어서 다시 계산했다는 뜻이다.

### @Observable: 모델 객체를 관찰하기 (iOS 17)
{: id="observable-모델-객체를-관찰하기-ios-17" }

화면 하나에 담기 어려운 데이터는 클래스 모델로 뺀다. iOS 17, macOS 14부터는 `@Observable` 매크로를 붙이면 된다. 프로퍼티에 따로 표시할 것이 없다.

```swift
import Observation

@Observable
final class Profile {
    var name = "Kim"
    var score = 0
}

struct NameView: View {
    let profile: Profile
    var body: some View {
        let _ = print("NameView.body")
        Text(profile.name)
    }
}

struct ScoreView: View {
    let profile: Profile
    var body: some View {
        let _ = print("ScoreView.body")
        Text("\(profile.score)")
    }
}

struct ProfileScreen: View {
    let profile: Profile
    var body: some View {
        let _ = print("ProfileScreen.body")
        VStack {
            NameView(profile: profile)
            ScoreView(profile: profile)
        }
    }
}
```

`NameView`는 `name`만, `ScoreView`는 `score`만 읽는다. 화면을 띄운 다음 바깥에서 `score`와 `name`을 차례로 바꿨다.

```text
ProfileScreen.body
NameView.body
ScoreView.body
--- score += 1
ScoreView.body
--- name = Lee
NameView.body
```

`score`를 바꾸면 `ScoreView`만, `name`을 바꾸면 `NameView`만 다시 계산됐다. `ProfileScreen`은 `profile`의 프로퍼티를 읽지 않으니 한 번도 다시 계산되지 않았다.

Observation은 `body`를 평가하는 동안 모델에서 실제 읽은 프로퍼티를 추적한다. 그 프로퍼티를 쓰면 해당 뷰의 의존성이 바뀐다. 계산 프로퍼티가 모델의 다른 값을 읽으면 그 안에서 읽은 값도 추적 대상이 된다. 관찰할 필요가 없는 프로퍼티는 `@ObservationIgnored`로 표시할 수 있다. SwiftUI의 다른 입력이나 환경 변화는 여전히 별도로 뷰 갱신을 일으킬 수 있다. [Apple · Managing model data in your app](https://developer.apple.com/documentation/swiftui/managing-model-data-in-your-app)

{: .tip }
`@Observable`은 뷰마다 "네가 읽은 칸"을 메모해 두는 사서다. `score` 칸이 바뀌면 `score`를 읽어 간 사람에게만 연락한다.

### 예전 방식: ObservableObject와 비교
{: id="예전-방식-observableobject와-비교" }

SwiftUI의 Observation 통합이 들어온 iOS 17보다 낮은 버전을 지원하거나 기존 Combine 모델을 유지할 때는 `ObservableObject`와 `@Published`를 사용할 수 있다. 같은 실험을 해 보자.

```swift
final class OldProfile: ObservableObject {
    @Published var name = "Kim"
    @Published var score = 0
}

struct OldNameView: View {
    @ObservedObject var profile: OldProfile
    var body: some View {
        let _ = print("OldNameView.body")
        Text(profile.name)
    }
}
// OldScoreView는 score를 읽는다 (구조는 같다)
```

```text
OldNameView.body
OldScoreView.body
--- score += 1
OldNameView.body
OldScoreView.body
```

`score`만 바꿨는데 `name`만 읽는 `OldNameView`도 다시 계산됐다. 이 방식에서 SwiftUI는 프로퍼티마다 추적하는 대신 객체가 내는 `objectWillChange` 알림을 관찰한다. 같은 객체를 관찰하는 뷰들은 모두 이 알림을 받는다.

두 방식의 도구는 이렇게 짝지어진다. Apple의 마이그레이션 문서 기준이다.

| 하는 일 | 예전 (`ObservableObject`) | 지금 (`@Observable`, iOS 17) |
| --- | --- | --- |
| 모델 표시 | `ObservableObject` 채택 + `@Published` | `@Observable` 매크로 하나 |
| 뷰가 모델을 소유 | `@StateObject` (iOS 14) | `@State` |
| 받은 모델을 관찰 | `@ObservedObject` | 표시 없이 그냥 프로퍼티 |
| 받은 모델의 바인딩 | `@ObservedObject` + `$` | `@Bindable` |
| 환경으로 전달 | `.environmentObject(_:)` | `.environment(_:)` |
| 환경에서 읽기 | `@EnvironmentObject` | `@Environment(타입.self)` |

{: .note }
Apple 문서는 한 번에 다 바꿀 필요가 없다고 설명한다. 모델 타입 하나씩 `@Observable`로 옮겨도 되고, 두 방식이 한 앱에 섞여 있어도 된다.

### @StateObject와 @ObservedObject의 차이
{: id="stateobject와-observedobject의-차이" }

예전 방식에서 자주 헷갈리는 부분이 있다. 둘 다 객체를 관찰하지만, **누가 객체를 소유하느냐**가 다르다. SwiftUI는 같은 정체성이 유지되는 동안 `@StateObject`의 객체를 보존한다. 뷰 초기화 인자가 바뀌어도 기존 객체가 자동으로 교체되지는 않는다. [Apple · StateObject](https://developer.apple.com/documentation/swiftui/stateobject)

```swift
@MainActor
final class Ticket: ObservableObject {
    let no: Int
    // 만들 때마다 1, 2, 3... 번호를 받는다
    init() { no = nextSerial() }
}

struct OwnerView: View {
    @StateObject private var ticket = Ticket()
    // body에서 ticket.no를 출력
}

struct BorrowView: View {
    @ObservedObject var ticket = Ticket()
    // body에서 ticket.no를 출력
}
```

두 뷰를 담은 부모 화면을 다시 계산하게 만들었다.

```text
TicketScreen other=0
  nextSerial() -> 1
  nextSerial() -> 2
OwnerView ticket=2
BorrowView ticket=1
--- other += 1
TicketScreen other=1
  nextSerial() -> 3
BorrowView ticket=3
```

부모가 다시 계산되자 `BorrowView`는 새 `Ticket`(3번)을 받았다. 이전 객체에 담겨 있던 값은 사라진다. `OwnerView`는 새로 만들지 않았다.

{: .warning }
`@ObservedObject`는 "남이 만든 객체를 빌려 본다"는 표시다. 그 자리에서 `= Ticket()`처럼 직접 만들면 부모가 다시 계산될 때마다 새 객체가 생긴다. 뷰가 직접 만드는 객체는 `@StateObject`(iOS 17 이상에서 `@Observable`이면 `@State`)에 둔다.

### @Bindable과 @Environment (iOS 17)
{: id="bindable과-environment-ios-17" }

`@Observable` 모델의 프로퍼티를 `TextField`처럼 바인딩이 필요한 곳에 넘기려면 `@Bindable`을 붙인다. 그러면 `$profile.name` 같은 바인딩을 만들 수 있다.

```swift
struct NameEditor: View {
    @Bindable var profile: Profile
    var body: some View {
        TextField("이름", text: $profile.name)
    }
}
```

여러 단계 아래 뷰까지 같은 모델을 넘겨야 하면, 중간 뷰마다 인자로 넘기는 대신 **환경(environment)** 에 넣는다.

```swift
struct ScoreBadge: View {
    @Environment(Profile.self) private var profile
    var body: some View {
        let _ = print(
            "ScoreBadge.body score=\(profile.score)")
        Text("\(profile.score)점")
    }
}

// 위쪽 어딘가에서
ScoreBadge()
    .environment(profile)
```

환경에 `Profile`이 공급되지 않았는데 `@Environment(Profile.self)`를 필수 타입으로 읽으면 실행 중 오류가 난다. 필요한 값을 앱이 제공하는 위치와 미리보기에서 주입하는 위치를 함께 확인한다. 아래 실행에서는 올바로 주입한 모델의 `score`를 5 올렸다.

```text
ScoreBadge.body score=0
--- score += 5
ScoreBadge.body score=5
```

{: .tip }
환경은 건물의 방송 시스템이다. 1층에서 한 번 틀면 위층 어느 방에서든 들을 수 있다. 중간 층마다 쪽지를 전달할 필요가 없다.

`@Bindable`, `@Environment(타입.self)`, `@Observable`은 모두 iOS 17이 필요하다. 배포 대상을 iOS 13으로 두고 컴파일하자 컴파일러가 이렇게 알려 줬다(Xcode 16.2, iOS 18.2 SDK).

```text
error: 'Observable()' is only available in iOS 17.0 or newer
error: 'Bindable' is only available in iOS 17.0 or newer
error: 'StateObject' is only available in iOS 14.0 or newer
error: 'task(priority:_:)' is only available in iOS 15.0 or newer
```

(같은 파일의 `@State`, `ObservableObject`, `#Preview`는 iOS 13에서 오류가 나지 않았다.)

## 주요 API

| API | 역할 |
| --- | --- |
| `@State` | 뷰가 소유하는 값. 값이 바뀌면 `body`를 다시 계산한다 |
| `@Binding` | 다른 뷰가 가진 값을 읽고 고치는 연결. `$value`로 넘긴다 |
| `@Observable` | iOS 17. `body`에서 읽은 속성만 관찰하는 모델 매크로 |
| `@Bindable` | iOS 17. `@Observable` 모델의 속성을 `$model.name`처럼 바인딩 |
| `@Environment(Model.self)` / `.environment(model)` | iOS 17. 하위 뷰 전체에 모델 전달·읽기 |
| `ObservableObject` / `@Published` | 객체 단위 변경 알림(`objectWillChange`)을 보내는 예전 방식 |
| `@StateObject` | 뷰가 만들고 소유하는 `ObservableObject`. 뷰가 다시 만들어져도 유지 |
| `@ObservedObject` | 밖에서 받은 `ObservableObject`를 관찰. 소유하지 않는다 |
| `Self._printChanges()` | 디버그용. 무엇 때문에 `body`가 다시 계산됐는지 출력 |

## 이어서 읽기

- 이전 글: [SwiftUI 레이아웃]({{ '/swiftui/layout/' | relative_url }})
- 다음 글: [뷰의 정체성과 목록·화면 이동]({{ '/swiftui/identity-navigation/' | relative_url }})
- [SwiftUI 연재 목차]({{ '/swiftui/' | relative_url }})
