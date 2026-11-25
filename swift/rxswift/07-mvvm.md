---
title: "MVVM + RxSwift"
description: "Input/Output 구조로 뷰모델을 설계하고, RxSwift로 뷰와 뷰모델을 바인딩하는 전체 패턴을 예제로 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 7
permalink: /swift/rxswift/mvvm/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [Swift, RxSwift, MVVM, Architecture, iOS]
---

# MVVM + RxSwift
{: .no_toc }

{% include article-toc.md %}

앞에서 살펴본 Observable, Operator, Subject, Scheduler, Error Handling을 하나의 패턴으로 조립한다. MVVM에서 뷰모델은 뷰의 상태를 관리하고 비즈니스 로직을 담는다. RxSwift로 뷰와 뷰모델을 바인딩하면 상태 변화가 자동으로 UI에 반영된다.

## MVVM의 역할 분리

```text
View (ViewController)
  ↓ 사용자 입력 (버튼 탭, 텍스트 입력)
ViewModel
  ↓ 비즈니스 로직, 상태 관리
Model (Service, Repository)
```

- **View**: UI 렌더링과 사용자 이벤트 전달만 담당한다. 로직이 없다.
- **ViewModel**: View로부터 Input을 받아 처리하고, Output을 Observable로 내보낸다. UIKit을 import하지 않는다.
- **Model**: 데이터와 비즈니스 규칙. 네트워크, 데이터베이스 접근.

## Input / Output 구조

뷰모델의 인터페이스를 `Input`과 `Output`으로 명시적으로 분리하는 패턴이다.

```swift
protocol ViewModelType {
    associatedtype Input
    associatedtype Output

    func transform(input: Input) -> Output
}
```

뷰컨트롤러는 Input을 만들어 뷰모델에 전달하고, Output을 받아 바인딩한다.

## 예제: 사용자 검색 화면

화면 구성:
- 검색 텍스트필드
- 검색 결과 테이블뷰
- 로딩 인디케이터
- 에러 레이블

### Model

```swift
struct User: Decodable {
    let id: Int
    let login: String
    let avatarUrl: String
}

class UserService {
    static func search(query: String) -> Observable<[User]> {
        guard !query.isEmpty else { return .just([]) }
        let url = URL(string: "https://api.github.com/search/users?q=\(query)")!
        return URLSession.shared.rx.data(request: URLRequest(url: url))
            .map { try JSONDecoder().decode(SearchResponse.self, from: $0).items }
    }
}

struct SearchResponse: Decodable {
    let items: [User]
}
```

### ViewModel

```swift
class SearchViewModel: ViewModelType {

    struct Input {
        let query: Observable<String>
        let refresh: Observable<Void>
    }

    struct Output {
        let users: Observable<[User]>
        let isLoading: Observable<Bool>
        let errorMessage: Observable<String>
    }

    func transform(input: Input) -> Output {
        let isLoading = BehaviorRelay<Bool>(value: false)

        let result = input.query
            .debounce(.milliseconds(300), scheduler: MainScheduler.instance)
            .distinctUntilChanged()
            .do(onNext: { _ in isLoading.accept(true) })
            .flatMapLatest { query in
                UserService.search(query: query)
                    .do(onNext: { _ in isLoading.accept(false) })
                    .catch { error in
                        isLoading.accept(false)
                        return .just([])
                    }
            }
            .share(replay: 1)

        let users = result.map { $0 }

        let errorMessage = input.query
            .flatMapLatest { query in
                UserService.search(query: query)
                    .map { _ in "" }
                    .catch { Observable.just($0.localizedDescription) }
            }

        return Output(
            users: users,
            isLoading: isLoading.asObservable(),
            errorMessage: errorMessage
        )
    }
}
```

### ViewController

