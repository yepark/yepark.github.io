---
title: "MVVM + RxSwift"
description: "RxSwift로 검색 뷰모델을 만들고 Single·Driver·Signal로 요청과 화면을 연결합니다. RxTest로 중복 요청, 로딩, 실패 후 다음 검색을 확인합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 7
permalink: /swift/rxswift/mvvm/
last_modified_at: 2026-11-26
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-26
tags: [Swift, RxSwift, MVVM, Architecture, iOS]
---

# MVVM + RxSwift
{: .no_toc }

{% include article-toc.md %}

검색창에 `s`, `sw`, `swi`를 연달아 입력한 뒤 사용자가 멈추면 `swi`로 한 번만 요청한다. 화면에는 검색 결과와 로딩 상태가 함께 바뀐다. 실패 메시지가 필요해도 그 메시지를 얻으려고 서버에 다시 요청할 필요는 없다.

**MVVM(Model–View–ViewModel)**의 세 부분에 이 일을 나눈다. Model 쪽 서비스는 검색어에 맞는 응답을 가져온다. ViewModel은 검색창 입력을 받아 검색할 때를 정하고, 결과·로딩·오류를 화면에 내보낸다. View는 입력과 출력을 연결한다. 뷰모델이 검색 함수와 시계를 매개변수로 받으면 화면과 HTTP 서버 없이도 흐름을 검사할 수 있다.

```text
View의 입력         ViewModel                         View의 출력
검색어   ────────▶  공백 제거 → 타이머 → 요청  ────────▶  결과 목록
                                                 ├───▶  로딩 상태
                                                 └───▶  실패 알림
```

## 값의 개수를 타입으로 약속하기

**Trait**는 Observable에서 어떤 종류의 이벤트를 받을지 타입 이름으로 좁혀 표현한다. 사용자 한 명을 가져오는 요청, 없어도 정상인 캐시, 받은 값을 돌려줄 필요가 없는 저장이 각각 다른 약속을 갖는다.

| 타입 | 성공 경로 | 오류 경로 | 사례 |
| --- | --- | --- | --- |
| `Single<T>` | 값 하나 | 실패 | 서버에서 사용자 한 명 읽기 |
| `Maybe<T>` | 값 하나 또는 값 없이 완료 | 실패 | 캐시에 저장된 이미지 읽기 |
| `Completable` | 값 없이 완료 | 실패 | 토큰 저장 |

아래 예제는 RxSwift 6.9.1, Swift 6.0.3, macOS 15.6에서 실행했다. 실행 파일에 공통 코드부터 붙인다. `wait`는 이후 예제에서 메인 큐에 예약한 작업을 기다린다.

```swift
import Foundation
import RxSwift
import RxCocoa

let disposeBag = DisposeBag()
enum APIError: Error { case server, offline }
func here() -> String { Thread.isMainThread ? "main" : String(cString: __dispatch_queue_get_label(nil)) }
func wait(_ s: Double) { RunLoop.main.run(until: Date().addingTimeInterval(s)) }
let io = SerialDispatchQueueScheduler(internalSerialQueueName: "io")
```

```swift
print("--- 1. Single")
func fetchUser(id: Int) -> Single<String> {
    Single.create { single in
        if id == 1 { single(.success("yep")) } else { single(.failure(APIError.server)) }
        return Disposables.create()
    }
}
for id in [1, 2] {
    fetchUser(id: id)
        .subscribe(onSuccess: { print("id \(id) 성공:", $0) },
                   onFailure: { print("id \(id) 실패:", $0) })
        .disposed(by: disposeBag)
}

print("--- 2. asSingle(): 값 개수가 정확히 1개여야 한다")
for (name, o) in [("1개", Observable.of(1)), ("0개", Observable<Int>.empty()), ("2개", Observable.of(1, 2))] {
    o.asSingle()
        .subscribe(onSuccess: { print(name, "→ success", $0) },
                   onFailure: { print(name, "→ failure", $0) })
        .disposed(by: disposeBag)
}

print("--- 3. Maybe")
func cachedImage(for key: String) -> Maybe<String> {
    Maybe.create { maybe in
        if key == "hit" { maybe(.success("캐시 이미지")) } else { maybe(.completed) }
        return Disposables.create()
    }
}
for key in ["hit", "miss"] {
    cachedImage(for: key)
        .subscribe(onSuccess: { print(key, "→ success", $0) },
                   onError: { print(key, "→ error", $0) },
                   onCompleted: { print(key, "→ completed (값 없음)") })
        .disposed(by: disposeBag)
}

print("--- 4. Completable + andThen")
func saveToken() -> Completable {
    Completable.create { completable in
        print("  토큰 저장")
        completable(.completed)
        return Disposables.create()
    }
}
saveToken()
    .andThen(fetchUser(id: 1))
    .subscribe(onSuccess: { print("저장 뒤 사용자:", $0) })
    .disposed(by: disposeBag)

print("--- 5. Single도 공유하지 않는다 (cold)")
var requestCount = 0
let request = Single<String>.create { single in
    requestCount += 1
    single(.success("응답"))
    return Disposables.create()
}
request.subscribe().disposed(by: disposeBag)
request.subscribe().disposed(by: disposeBag)
print("요청 횟수:", requestCount)
```

