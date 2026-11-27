---
title: "Swift 오류 처리"
description: "Swift의 throws·try·do-catch로 실패를 표현하고 처리하는 방법, 오류 타입 설계, try?와 try!, Result, 타입이 정해진 throws(typed throws), defer, 오류를 어느 계층에서 처리할지 기준을 예제로 설명합니다."
parent: Swift
nav_order: 8
permalink: /swift/error-handling/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Swift, Error, throws, Result]
---

# Swift 오류 처리
{: .no_toc }

{% include article-toc.md %}

회원가입에서 이메일 형식이 틀렸거나, 서버가 응답하지 않거나, 저장 공간이 부족할 수 있다. 실패할 수 있는 작업을 `nil`이나 `-1`로만 알리면 호출하는 쪽은 **왜** 실패했는지 모르고, 실패를 확인하는 것을 잊어도 컴파일러가 알려 주지 않는다. Swift는 실패를 **타입 시스템**에 올려 이 문제를 푼다.

이 글을 쓴 환경에는 Swift 툴체인이 없어 예제를 직접 실행하지 못했다. 주석의 출력은 코드에서 결정되는 값이다.

## 오류 정의하기

오류는 `Error` 프로토콜을 따르는 타입이다. 보통 열거형으로 실패 이유를 나열한다.

```swift
enum SignUpError: Error {
    case invalidEmail(String)
    case passwordTooShort(minimum: Int)
    case alreadyRegistered
}
```

연관 값(`String`, `minimum: Int`)에 실패에 대한 정보를 담을 수 있다. 사용자에게 보여 줄 문장이 필요하면 `LocalizedError`를 따르게 해 `errorDescription`을 구현한다.

## throws, try, do-catch

```swift
func signUp(email: String, password: String) throws -> String {
    guard email.contains("@") else {
        throw SignUpError.invalidEmail(email)
    }
    guard password.count >= 8 else {
        throw SignUpError.passwordTooShort(minimum: 8)
    }
    return "가입 완료: \(email)"
}
```

| 키워드 | 쓰는 곳 | 뜻 |
| --- | --- | --- |
| `throws` | 함수 선언 | 이 함수는 실패할 수 있다 |
| `throw` | 함수 안 | 실패를 알리고 즉시 빠져나간다 |
| `try` | 호출하는 곳 | 실패할 수 있는 호출임을 표시 |
| `do-catch` | 호출하는 곳 | 실패를 받아 처리한다 |

```swift
do {
    let message = try signUp(email: "kim", password: "12345678")
    print(message)
} catch SignUpError.invalidEmail(let email) {
    print("이메일 형식이 아닙니다: \(email)")
} catch SignUpError.passwordTooShort(let minimum) {
    print("비밀번호는 \(minimum)자 이상이어야 합니다")
} catch {
    print("알 수 없는 오류: \(error)")
}
// 이메일 형식이 아닙니다: kim
```

`throws` 함수를 `try` 없이 부르면 컴파일 오류가 난다. 실패 가능성을 무시하고 넘어갈 수 없다. 마지막 `catch`는 위에서 걸러지지 않은 모든 오류를 받으며, 그 안에서는 `error`라는 이름으로 오류를 쓸 수 있다.

처리하지 않고 위로 넘기고 싶다면 호출하는 함수도 `throws`로 선언하고 `try`만 쓰면 된다. 오류는 처리할 수 있는 계층까지 올라간다.

## try?와 try!

| 형태 | 실패하면 | 언제 쓰나 |
| --- | --- | --- |
| `try` | 오류가 위로 전달되거나 `catch`로 간다 | 기본 |
| `try?` | 결과가 `nil`이 된다 (오류 정보는 버려진다) | 실패 이유가 중요하지 않을 때 |
| `try!` | 앱이 즉시 종료된다 | 실패가 절대 일어날 수 없다고 증명할 수 있을 때만 |

```swift
let result = try? signUp(email: "kim@example.com", password: "123")
print(result as Any)   // nil (비밀번호가 짧아 실패했지만 이유는 알 수 없다)
```

`try?`는 편하지만 실패 이유를 버린다. 로그를 남겨야 하거나 사용자에게 이유를 알려야 하는 곳에서 쓰면 문제를 찾기 어려워진다. `try!`는 [Optional의 강제 언래핑 `!`]({{ '/swift/swift-optional/' | relative_url }})처럼, 앱 번들에 들어 있는 고정 파일을 읽는 경우처럼 실패가 곧 개발자 실수인 곳에만 쓴다.

## 정리 코드는 defer로

