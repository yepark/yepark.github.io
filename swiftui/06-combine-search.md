---
title: "Combine 실습: 검색 화면"
description: "검색어 입력부터 debounce, 이전 요청 취소, 오류 복구, SwiftUI 바인딩까지 Combine 검색 모델을 실행 결과로 확인합니다."
parent: SwiftUI
nav_order: 6
permalink: /swiftui/combine-search/
date: 2026-11-26
first_written: 2026-11-26
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [SwiftUI, iOS, Combine]
---

# Combine 실습: 검색 화면
{: .no_toc }

{% include article-toc.md %}

앞 글에서 본 Combine 연산자로 실제 검색 화면을 만든다. 입력이 멈출 때까지 기다리고(debounce), 새 검색어가 오면 이전 요청을 취소하고, 실패해도 다음 검색은 계속되는 흐름을 모델 하나에 담은 뒤 SwiftUI 화면에 연결한다. 마지막에는 같은 일을 `@Observable`과 async/await로 할 때와 비교한다.

## 실습: 검색어부터 화면 상태까지 연결하기 {#combine-search}

검색창을 만들고 `sw`로 보낸 느린 요청을 `ui`로 바꿔 보자. 결과를 기다리는 동안에는 로딩을 보여 준다. 실패하면 오류 문구를 표시하고, 다음 검색어가 들어오면 다시 검색한다.

```text
TextField → Binding<String> → SearchModel.query
    → $query → 문자열 정리 → 이전 대기·요청 취소 → 새 요청
    → SearchModel.state → body → 목록, 로딩 또는 오류 문구
```

### SearchModel과 검색 서비스 {#combine-search-model}

`query`는 화면이나 사용자가 쓰는 입력이다. `state`는 모델만 쓰는 출력이다. 로딩·결과·실패를 따로 Bool과 배열에 담으면 서로 어긋날 수 있으므로, 한 번에 한 경우만 표현하는 `enum`으로 둔다. 바깥에서 검색 함수를 받으면 실제 API 없이 같은 규칙을 확인할 수 있다.

```swift
import Combine
import Foundation

enum SearchState: Equatable {
    case idle
    case loading
    case results([String])
    case failed(String)
}

@MainActor
final class SearchModel: ObservableObject {
    @Published var query = ""
    @Published private(set) var state = SearchState.idle

    typealias Search = (String) -> AnyPublisher<[String], Error>
    private var subscription: AnyCancellable?

    init(search: @escaping Search) {
        subscription = $query
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .removeDuplicates()
            .map { text -> AnyPublisher<SearchState, Never> in
                guard !text.isEmpty else {
                    return Just(SearchState.idle)
                        .eraseToAnyPublisher()
                }

                return Just(text)
                    .delay(for: .milliseconds(300), scheduler: DispatchQueue.main)
                    .flatMap { term in
                        search(term)
                            .receive(on: DispatchQueue.main)
                            .map(SearchState.results)
                            .catch { _ in Just(.failed("검색에 실패했습니다.")) }
                    }
                    .prepend(.loading)
                    .eraseToAnyPublisher()
            }
            .switchToLatest()
            .sink { [weak self] state in
                self?.state = state
            }
    }
}
```

이 검색에서는 새 검색어가 들어오는 즉시 이전 구독을 끊는다. 입력을 먼저 `debounce`하고 나서 `switchToLatest`에 전달하면, 300ms 대기 중에는 이전 요청이 살아 있어 오래된 응답이 화면에 올 수 있다. 여기서는 **검색어마다 대기와 요청을 하나의 내부 Publisher로 묶고**, 새 검색어를 받는 즉시 `switchToLatest`로 바꾼다. 이는 이전 대기까지 취소해서 결과적으로 300ms 동안 잠잠해진 검색어만 서버에 보낸다.

`catch`는 한 검색의 내부에 있다. 오류를 화면 상태 `.failed`로 바꾼 뒤에도 바깥 `$query` 구독은 다음 입력을 받을 수 있다. 같은 검색어로 다시 시도하는 버튼을 추가하려면 별도 재시도 입력을 연결한다. 현재 코드는 정리한 검색어가 같으면 요청을 건너뛴다.