```swift
class SearchViewController: UIViewController {

    @IBOutlet weak var searchBar: UISearchBar!
    @IBOutlet weak var tableView: UITableView!
    @IBOutlet weak var activityIndicator: UIActivityIndicatorView!
    @IBOutlet weak var errorLabel: UILabel!

    private let viewModel = SearchViewModel()
    private let disposeBag = DisposeBag()

    override func viewDidLoad() {
        super.viewDidLoad()
        bind()
    }

    private func bind() {
        // Input 구성
        let input = SearchViewModel.Input(
            query: searchBar.rx.text.orEmpty.asObservable(),
            refresh: Observable.never()  // 당겨서 새로고침은 추후 연결
        )

        // Transform → Output
        let output = viewModel.transform(input: input)

        // Output 바인딩
        output.users
            .observeOn(MainScheduler.instance)
            .bind(to: tableView.rx.items(cellIdentifier: "UserCell")) { _, user, cell in
                cell.textLabel?.text = user.login
            }
            .disposed(by: disposeBag)

        output.isLoading
            .observeOn(MainScheduler.instance)
            .bind(to: activityIndicator.rx.isAnimating)
            .disposed(by: disposeBag)

        output.errorMessage
            .observeOn(MainScheduler.instance)
            .map { $0.isEmpty ? true : false }
            .bind(to: errorLabel.rx.isHidden)
            .disposed(by: disposeBag)

        output.errorMessage
            .observeOn(MainScheduler.instance)
            .bind(to: errorLabel.rx.text)
            .disposed(by: disposeBag)

        // 셀 선택
        tableView.rx.modelSelected(User.self)
            .subscribe(onNext: { [weak self] user in
                self?.navigateToDetail(user: user)
            })
            .disposed(by: disposeBag)
    }

    private func navigateToDetail(user: User) {
        // 상세 화면 이동
    }
}
```

## share(replay:)가 필요한 이유

`result`를 `users`와 `errorMessage` 두 곳에서 구독하면 `UserService.search`가 두 번 실행된다. `share(replay: 1)`은 하나의 실행 결과를 여러 구독자에게 공유한다.

```swift
// share 없이
let result = searchQuery.flatMapLatest { UserService.search($0) }
result.bind(to: tableView...)    // 네트워크 요청 1번
result.bind(to: errorLabel...)   // 네트워크 요청 1번 더 ← 2번 요청

// share(replay: 1)
let result = searchQuery.flatMapLatest { UserService.search($0) }.share(replay: 1)
result.bind(to: tableView...)    // 공유된 결과 사용
result.bind(to: errorLabel...)   // 같은 결과 사용 ← 1번 요청
```

## 테스트하기

Input/Output 구조는 ViewController 없이 뷰모델을 단독으로 테스트하기 쉽다.

```swift
import RxTest

class SearchViewModelTests: XCTestCase {
    var scheduler: TestScheduler!
    var disposeBag: DisposeBag!

    override func setUp() {
        scheduler = TestScheduler(initialClock: 0)
        disposeBag = DisposeBag()
    }

    func test_빈쿼리_결과없음() {
        let viewModel = SearchViewModel()
        let queryEvents = scheduler.createHotObservable([
            .next(100, ""),
            .next(200, "yep")
        ])

        let input = SearchViewModel.Input(
            query: queryEvents.asObservable(),
            refresh: Observable.never()
        )
        let output = viewModel.transform(input: input)
        let observer = scheduler.createObserver([User].self)

        output.users
            .bind(to: observer)
            .disposed(by: disposeBag)

        scheduler.start()

        // 빈 쿼리 → 빈 배열
        XCTAssertEqual(observer.events.first?.value.element?.count, 0)
    }
}
```

ViewController를 띄우지 않고 Input을 주입해 Output을 검증한다. UI가 없어도 로직을 검증할 수 있다.

## 정리

RxSwift + MVVM의 핵심은 단방향 데이터 흐름이다.

```text
View (Input) → ViewModel.transform() → Observable (Output) → View 바인딩
```

ViewModel은 UIKit 없이 Input → Output 변환만 한다. View는 Input을 만들고 Output을 바인딩한다. 이 분리 덕분에 뷰모델을 단독으로 테스트할 수 있고, 뷰 교체(UIKit → SwiftUI)도 뷰모델 수정 없이 가능해진다.

## 참고

- [RxSwift Community: MVVM Pattern](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/Examples.md)
- [RxSwift: RxCocoa Traits](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/Traits.md)