```text
--- 1. Single
id 1 성공: yep
id 2 실패: server
--- 2. asSingle(): 값 개수가 정확히 1개여야 한다
1개 → success 1
0개 → failure Sequence doesn't contain any elements.
2개 → failure Sequence contains more than one element.
--- 3. Maybe
hit → success 캐시 이미지
miss → completed (값 없음)
--- 4. Completable + andThen
  토큰 저장
저장 뒤 사용자: yep
--- 5. Single도 공유하지 않는다 (cold)
요청 횟수: 2
```

`asSingle()`은 값이 정확히 하나인지 확인한다. 원본의 값을 미리 하나로 자르는 연산자가 아니다. 원본에 값이 없거나 둘 이상이면 실패한다. 위 `Single.create` 예제를 구독 두 곳에 연결했을 때는 클로저가 두 번 실행됐다. 구독을 공유해야 한다면 공유 여부를 별도로 설계한다.

## 화면 상태와 한 번만 보여 줄 알림

`Driver`와 `Signal`은 RxCocoa에서 화면을 연결할 때 쓰는 Trait다. 두 타입은 오류를 내보내지 않고 메인 스케줄러에서 이벤트를 전달한다. 연결 중인 구독끼리 같은 실행을 공유한다. `Driver`는 활성 연결의 마지막 값을 새 구독자에게 재생한다. `Signal`은 재생할 값을 보관하지 않는다.

| 화면에 보낼 값 | 타입 | 이유 |
| --- | --- | --- |
| 검색 결과 목록, 로딩 아이콘 상태 | `Driver` | 나중에 연결해도 현재 상태가 필요하다 |
| 실패 토스트, 화면 이동 요청 | `Signal` | 지난 이벤트를 새 연결에서 재생할 필요가 없다 |

아래에서 데이터는 `io` 큐에서 준비한다. `drive` 콜백은 메인 스레드에서 받아 출력한다. 이어서 첫 구독을 유지한 채 두 번째 구독을 붙여 재생 차이를 확인한다.

```swift
print("--- 6. Driver: 메인 스레드에서 받는다")
let background = Observable.just("서버 데이터").subscribe(on: io)
    .do(onNext: { _ in print("  만든 곳:", here()) })
background
    .asDriver(onErrorJustReturn: "기본값")
    .drive(onNext: { print("  drive 받은 곳:", here(), $0) })
    .disposed(by: disposeBag)
wait(0.2)

print("--- 8. Driver는 마지막 값을 다시 준다, Signal은 안 준다")
let relay = PublishRelay<String>()
var driverRuns = 0, signalRuns = 0

let driver = relay.do(onNext: { _ in driverRuns += 1 }).asDriver(onErrorJustReturn: "")
let signal = relay.do(onNext: { _ in signalRuns += 1 }).asSignal(onErrorJustReturn: "")
driver.drive(onNext: { print("  driver 구독1:", $0) }).disposed(by: disposeBag)
signal.emit(onNext: { print("  signal 구독1:", $0) }).disposed(by: disposeBag)
relay.accept("토스트: 저장됨")
wait(0.05)
print("  -- 늦게 구독")
driver.drive(onNext: { print("  driver 구독2(늦게):", $0) }).disposed(by: disposeBag)
signal.emit(onNext: { print("  signal 구독2(늦게):", $0) }).disposed(by: disposeBag)
wait(0.05)
print("  driver 쪽 do 실행 횟수:", driverRuns, "/ signal 쪽:", signalRuns)

print("--- 9. BehaviorRelay.asDriver()")
let isLoading = BehaviorRelay<Bool>(value: false)
isLoading.asDriver()
    .drive(onNext: { print("  로딩 표시:", $0) })
    .disposed(by: disposeBag)
isLoading.accept(true)
isLoading.accept(false)
wait(0.05)
```

