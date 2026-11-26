---
title: "Error Handling"
description: "실패한 RxSwift 요청을 catch로 복구하고, retry의 시도 횟수와 지수 백오프를 실제 출력과 가상 시간 테스트로 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 6
permalink: /swift/rxswift/error-handling/
last_modified_at: 2026-11-26
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-26
tags: [Swift, RxSwift, Error, catch, retry]
---

# Error Handling
{: .no_toc }

{% include article-toc.md %}

검색창에 `swift`, `error`, `rxswift`를 차례로 넣었다. 두 번째 요청에서 서버 오류를 내자 마지막 검색은 시작되지 않았다. 한 번의 요청이 끝난 것과 입력을 받는 스트림이 끝난 것을 구분하면 어디에서 오류를 잡아야 하는지 알 수 있다.

```text
검색어          swift          error       rxswift
복구 없는 결과   swift 결과     X           (입력을 받지 않음)
요청별로 복구    swift 결과     검색 실패   rxswift 결과
```

`X`는 오류 이벤트다. Observable 구독은 오류를 끝 이벤트로 받고, 그 뒤에는 값을 받지 않는다. 아래 코드는 RxSwift 6.9.1, Swift 6.0.3으로 실행했다. 공통 코드부터 순서대로 붙인다.

```swift
import Foundation
import RxSwift

let disposeBag = DisposeBag()
enum APIError: Error { case notFound, server }
struct User: CustomStringConvertible { let name: String; var description: String { name }
    static let anonymous = User(name: "익명") }

func fetchUser(_ result: Result<User, APIError>) -> Observable<User> {
    Observable.create { o in
        switch result {
        case .success(let u): o.onNext(u); o.onCompleted()
        case .failure(let e): o.onError(e)
        }
        return Disposables.create()
    }
}
func log<T>(_ tag: String) -> (Event<T>) -> Void {
    { e in
        switch e {
        case .next(let v): print("\(tag) next:", v)
        case .error(let err): print("\(tag) error:", err)
        case .completed: print("\(tag) completed")
        }
    }
}
```

## catch로 오류를 복구할 범위 정하기

`catch`는 실패한 소스에서 대체 Observable로 바꾼다. 대체 Observable이 값 하나를 내보내고 완료했다면 구독자도 그 값을 받고 완료된다. 첫 번째 예제는 오류를 그대로 받는다. 두 번째는 고정값으로 바꾸고, 세 번째는 `notFound`에만 익명 사용자를 반환한다.

```swift
print("--- 1. 아무 처리 없이 error가 오면")
fetchUser(.failure(.server)).subscribe(log("기본")).disposed(by: disposeBag)

print("--- 2. catchAndReturn")
fetchUser(.failure(.server)).catchAndReturn(.anonymous).subscribe(log("catchAndReturn")).disposed(by: disposeBag)

print("--- 3. catch: 고칠 수 있는 에러만 고친다")
for e in [APIError.notFound, .server] {
    fetchUser(.failure(e))
        .catch { error in
            if case APIError.notFound = error { return .just(.anonymous) }
            return .error(error)
        }
        .subscribe(log("catch(\(e))"))
        .disposed(by: disposeBag)
}
```

```text
--- 1. 아무 처리 없이 error가 오면
기본 error: server
--- 2. catchAndReturn
catchAndReturn next: 익명
catchAndReturn completed
--- 3. catch: 고칠 수 있는 에러만 고친다
catch(notFound) next: 익명
catch(notFound) completed
catch(server) error: server
```

이때 `catchAndReturn(.anonymous)`은 익명 사용자와 완료를 내보냈다. 값이 하나인 대체 소스라서 그렇다. `catch`에서 `.error(error)`를 반환한 경우에는 구독자가 그대로 오류를 받는다.

## retry의 숫자는 전체 시도 횟수