함수가 성공하든 실패하든 반드시 해야 하는 정리 작업이 있다. 파일 닫기, 잠금 해제, 로딩 표시 끄기 같은 것이다.

```swift
func loadProfile() throws -> String {
    print("로딩 시작")
    defer { print("로딩 끝") }    // 함수를 빠져나갈 때 항상 실행된다

    throw SignUpError.alreadyRegistered
}

_ = try? loadProfile()
// 로딩 시작
// 로딩 끝
```

`defer` 블록은 `return`으로 끝나든 `throw`로 끝나든 현재 범위를 빠져나갈 때 실행된다. 정리 코드를 모든 `return`과 `catch`마다 반복할 필요가 없다.

## Result: 오류를 값으로 담기

`Result<Success, Failure>`는 성공 값이나 오류 중 하나를 담는 열거형이다. 오류를 바로 던지지 않고 값으로 저장하거나 전달해야 할 때 쓴다.

```swift
let r: Result<String, Error> = Result { try signUp(email: "lee@example.com", password: "12345678") }

switch r {
case .success(let message):
    print(message)        // 가입 완료: lee@example.com
case .failure(let error):
    print(error)
}

// throws 함수 안에서는 다시 throws 방식으로 꺼낼 수 있다
// let message = try r.get()
```

`async/await`가 나오기 전에는 완료 클로저로 `Result`를 넘기는 방식을 많이 썼다. 지금은 비동기 함수도 [`async throws`]({{ '/swift/concurrency/async-await/' | relative_url }})로 표현할 수 있으므로, `Result`는 여러 작업의 성공·실패를 모아 두거나 화면 상태에 저장할 때 주로 쓴다.

## 타입이 정해진 throws

Swift 6부터는 함수가 던지는 오류의 타입을 정할 수 있다.

```swift
func validate(email: String) throws(SignUpError) {
    guard email.contains("@") else {
        throw .invalidEmail(email)
    }
}

do throws(SignUpError) {
    try validate(email: "kim")
} catch {
    // error의 타입이 any Error가 아니라 SignUpError로 정해진다
    switch error {
    case .invalidEmail(let e): print("형식 오류: \(e)")
    case .passwordTooShort, .alreadyRegistered: break
    }
}
```

함수를 `throws(SignUpError)`로 선언하고 `do throws(SignUpError)`로 받으면 `catch` 안의 `error`가 `SignUpError` 타입이 되어, 모든 경우를 `switch`로 빠짐없이 처리했는지 컴파일러가 확인한다. 다만 함수가 던질 수 있는 오류가 나중에 늘어나면 호출하는 모든 코드가 영향을 받으므로, Swift 문서는 공개 API보다는 모듈 내부나 오류 종류가 정말 고정된 곳에 쓰기를 권한다. 대부분의 코드는 그냥 `throws`로 충분하다.

## 어디서 처리할까

오류를 잡을 때마다 처리할 필요는 없다. 계층별 역할을 나누면 코드가 단순해진다.

| 계층 | 할 일 |
| --- | --- |
| 저수준(네트워크, 파일, DB) | 원인을 담은 구체적인 오류를 던진다 |
| 서비스 | 필요하면 도메인 오류로 바꿔 던진다 (`URLError` → `SignUpError.serverUnavailable`) |
| 화면(ViewModel) | 잡아서 사용자에게 보여 줄 상태로 바꾼다. 로그를 남긴다 |

중간 계층에서 `catch`로 잡아 아무것도 하지 않고 넘어가는 것(오류 삼키기)이 가장 나쁘다. 실패했는데 성공한 것처럼 다음 단계가 진행된다. 처리할 수 없으면 그대로 던진다.

## 정리

- 오류는 `Error`를 따르는 타입이며, 보통 열거형으로 실패 이유와 정보를 담는다.
- `throws` 함수는 `try` 없이 부를 수 없어서, 실패 가능성을 무시할 수 없다.
- `try?`는 이유를 버리고, `try!`는 실패 시 종료한다. 기본은 `try`와 `do-catch`다.
- `defer`로 성공·실패와 상관없는 정리 코드를 한 번만 쓴다.
- `Result`는 오류를 값으로 담을 때, typed throws는 오류 종류가 고정된 내부 코드에 쓴다.
- 오류는 처리할 수 있는 계층까지 올려 보내고, 중간에서 삼키지 않는다.

## 참고

- [The Swift Programming Language: Error Handling](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/errorhandling/)
- [Swift Evolution SE-0413: Typed throws](https://github.com/swiftlang/swift-evolution/blob/main/proposals/0413-typed-throws.md)
- [Apple: Result](https://developer.apple.com/documentation/swift/result)