```text
--- 6. Driver: 메인 스레드에서 받는다
  만든 곳: io
  drive 받은 곳: main 서버 데이터
--- 8. Driver는 마지막 값을 다시 준다, Signal은 안 준다
  driver 구독1: 토스트: 저장됨
  signal 구독1: 토스트: 저장됨
  -- 늦게 구독
  driver 구독2(늦게): 토스트: 저장됨
  driver 쪽 do 실행 횟수: 1 / signal 쪽: 1
--- 9. BehaviorRelay.asDriver()
  로딩 표시: false
  로딩 표시: true
  로딩 표시: false
```

{: .warning }
`asDriver(onErrorJustReturn:)`은 오류가 난 소스를 기본값을 내보내고 완료하는 새 소스로 바꾼다. 계속 검색하려면 각 요청의 오류를 `flatMapLatest` 안에서 처리한다. [Error Handling의 검색 요청 예제]({{ "/swift/rxswift/error-handling/#검색-요청-안에서-오류-처리하기" | relative_url }})에서 복구 위치를 바꾼 결과를 볼 수 있다.

## 검색 뷰모델은 요청을 한 곳에서 시작한다

입력에는 검색어 Observable을 둔다. 화면에는 `users`, `isLoading`, `errorMessage` 세 출력을 건넨다. 실제 앱에서는 네트워크 서비스를 `search`로 전달하고, 테스트에서는 가짜 함수를 전달한다.

다음 파일을 앱이나 라이브러리 타깃에 넣는다. 아래 테스트에서는 모듈 이름이 `RxDemoLib`다.

```swift
import Foundation
import RxSwift
import RxCocoa

public final class SearchViewModel {
    public struct Input {
        public let query: Observable<String>
        public init(query: Observable<String>) { self.query = query }
    }

    public struct Output {
        public let users: Driver<[String]>
        public let isLoading: Driver<Bool>
        public let errorMessage: Signal<String>
    }

    private let search: (String) -> Single<[String]>
    private let scheduler: SchedulerType

    // 검색 함수와 스케줄러를 밖에서 넣는다. 테스트에서 가짜를 넣기 위해서다.
    public init(search: @escaping (String) -> Single<[String]>,
                scheduler: SchedulerType = MainScheduler.instance) {
        self.search = search
        self.scheduler = scheduler
    }

    public func transform(input: Input) -> Output {
        let isLoading = BehaviorRelay<Bool>(value: false)
        let errorMessage = PublishRelay<String>()
        let search = self.search

        let users = input.query
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .debounce(.milliseconds(300), scheduler: scheduler)
            .distinctUntilChanged()
            .flatMapLatest { query -> Observable<[String]> in
                guard !query.isEmpty else { return .just([]) }
                return search(query)
                    .asObservable()
                    .do(onSubscribe: { isLoading.accept(true) },
                        onDispose: { isLoading.accept(false) })
                    .catch { _ in
                        errorMessage.accept("검색에 실패했습니다")
                        return .just([])
                    }
            }
            .asDriver(onErrorJustReturn: [])

        return Output(
            users: users,
            isLoading: isLoading.asDriver().distinctUntilChanged(),
            errorMessage: errorMessage.asSignal()
        )
    }
}
```

한 번의 검색 흐름을 따라가 보자.

1. 검색어 앞뒤의 공백을 자르고, 입력이 300ms 잠잠해질 때까지 기다린다. 직전 검색어와 같으면 다시 요청하지 않는다.
2. 새 검색어가 오면 `flatMapLatest`가 이전 요청의 구독을 해제한다. 검색 기능에서 실제 작업도 취소하려면 소스가 구독 해제를 네트워크 작업의 취소와 묶어야 한다.
3. 빈 검색어에는 바로 빈 목록을 내보낸다. 요청의 구독이 시작되면 로딩을 켠다. 이 예제에서 `onDispose`는 정상 종료, 실패, 새 입력으로 인한 구독 해제 뒤에 로딩을 끈다.
4. 한 검색이 실패하면 알림을 보내고 그 요청의 결과만 빈 목록으로 바꾼다. 다음 검색어는 계속 받는다.
5. `users`를 `Driver`로 만들어 활성 구독끼리 요청을 공유한다. 로딩과 오류 출력은 동일한 검색의 상태를 Relay로 전달한다. 화면에서 이 요청 흐름을 시작하는 구독은 `users.drive`다.