`retry(3)`을 쓰면 첫 구독을 포함해 최대 세 번 구독한다. 실패가 두 번까지 이어져도 세 번째 시도에서 성공할 수 있다.

```swift
print("--- 4. retry(3)은 '총 3번 시도'다")
var attempt = 0
let flaky = Observable<String>.create { o in
    attempt += 1
    print("  시도 #\(attempt)")
    o.onError(APIError.server)
    return Disposables.create()
}
flaky.retry(3).subscribe(log("retry(3)")).disposed(by: disposeBag)

print("--- 5. 세 번째에 성공하는 요청")
var tries = 0
let thirdTime = Observable<String>.create { o in
    tries += 1
    print("  시도 #\(tries)")
    if tries < 3 { o.onError(APIError.server) } else { o.onNext("성공 데이터"); o.onCompleted() }
    return Disposables.create()
}
thirdTime.retry(3).subscribe(log("retry")).disposed(by: disposeBag)
```

```text
--- 4. retry(3)은 '총 3번 시도'다
  시도 #1
  시도 #2
  시도 #3
retry(3) error: server
--- 5. 세 번째에 성공하는 요청
  시도 #1
  시도 #2
  시도 #3
retry next: 성공 데이터
retry completed
```

{: .warning }
`retry()`에 횟수를 주지 않으면 오류가 날 때마다 다시 구독한다. 네트워크 재시도에는 실패 조건과 횟수 한도를 정한다. 요청이 이미 서버에 적용됐는지 알 수 없는 상황에서 쓰기 작업을 다시 보내면 중복 처리될 수 있다.

다시 구독할 때 요청을 새로 시작하려면 `Observable.create`나 `Observable.deferred` 안에서 작업을 시작한다. 소스가 이미 일어난 이벤트를 전달하는 Subject라면 재구독한다고 이전 요청이 다시 시작되지는 않는다.

## 실패 사이에 기다리기

`retry(when:)`은 오류 Observable을 받아 재시도 시점을 정하게 한다. 반환한 Observable이 다음 값을 내보내면 원본을 다시 구독한다. 완료하면 시퀀스도 완료하고, 오류를 내보내면 그 오류를 전달하고 끝난다.

실패 후 대기 시간을 10틱, 20틱, 40틱으로 늘리는 방법을 **지수 백오프(exponential backoff)**라고 부른다. 아래 테스트는 요청이 매번 5틱 뒤 응답한다고 가정한다. 코드는 XCTest 타깃에 넣는다. 같은 타깃에 `describe`가 있으면 기존 함수를 사용한다. 첫 시도 외에 최대 세 번 다시 구독한다. 현재 API 이름은 `retry(when:)`이고, 후행 클로저로 적으면 `retry { ... }`가 된다.

```swift
import Foundation
import XCTest
import RxSwift
import RxTest

func describe<T>(_ events: [Recorded<Event<T>>]) -> String {
    events.map { r -> String in
        switch r.value {
        case .next(let v): return "\(r.time):\(v)"
        case .error: return "\(r.time):error"
        case .completed: return "\(r.time):|"
        }
    }.joined(separator: "  ")
}

final class P6Tests: XCTestCase {
    enum APIError: Error { case server }

    func testExponentialBackoff() {
        let scheduler = TestScheduler(initialClock: 0)
        var attempts: [Int] = []
        let request = Observable<String>.deferred {
            attempts.append(scheduler.clock)
            // 실제 네트워크처럼 5틱 걸린다. 네 번째 시도에서 성공한다.
            let result: Observable<String> = attempts.count < 4 ? .error(APIError.server) : .just("성공")
            return result.delaySubscription(.seconds(5), scheduler: scheduler)
        }
        let res = scheduler.start(created: 0, subscribed: 0, disposed: 1000) {
            request.retry { errors in
                errors.enumerated().flatMap { index, error -> Observable<Int> in
                    guard index < 3 else { return .error(error) }
                    let delay = 10 * Int(pow(2.0, Double(index)))   // 10, 20, 40틱
                    return Observable<Int>.timer(.seconds(delay), scheduler: scheduler)
                }
            }
        }
        print("시도한 시각:", attempts)
        print("결과:", describe(res.events))
    }

    func testBackoffGivesUp() {
        let scheduler = TestScheduler(initialClock: 0)
        var attempts: [Int] = []
        let request = Observable<String>.deferred {
            attempts.append(scheduler.clock)
            // 실제 네트워크처럼 5틱 뒤에 실패한다
            return Observable<String>.error(APIError.server)
                .delaySubscription(.seconds(5), scheduler: scheduler)
        }
        let res = scheduler.start(created: 0, subscribed: 0, disposed: 1000) {
            request.retry { errors in
                errors.enumerated().flatMap { index, error -> Observable<Int> in
                    guard index < 3 else { return .error(error) }
                    return Observable<Int>.timer(.seconds(10 * Int(pow(2.0, Double(index)))), scheduler: scheduler)
                }
            }
        }
        print("시도한 시각:", attempts)
        print("결과:", describe(res.events))
    }
}
```

