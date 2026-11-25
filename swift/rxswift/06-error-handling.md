---
title: "Error Handling"
description: "RxSwift에서 catch, retry, retryWhen으로 오류를 복구하고, Result 타입으로 에러를 흐름 안에 담는 패턴을 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 6
permalink: /swift/rxswift/error-handling/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [Swift, RxSwift, Error, catch, retry]
---

# Error Handling
{: .no_toc }

{% include article-toc.md %}

Observable이 `error` 이벤트를 내보내면 시퀀스가 종료된다. 그 이후로는 어떤 `next`도 오지 않는다. 에러가 UI 바인딩까지 올라가면 바인딩이 끊어진다. 에러를 적절한 위치에서 처리하지 않으면 흐름이 조용히 멈춘다.

## error 이벤트가 흐르는 방식

```text
Observable<T>
  ├── next(value)   → 계속 흐른다
  ├── error(Error)  → 시퀀스 종료. 이후 next 없음
  └── completed     → 시퀀스 정상 종료
```

에러가 체인을 따라 올라가다 처리되지 않으면 `subscribe(onError:)`까지 도달한다. 여기서도 처리하지 않으면 에러는 무시된다.

## catch

에러가 발생했을 때 대체 Observable로 전환한다. 시퀀스가 종료되지 않고 대체 값으로 이어진다.

```swift
// catchAndReturn: 에러 발생 시 고정값으로 대체
fetchUser()
    .catchAndReturn(User.anonymous)
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)

// catch: 에러 종류에 따라 다른 Observable로 전환
fetchUser()
    .catch { error in
        if let apiError = error as? APIError, apiError == .notFound {
            return .just(User.anonymous)
        }
        return .error(error)  // 처리 못 하면 다시 에러로
    }
    .subscribe(onNext: { print($0) })
    .disposed(by: disposeBag)
```

`catch` 안에서 다시 `.error(error)`를 반환하면 에러를 위임한다. 모든 에러를 한 곳에서 삼키지 않고 처리 가능한 에러만 복구하는 것이 좋다.

## retry

에러 발생 시 처음부터 다시 구독을 시작한다. 네트워크 요청 일시 실패처럼 재시도로 해결될 수 있는 경우에 쓴다.

```swift
// 최대 3번 재시도
fetchData()
    .retry(3)
    .subscribe(
        onNext:  { print("성공:", $0) },
        onError: { print("3번 모두 실패:", $0) }
    )
    .disposed(by: disposeBag)
```

`retry()`에 횟수를 넘기지 않으면 무한 재시도한다. 에러가 계속 나면 무한 루프가 된다. 반드시 횟수 또는 조건을 지정한다.

## retryWhen

재시도 타이밍을 직접 제어한다. 지수 백오프(exponential backoff) 같은 패턴을 구현할 수 있다.

```swift
fetchData()
    .retryWhen { errors in
        errors.enumerated().flatMap { attempt, error -> Observable<Int> in
            guard attempt < 3 else {
                return Observable.error(error)  // 3번 초과 시 포기
            }
            let delay = Int(pow(2.0, Double(attempt)))  // 1초, 2초, 4초
            print("재시도 \(attempt + 1)회, \(delay)초 후")
            return Observable<Int>.timer(
                .seconds(delay),
                scheduler: MainScheduler.instance
            )
        }
    }
    .subscribe(
        onNext:  { print("성공:", $0) },
        onError: { print("최종 실패:", $0) }
    )
    .disposed(by: disposeBag)
```

## Result 타입으로 에러를 흐름 안에 담기

에러가 Observable 시퀀스를 종료시키지 않도록, `Result<T, Error>` 타입으로 변환해 흐름 안에 담는 패턴이다. UI 바인딩에서 에러가 바인딩을 끊지 않게 하는 가장 안전한 방법이다.

```swift
func safeFetch() -> Observable<Result<User, Error>> {
    return fetchUser()
        .map { Result.success($0) }
        .catch { .just(.failure($0)) }
}

safeFetch()
    .subscribe(onNext: { result in
        switch result {
        case .success(let user): print("유저:", user)
        case .failure(let error): print("에러:", error)
        }
    })
    .disposed(by: disposeBag)
```

이 방식은 에러가 오더라도 `completed`가 아닌 `.next(.failure(error))`로 처리된다. 구독이 끊어지지 않는다.

## materialize / dematerialize

이벤트 자체를 값으로 감싼다. 에러·완료 이벤트도 `next` 로 흘러 로깅이나 디버깅에 유용하다.

```swift
Observable.of(1, 2, 3)
    .concat(Observable.error(URLError(.badURL)))
    .materialize()
    .subscribe(onNext: { event in
        print(event)  // next(1), next(2), next(3), error(...)
    })
    .disposed(by: disposeBag)
```

`dematerialize()`로 다시 원래 이벤트 흐름으로 되돌릴 수 있다.

## 실습: 네트워크 재시도 + 오류 화면

```swift
class FeedViewModel {
    let items: Observable<[FeedItem]>
    let errorMessage: Observable<String>

    init() {
        let result = FeedService.fetchFeed()
            .retry(2)
            .map { Result<[FeedItem], Error>.success($0) }
            .catch { .just(.failure($0)) }
            .share()

        items = result.compactMap {
            if case .success(let items) = $0 { return items }
            return nil
        }

        errorMessage = result.compactMap {
            if case .failure(let error) = $0 {
                return error.localizedDescription
            }
            return nil
        }
    }
}

// ViewController
viewModel.items
    .bind(to: tableView.rx.items(...))
    .disposed(by: disposeBag)

viewModel.errorMessage
    .bind(to: errorLabel.rx.text)
    .disposed(by: disposeBag)
```

`retry(2)`로 2번 재시도하고, 실패하면 `Result.failure`로 감싸 흐름을 유지한다. 뷰모델에서 items와 errorMessage를 분리해 뷰가 각각 바인딩한다.

## 정리

| 방법 | 동작 | 적합한 상황 |
| --- | --- | --- |
| `catchAndReturn` | 에러를 고정값으로 대체 | 기본값이 있는 경우 |
| `catch` | 에러에 따라 다른 Observable로 전환 | 에러별 복구 로직 |
| `retry(n)` | n번 재구독 | 일시적 네트워크 실패 |
| `retryWhen` | 조건·시간 제어 재시도 | 지수 백오프 |
| `Result<T, E>` | 에러를 값으로 담기 | UI 바인딩 안정성 |

다음에는 RxSwift를 MVVM 패턴과 함께 쓰는 [MVVM + RxSwift]({{ "/swift/rxswift/mvvm/" | relative_url }})를 살펴본다.

## 참고

- [ReactiveX: Error Handling Operators](https://reactivex.io/documentation/operators.html#error)
- [RxSwift GitHub: Error Handling](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/GettingStarted.md#error-handling)