여러 독립 요청을 동시에 실행하도록 설계를 바꾸면 로딩을 단일 Bool로 켜고 끄는 방식에 문제가 생긴다. 요청 하나가 끝날 때 아직 다른 요청이 살아 있을 수 있다. 여기서는 `flatMapLatest`로 활성 요청을 하나로 제한한다.

## UIKit에서 출력 연결하기

아래 코드는 텍스트 입력과 테이블, 로딩 표시, 알림을 연결하는 화면 예시다. UIKit 화면은 실행하지 않았다. 셀을 `UserCell`로 등록하고 뷰가 바인딩을 한 번 만들도록 한다.

```swift
// 실행하지 않음 (UIKit 화면 바인딩)
let input = SearchViewModel.Input(
    query: searchBar.rx.text.orEmpty.asObservable()
)
let output = viewModel.transform(input: input)

output.isLoading
    .drive(activityIndicator.rx.isAnimating)
    .disposed(by: disposeBag)

output.errorMessage
    .emit(onNext: { [weak self] message in
        self?.showToast(message)
    })
    .disposed(by: disposeBag)

output.users
    .drive(tableView.rx.items(cellIdentifier: "UserCell")) { _, name, cell in
        cell.textLabel?.text = name
    }
    .disposed(by: disposeBag)
```

토스트와 로딩을 먼저 연결하면 `users` 구독이 첫 요청을 시작할 때 이미 결과를 받을 구독자가 있다. 화면 안에서 같은 입력으로 `transform`을 다시 호출하면 새 요청 흐름을 만들므로, 한 번 만든 출력을 연결한다.

## RxTest로 화면 없이 검색 검사하기

`TestScheduler`는 테스트에서 시간을 움직인다. 1틱을 1ms로 정하고, 100ms 뒤 응답하는 가짜 검색을 넣는다. 테스트는 사용자가 입력한 시각과 결과를 받은 시각을 각각 기록한다. `SharingScheduler.mock` 안에서는 `Driver`와 `Signal`의 스케줄러도 같은 테스트 시계에 맞춘다.

다음 파일은 XCTest 테스트 타깃에 넣는다. 위의 뷰모델을 같은 타깃에 넣었다면 `import RxDemoLib`를 빼고, 다른 모듈 이름을 쓴다면 해당 이름으로 바꾼다. `describe`를 이미 같은 타깃에 넣었다면 기존 함수를 사용한다.

```swift
import XCTest
import RxSwift
import RxCocoa
import RxTest
import RxBlocking
import RxDemoLib

func describe<T>(_ events: [Recorded<Event<T>>]) -> String {
    events.map { r -> String in
        switch r.value {
        case .next(let v): return "\(r.time):\(v)"
        case .error: return "\(r.time):error"
        case .completed: return "\(r.time):|"
        }
    }.joined(separator: "  ")
}

final class SearchViewModelTests: XCTestCase {
    enum APIError: Error { case offline }
    var scheduler: TestScheduler!
    var disposeBag: DisposeBag!
    var requested: [String]!

    override func setUp() {
        // 1틱 = 1ms. 기본값(1틱 = 1초)이면 .milliseconds(300)이 0틱이 된다.
        scheduler = TestScheduler(initialClock: 0, resolution: 0.001)
        disposeBag = DisposeBag()
        requested = []
    }

    // 가짜 서버: 100ms 뒤에 응답한다. "fail"이면 실패한다.
    func fakeSearch(_ query: String) -> Single<[String]> {
        requested.append(query)
        let all = ["Swift", "SwiftUI", "RxSwift", "Combine"]
        let result: Single<[String]> = query == "fail"
            ? .error(APIError.offline)
            : .just(all.filter { $0.localizedCaseInsensitiveContains(query) })
        return result.delaySubscription(.milliseconds(100), scheduler: scheduler)
    }

    func makeOutput(_ events: [Recorded<Event<String>>]) -> SearchViewModel.Output {
        let query = scheduler.createHotObservable(events)
        let viewModel = SearchViewModel(search: fakeSearch, scheduler: scheduler)
        return viewModel.transform(input: .init(query: query.asObservable()))
    }

    func test_빠르게_입력하면_마지막_검색어로_한번만_요청한다() {
        SharingScheduler.mock(scheduler: scheduler) {
            let output = makeOutput([
                .next(100, "s"), .next(150, "sw"), .next(200, "swi"),
            ])
            let users = scheduler.createObserver([String].self)
            let loading = scheduler.createObserver(Bool.self)
            output.users.drive(users).disposed(by: disposeBag)
            output.isLoading.drive(loading).disposed(by: disposeBag)

            scheduler.start()

            print("요청:", requested!)
            print("users:", describe(users.events))
            print("isLoading:", describe(loading.events))
            XCTAssertEqual(requested, ["swi"])
            XCTAssertEqual(users.events, [.next(601, ["Swift", "SwiftUI", "RxSwift"])])
        }
    }

    func test_실패해도_다음_검색은_된다() {
        SharingScheduler.mock(scheduler: scheduler) {
            let output = makeOutput([
                .next(100, "fail"),
                .next(1000, "rx"),
            ])
            let users = scheduler.createObserver([String].self)
            let errors = scheduler.createObserver(String.self)
            output.users.drive(users).disposed(by: disposeBag)
            output.errorMessage.emit(to: errors).disposed(by: disposeBag)

            scheduler.start()

            print("users:", describe(users.events))
            print("errorMessage:", describe(errors.events))
            XCTAssertEqual(users.events.map(\.value.element), [[], ["RxSwift"]])
        }
    }

    func test_RxBlocking으로_Single_결과_기다리기() throws {
        let background = ConcurrentDispatchQueueScheduler(qos: .default)
        let single = Single.just(["Swift"]).delay(.milliseconds(50), scheduler: background)

        let value = try single.toBlocking(timeout: 1).first()
        print("toBlocking().first():", value as Any)

        let failing = Single<[String]>.error(APIError.offline)
        switch failing.toBlocking().materialize() {
        case .completed(let elements): print("completed:", elements)
        case .failed(let elements, let error): print("failed:", elements, error)
        }
    }
}
```