`AnyPublisher`는 내부 연산자 타입을 숨기되 보내는 값과 오류 타입을 유지한다. 모델에서 반환하는 내부 Publisher는 실패를 화면 상태로 바꿨으므로 `Failure == Never`다. 구독은 모델이 보관한다. `sink`가 모델을 강하게 잡으면 `모델 → 구독 → 클로저 → 모델`로 참조가 이어지므로 `[weak self]`를 사용한다.

다음 가짜 서비스는 `sw`에 700ms, 나머지에 100ms 뒤에 응답한다. `error`를 입력하면 오류를 보낸다. 응답 준비는 백그라운드에서 실행한다. 시작과 취소를 기록해서 화면 출력이 바뀌지 않는 이유를 확인한다.

```swift
import Combine
import Foundation

enum DemoSearch {
    enum Failure: Error { case offline }

    static func search(_ term: String) -> AnyPublisher<[String], Error> {
        let catalog = ["Swift", "SwiftUI", "Combine"]
        let delay = term == "sw" ? 700 : 100

        return Just(term)
            .delay(for: .milliseconds(delay), scheduler: DispatchQueue.global())
            .tryMap { text in
                if text == "error" { throw Failure.offline }
                return catalog.filter { $0.localizedCaseInsensitiveContains(text) }
            }
            .handleEvents(
                receiveSubscription: { _ in print("요청 시작: \(term)") },
                receiveCancel: { print("요청 취소: \(term)") }
            )
            .eraseToAnyPublisher()
    }
}
```

백그라운드 응답은 모델의 `map`과 `catch` 앞에서 메인 큐로 받는다. 빈 입력과 로딩은 메인 액터에 있는 `query`가 바뀔 때 보낸다. 검색 응답도 메인 큐로 옮긴 뒤 모으므로, `switchToLatest` 뒤의 `sink`에서 바로 화면 상태를 쓸 수 있다.

### SwiftUI 화면에서 바인딩하기 {#combine-search-view}

새 SwiftUI 앱에 위의 `SearchModel.swift`와 `DemoSearch.swift`를 추가한다. 기본 앱 진입점 파일을 아래 코드로 교체한다. `@main`은 앱에 하나만 둔다.

```swift
import SwiftUI

@MainActor
struct SearchView: View {
    @StateObject private var model: SearchModel

    init(search: @escaping SearchModel.Search) {
        _model = StateObject(wrappedValue: SearchModel(search: search))
    }

    var body: some View {
        NavigationStack {
            VStack {
                TextField("검색어", text: $model.query)
                    .textFieldStyle(.roundedBorder)
                    .padding()

                switch model.state {
                case .idle:
                    Text("검색어를 입력하세요.")
                case .loading:
                    ProgressView("검색 중")
                case .results(let names):
                    if names.isEmpty {
                        Text("검색 결과가 없습니다.")
                    } else {
                        List(names, id: \.self) { Text($0) }
                    }
                case .failed(let message):
                    Text(message)
                        .foregroundStyle(.red)
                }
                Spacer(minLength: 0)
            }
            .navigationTitle("프레임워크 검색")
        }
    }
}

@main
struct SearchDemoApp: App {
    var body: some Scene {
        WindowGroup {
            SearchView(search: DemoSearch.search)
        }
    }
}
```

`TextField`의 `$model.query`는 SwiftUI가 만드는 `Binding<String>`이다. 반면 모델 내부 `$query`는 Combine의 `Published<String>.Publisher`다. 앞의 경로는 원본 값을 읽고 쓰며, 뒤의 경로는 입력이 변할 때 검색 흐름으로 값을 보낸다. 목록 예제의 문자열은 서로 달라 `id: \.self`를 썼다. 이름이 겹칠 수 있는 실제 데이터에서는 목록 항목의 고유 ID를 사용한다.

Swift 6 모드, iOS 18.2 시뮬레이터 SDK, iOS 16 배포 대상으로 앱 코드의 타입 검사를 통과했다. 시뮬레이터 화면에서 입력을 직접 재생하지는 않았다.

### macOS에서 이전 요청 취소와 실패 복구 확인 {#combine-search-verification}

화면에 바인딩하는 대신 같은 모델의 `$state`를 직접 구독했다. 아래 `main.swift`와 두 모델 파일을 한 폴더에 넣고 실행한다. `wait`는 명령줄 실험에서만 쓰며, 메인 큐에 예약된 이벤트가 도착할 시간을 준다.