```text
시도한 시각: [0, 15, 40, 85]
결과: 90:error
시도한 시각: [0, 15, 40, 85]
결과: 90:성공  90:|
```

첫 시도는 0에 시작해 5에 끝난다. 10틱을 기다려 15에 두 번째 시도를 한다. 같은 계산을 반복하면 세 번째는 40, 네 번째는 85에 시작한다. 네 번째 응답이 오는 90틱에 결과가 결정된다.

## 검색 요청 안에서 오류 처리하기

`flatMapLatest`의 안쪽은 한 검색어에 대한 요청이다. 바깥쪽은 계속 들어오는 검색어다. 안쪽 오류가 바깥으로 올라오면 검색어를 받던 구독도 끝난다.

```swift
print("--- 6. 흔한 실수: flatMap 안의 에러가 바깥 흐름을 끝낸다")
func search(_ q: String) -> Observable<String> {
    q == "error" ? .error(APIError.server) : .just("\(q) 결과")
}
do {
    let query = PublishSubject<String>()
    query.flatMapLatest { search($0) }
        .subscribe(log("검색"))
        .disposed(by: disposeBag)
    query.onNext("swift")
    query.onNext("error")
    query.onNext("rxswift")   // 이미 끝난 뒤라 아무 일도 없다
}

print("--- 7. 고친 코드: 안쪽에서 에러를 잡는다")
do {
    let query = PublishSubject<String>()
    query.flatMapLatest { q in
            search(q).catchAndReturn("검색 실패")
        }
        .subscribe(log("검색"))
        .disposed(by: disposeBag)
    query.onNext("swift")
    query.onNext("error")
    query.onNext("rxswift")
}
```

```text
--- 6. 흔한 실수: flatMap 안의 에러가 바깥 흐름을 끝낸다
검색 next: swift 결과
검색 error: server
--- 7. 고친 코드: 안쪽에서 에러를 잡는다
검색 next: swift 결과
검색 next: 검색 실패
검색 next: rxswift 결과
```

실패를 복구한 위치가 다르다. 두 번째 구독은 안쪽 요청이 실패하면 그 요청만 `검색 실패`로 바꾼다. 바깥쪽 검색어 스트림은 계속 다음 입력을 받는다.

## 실패 정보를 값에 담기

화면에 오류를 표시하면서 다음 검색도 계속 받아야 한다면 `Result`를 선택할 수 있다. 정상 응답은 `.success`, 실패는 `.failure`로 담아 둘 다 `next`로 전달한다.

```swift
print("--- 8. Result로 감싸기")
do {
    let query = PublishSubject<String>()
    query.flatMapLatest { q in
            search(q)
                .map { Result<String, Error>.success($0) }
                .catch { .just(.failure($0)) }
        }
        .subscribe(onNext: { result in
            switch result {
            case .success(let text): print("성공:", text)
            case .failure(let error): print("실패:", error)
            }
        })
        .disposed(by: disposeBag)
    query.onNext("swift")
    query.onNext("error")
    query.onNext("rxswift")
}
```

