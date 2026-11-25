---
title: "Scheduler"
description: "subscribeOn과 observeOn으로 RxSwift의 작업 스레드와 결과 수신 스레드를 분리하는 방법, 주요 Scheduler 종류를 설명합니다."
parent: RxSwift
grand_parent: Swift
nav_order: 5
permalink: /swift/rxswift/scheduler/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [Swift, RxSwift, Scheduler, Thread, MainScheduler]
---

# Scheduler
{: .no_toc }

{% include article-toc.md %}

네트워크 요청이나 파일 읽기를 메인 스레드에서 하면 UI가 멈춘다. 결과를 백그라운드에서 받으면 UI를 업데이트할 수 없다. RxSwift에서는 `Scheduler`로 작업과 결과 수신의 실행 맥락을 선언적으로 지정한다.

## subscribeOn과 observeOn

두 연산자가 실행 위치를 결정한다.

| 연산자 | 역할 |
| --- | --- |
| `subscribeOn` | Observable이 **구독될 때** 실행되는 스레드 지정 (보통 작업 스레드) |
| `observeOn` | 이후 연산자와 구독자가 실행될 스레드 지정 (보통 메인 스레드) |

```swift
fetchData()                                            // 어떤 스레드든
    .subscribeOn(ConcurrentDispatchQueueScheduler(qos: .background))  // 여기서 실행
    .map { parse($0) }                                 // 백그라운드에서
    .observeOn(MainScheduler.instance)                 // 이후는 메인 스레드
    .subscribe(onNext: { self.updateUI($0) })          // 메인에서 UI 업데이트
    .disposed(by: disposeBag)
```

`subscribeOn`은 체인 어디에 있어도 구독 시작 스레드에만 영향을 준다. `observeOn`은 선언한 위치 이후의 연산자에 영향을 준다.

## 주요 Scheduler

| Scheduler | 설명 | 주요 용도 |
| --- | --- | --- |
| `MainScheduler.instance` | 메인 스레드 (직렬) | UI 업데이트 |
| `MainScheduler.asyncInstance` | 메인 스레드 (비동기) | 현재 메인에서 호출해도 다음 런루프에서 |
| `SerialDispatchQueueScheduler` | 직렬 큐 | 순서 보장이 필요한 백그라운드 |
| `ConcurrentDispatchQueueScheduler` | 동시 큐 | 병렬 처리 (파싱, 계산) |
| `OperationQueueScheduler` | OperationQueue | 의존성·취소 제어 |
| `TestScheduler` | 가상 시간 | 단위 테스트에서 시간 제어 |

## 가장 흔한 패턴

```swift
// 네트워크 요청 → 파싱 → UI 업데이트
NetworkService.fetch(url: url)
    .subscribeOn(ConcurrentDispatchQueueScheduler(qos: .userInitiated))
    .map { try JSONDecoder().decode(Response.self, from: $0) }
    .observeOn(MainScheduler.instance)
    .subscribe(
        onNext:  { [weak self] in self?.render($0) },
        onError: { [weak self] in self?.showError($0) }
    )
    .disposed(by: disposeBag)
```

`map`까지는 백그라운드 큐에서 실행한다. `observeOn` 이후의 `subscribe`는 메인 스레드에서 실행한다.

## observeOn 위치에 따른 차이

```swift
observable
    .map { heavyWork($0) }     // 어느 스레드?
    .observeOn(MainScheduler.instance)
    .map { lightWork($0) }     // 메인 스레드
    .subscribe(onNext: { ... }) // 메인 스레드
```

`observeOn` **앞**의 `map`은 이전 스레드(subscribeOn이나 소스의 스레드)에서 실행된다. **뒤**의 `map`과 subscribe는 MainScheduler에서 실행된다. 무거운 작업은 observeOn 앞에 두어야 UI 스레드 점유를 막을 수 있다.

## 메인 스레드에서 이미 실행 중일 때

`MainScheduler.instance`는 현재 이미 메인 스레드라면 동기적으로 즉시 실행한다. 재진입을 허용한다. `MainScheduler.asyncInstance`는 항상 다음 런루프에 예약한다.

```swift
// 주의: 메인에서 MainScheduler.instance로 observeOn하면
// subscribe 클로저가 같은 콜 스택에서 즉시 실행될 수 있다.
// 순환 의존이 있으면 문제가 생길 수 있으므로 의식적으로 사용한다.
```

## 단위 테스트에서의 TestScheduler

`TestScheduler`는 가상 시간을 제어해 `debounce`, `delay`, `interval` 같은 시간 의존 Operator를 실제 시간 없이 테스트한다.

```swift
import RxTest

let scheduler = TestScheduler(initialClock: 0)
let observer  = scheduler.createObserver(Int.self)

let source = scheduler.createHotObservable([
    .next(100, 1),
    .next(200, 2),
    .next(300, 3),
    .completed(400)
])

source
    .delay(.milliseconds(50), scheduler: scheduler)
    .subscribe(observer)
    .disposed(by: disposeBag)

scheduler.start()

XCTAssertEqual(observer.events, [
    .next(150, 1),
    .next(250, 2),
    .next(350, 3),
    .completed(450)
])
```

실제 0.05초를 기다리지 않고 가상 시간 50틱으로 테스트한다.

## 실습: 이미지 비동기 로드

```swift
func loadImage(url: URL) -> Observable<UIImage?> {
    return Observable.create { observer in
        let task = URLSession.shared.dataTask(with: url) { data, _, error in
            if let error = error {
                observer.onError(error)
                return
            }
            observer.onNext(data.flatMap { UIImage(data: $0) })
            observer.onCompleted()
        }
        task.resume()
        return Disposables.create { task.cancel() }
    }
}

loadImage(url: imageURL)
    .subscribeOn(ConcurrentDispatchQueueScheduler(qos: .background))
    .observeOn(MainScheduler.instance)
    .subscribe(
        onNext:  { [weak self] in self?.imageView.image = $0 },
        onError: { print("이미지 로드 실패:", $0) }
    )
    .disposed(by: disposeBag)
```

URLSession 콜백 자체는 URLSession 내부 큐에서 실행되지만, `subscribeOn`으로 구독 시작 스레드를 명시적으로 백그라운드로 지정한다. `observeOn`으로 UI 업데이트는 메인 스레드에서 한다.

## 정리

- `subscribeOn`: Observable **실행** 스레드를 지정한다. 체인 어디에 있든 구독 시작에만 영향을 준다.
- `observeOn`: **이후** Operator와 구독자의 실행 스레드를 지정한다. 선언 위치가 중요하다.
- 무거운 작업은 `ConcurrentDispatchQueueScheduler`, UI 업데이트는 `MainScheduler.instance`가 기본 조합이다.

다음에는 오류를 복구하고 재시도하는 [Error Handling]({{ "/swift/rxswift/error-handling/" | relative_url }})을 살펴본다.

## 참고

- [RxSwift: Scheduler](https://reactivex.io/documentation/scheduler.html)
- [RxSwift GitHub: Schedulers](https://github.com/ReactiveX/RxSwift/blob/main/Documentation/Schedulers.md)