### 입력이 이어질 때 실제 요청 목록 확인

```text
요청: ["swi"]
users: 601:["Swift", "SwiftUI", "RxSwift"]
isLoading: 1:false  501:true  601:false
```

마지막 입력 200에서 300틱이 지난 500에 검색을 시작하고, 가짜 응답이 600에 준비된다. 이 설정에서 `Driver`가 값을 전달한 시각은 601이다. `requested`를 검사하므로 화면에 최신 값이 보였다는 사실과 실제 요청이 한 번만 시작됐다는 사실을 둘 다 확인할 수 있다.

### 요청이 실패한 뒤 다음 검색 확인

```text
users: 501:[]  1401:["RxSwift"]
errorMessage: 501:검색에 실패했습니다
```

첫 요청은 빈 결과와 오류 메시지를 보냈다. 두 번째 요청은 1401에 `RxSwift`를 보냈다. 요청별로 오류를 잡았으므로 다음 입력도 계속 처리했다.

### RxBlocking으로 한 결과 기다리기

```text
toBlocking().first(): Optional(["Swift"])
failed: [] offline
```

`RxBlocking`은 응답 하나를 기다려 반환하는 식으로 결과를 확인할 때 쓸 수 있다. 위 테스트는 백그라운드에서 전달하는 결과에 1초 제한을 두었다. 화면에서 메인 큐에 전달할 값을 메인 큐에서 차단하며 기다리면 전달을 막을 수 있다. 이벤트 순서나 지연을 확인할 때는 `TestScheduler`로 기록을 비교한다.

## 정리

모델은 요청의 결과 개수를 `Single`, `Maybe`, `Completable`로 표현한다. 뷰모델은 입력을 한 스트림으로 받아 요청을 만들고 화면이 받을 상태와 알림을 내보낸다. 화면은 상태를 `Driver`, 지난 값을 다시 보여 줄 필요가 없는 알림을 `Signal`로 연결한다.

검색 함수와 스케줄러를 바꿀 수 있게 만들면 호출 횟수, 시간, 실패 후 다음 입력까지 화면 없이 검사할 수 있다.

## 참고

- [RxSwift 6.9.1 Traits 문서](https://github.com/ReactiveX/RxSwift/blob/6.9.1/Documentation/Traits.md)
- [RxSwift 6.9.1 단위 테스트 문서](https://github.com/ReactiveX/RxSwift/blob/6.9.1/Documentation/UnitTests.md)
- [RxSwift 6.9.1 예제](https://github.com/ReactiveX/RxSwift/blob/6.9.1/Documentation/Examples.md)