```text
--- 8. Result로 감싸기
성공: swift 결과
실패: server
성공: rxswift 결과
```

{: .tip }
검색 결과와 오류 표시를 나눠 그릴 때는 먼저 한 요청에서 결과를 만들고 공유한다. 화면 출력마다 요청을 새로 만들면 같은 검색어로 서버를 한 번 더 호출한다. [MVVM + RxSwift]({{ "/swift/rxswift/mvvm/" | relative_url }})에서 검색 출력과 실패 알림을 연결한다.

## 종료 이벤트를 값으로 살펴보기

`materialize()`는 `next`, 오류, 완료를 각각 `Event` 값으로 감싼다. 예제의 `error(server)`는 구독에서 받은 값의 문자열이다. 이를 전달한 뒤 바깥 시퀀스는 완료된다. `dematerialize()`로 다시 풀면 원래의 오류와 완료가 복원된다.

```swift
print("--- 9. materialize")
Observable.of(1, 2)
    .concat(Observable.error(APIError.server))
    .materialize()
    .subscribe(onNext: { print($0) }, onCompleted: { print("(materialize 결과의) completed") })
    .disposed(by: disposeBag)

print("--- 10. do(onError:)는 보기만 하고 고치지 않는다")
fetchUser(.failure(.server))
    .do(onError: { print("  로그 남김:", $0) })
    .catchAndReturn(.anonymous)
    .subscribe(log("do"))
    .disposed(by: disposeBag)

print("--- 11. onError 없이 구독했는데 error가 오면")
fetchUser(.failure(.server))
    .subscribe(onNext: { print("next:", $0) })
    .disposed(by: disposeBag)
print("(다음 줄)")
```

```text
--- 9. materialize
next(1)
next(2)
error(server)
(materialize 결과의) completed
--- 10. do(onError:)는 보기만 하고 고치지 않는다
  로그 남김: server
do next: 익명
do completed
--- 11. onError 없이 구독했는데 error가 오면
Unhandled error happened: server
(다음 줄)
```

`do(onError:)`에서는 오류를 보고 로그를 남길 수 있다. 위 코드에서는 `catchAndReturn`이 복구를 맡는다. `onError`를 생략한 구독은 기본 오류 핸들러로 오류를 보낸다. 위 출력의 `Unhandled error happened`는 이번 실행 환경에서 기본 핸들러가 남긴 로그다.

## 정리

| 하고 싶은 일 | 연산자 |
| --- | --- |
| 정해 둔 기본값을 보내고 끝내기 | `catchAndReturn` |
| 오류 종류를 보고 다음 소스를 고르기 | `catch` |
| 전체 시도 횟수를 제한하기 | `retry(_:)` |
| 조건이나 대기 시간에 따라 다시 구독하기 | `retry(when:)` |
| 값이나 실패 정보를 모두 화면에 전달하기 | `Result`를 `next`로 보내기 |
| 종료 이벤트까지 값으로 관찰하기 | `materialize()` |

다음에는 [MVVM + RxSwift]({{ "/swift/rxswift/mvvm/" | relative_url }})에서 검색 화면을 만들고 실패한 뒤 다음 검색이 동작하는지 테스트한다.

## 참고

- [RxSwift ObservableType 연산자 문서](https://docs.rxswift.org/protocols/observabletype)
- [RxSwift 6.9.1 RetryWhen 구현](https://github.com/ReactiveX/RxSwift/blob/6.9.1/RxSwift/Observables/RetryWhen.swift)
- [RxSwift Error Handling](https://github.com/ReactiveX/RxSwift/blob/6.9.1/Documentation/GettingStarted.md#error-handling)