```swift
import Combine
import Foundation

func wait(_ seconds: TimeInterval) {
    RunLoop.main.run(until: Date().addingTimeInterval(seconds))
}

@MainActor
func probe() {
    let model = SearchModel(search: DemoSearch.search)
    var received: [SearchState] = []
    let log = model.$state.sink { state in
        precondition(Thread.isMainThread)
        if received.last != state { print("화면 상태: \(state)") }
        received.append(state)
    }

    model.query = "s"
    wait(0.10)
    model.query = "sw"
    wait(0.40)
    model.query = "ui"
    wait(0.50)
    model.query = " ui "
    wait(0.40)
    model.query = "error"
    wait(0.50)
    model.query = "combine"
    wait(0.50)
    model.query = ""
    wait(0.10)

    let finalStates = received.filter { $0 != .loading }
    precondition(finalStates == [
        .idle, .results(["SwiftUI"]),
        .failed("검색에 실패했습니다."),
        .results(["Combine"]), .idle,
    ])
    withExtendedLifetime(log) {}
}

MainActor.assumeIsolated { probe() }
```

```bash
swiftc -swift-version 6 SearchModel.swift DemoSearch.swift main.swift -o search-probe
./search-probe
```

```text
화면 상태: idle
화면 상태: loading
요청 시작: sw
요청 취소: sw
요청 시작: ui
화면 상태: results(["SwiftUI"])
화면 상태: loading
요청 시작: error
화면 상태: failed("검색에 실패했습니다.")
화면 상태: loading
요청 시작: combine
화면 상태: results(["Combine"])
화면 상태: idle
```

`s`의 대기 구독은 요청이 시작되기 전에 끊겼다. 이미 시작한 `sw`는 `ui`가 들어오자 취소됐다. 결과에 SwiftUI만 들어왔고 공백을 더한 `" ui "`도 새 요청을 만들지 않았다. `error` 이후에 `combine` 결과가 다시 왔다. 코드는 모든 상태 이벤트가 메인 스레드에서 왔는지와 예상한 최종 상태 순서를 검사한다.

### Observation과 async/await를 쓰는 경우 {#observation-async-await}

상태 관찰과 비동기 작업은 다른 역할이다. `@Observable`은 화면이 어떤 모델 속성을 읽었는지 추적한다. 자체적으로 `$query` 같은 Combine Publisher가 생기지는 않는다. `async/await`는 함수가 하나의 비동기 결과를 반환할 때 그 호출을 읽기 쉽게 정리한다. iOS 17 이상을 기본으로 하고 검색 API가 `async throws`를 반환한다면 이 둘을 함께 쓸 수 있다.

| 상황 | 나눠 맡길 역할 |
| --- | --- |
| 새 화면에서 읽은 모델 속성에 따라 화면을 갱신 | `@Observable`로 모델 관찰 |
| 검색어마다 잠시 기다렸다가 비동기 API 한 번 호출 | `.task(id:)`, `Task.sleep`, `async/await` |
| 이미 Publisher를 받거나 여러 입력 스트림을 합침 | Combine으로 값의 흐름을 처리 |
| iOS 16 이하 지원 또는 기존 Combine 모델을 화면에 연결 | `ObservableObject`와 `@StateObject` 또는 `@ObservedObject` |

`.task(id: 정리한검색어)`에 작업을 달면 ID가 바뀌거나 화면이 사라질 때 SwiftUI가 이전 작업의 취소를 요청한다. 취소는 협력적이다. 서비스에서 결과를 받았더라도 상태를 쓰기 전에 `Task.checkCancellation()`으로 확인해야 한다. 사용자 입력 때문에 취소된 경우에는 실패 문구를 표시하지 않는다. Combine의 `switchToLatest`와 `.task(id:)` 모두 최신 입력만 화면에 반영하는 데 쓸 수 있다. [Apple · task(id:)](https://developer.apple.com/documentation/swiftui/view/task(id:name:priority:file:line:_:)) · [Apple · Task](https://developer.apple.com/documentation/swift/task)

## 이어서 읽기

- 이전 글: [Combine과 SwiftUI]({{ '/swiftui/combine/' | relative_url }})
- 다음 글: [UIKit 연동과 미리보기]({{ '/swiftui/uikit-preview/' | relative_url }})
- [SwiftUI 연재 목차]({{ '/swiftui/' | relative_url }})
