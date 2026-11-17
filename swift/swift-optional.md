---
title: "Optional과 if let·guard let"
parent: "Swift"
nav_order: 2
permalink: /swift/swift-optional/
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
date: 2021-04-28
description: "Optional의 타입 의미와 if let, guard let, map·flatMap을 값의 수명 범위와 실패 경로 중심으로 설명합니다."
first_written: 2021-04-28
last_modified_date: 2026-11-17
tags: [Swift, Optional, Optional-Binding]
---

# Optional과 if let·guard let
{: .no_toc }

{% include article-toc.md %}

Swift의 Optional은 값이 있거나 없을 수 있음을 타입으로 표현한다. `String?`은 `String`과 다른 타입이며, 값을 사용하려면 안전하게 꺼내는 과정이 필요하다.

## 값이 없는 경우부터 생각하기

서버가 닉네임을 보내지 않았다고 생각해 보자. 빈 문자열은 ‘문자열은 있지만 길이가 0’인 값이고, `nil`은 ‘값 자체가 없음’이다. `String?`은 이 두 상황을 구분해 표현한다.

언래핑은 Optional 상자 안의 값을 꺼내는 과정이다. 먼저 값이 있는지 검사하고, 있다면 일반 `String`으로 사용할 새 이름을 만든다. 아래 예제에서는 조건이 성공한 뒤 그 이름을 어느 범위까지 사용할 수 있는지 비교하면 된다.

## `if let`: 특정 분기 안에서 사용할 때

Optional에 값이 있을 때만 짧은 작업을 수행하려면 `if let`이 자연스럽다.

```swift
func printNickname(_ nickname: String?) {
    if let nickname {
        print("별명: \(nickname)")
    } else {
        print("별명이 없습니다")
    }
}
```

바인딩한 `nickname`은 `if` 본문 안에서만 사용할 수 있다. 값의 유무에 따라 서로 다른 흐름이 모두 중요할 때 적합하다.

함수를 선언한 것만으로 출력되지는 않는다. 아래 두 줄을 이어서 호출해 두 경로를 확인한다.

```swift
printNickname("yep") // 별명: yep
printNickname(nil)   // 별명이 없습니다
```

첫 호출에서는 Optional 안의 문자열을 꺼내 첫 번째 `print`가 실행된다. 두 번째는 꺼낼 값이 없으므로 `else`가 실행된다. 빈 문자열 `""`을 넘기면 값은 있는 것이므로 첫 번째 경로로 들어간다.

## `guard let`: 조건이 아니면 일찍 종료할 때

이후 로직 전체에 값이 필요하다면 `guard let`으로 실패 조건을 먼저 처리한다.

```swift
enum ProfileError: Error {
    case missingID
}

func loadProfile(id: String?) throws {
    guard let id else {
        throw ProfileError.missingID
    }

    print("프로필 요청: \(id)")
}
```

`guard`의 `else` 블록은 `return`, `throw`, `break`, `continue` 또는 반환하지 않는 함수 호출로 현재 스코프를 벗어나야 한다. 바인딩한 값은 `guard` 다음 줄부터 바깥 스코프의 끝까지 유지된다.

## 같은 이름으로 다시 바인딩하기

Swift는 기존 Optional과 같은 이름으로 언래핑된 값을 만들 수 있다.

```swift
func greet(name: String?) {
    guard let name else { return }
    print("안녕하세요, \(name)")
}
```

이 문법은 `guard let name = name else { return }`을 짧게 쓴 것이다. 바인딩 이후의 `name`은 `String?`이 아니라 `String`이다.

## 여러 Optional을 함께 검사하기

쉼표로 여러 바인딩과 Boolean 조건을 연결할 수 있다. 앞 조건부터 평가하며 하나라도 실패하면 본문을 실행하지 않는다.

```swift
func makeURL(host: String?, port: Int?) -> URL? {
    guard
        let host,
        let port,
        (1...65_535).contains(port)
    else {
        return nil
    }

    return URL(string: "https://\(host):\(port)")
}
```

조건이 지나치게 많아지면 어떤 값이 실패했는지 알기 어려워진다. 서로 다른 오류를 사용자에게 알려야 한다면 여러 `guard`로 나누거나 검증 결과를 별도 타입으로 표현한다.

## `map`과 `flatMap`

Optional의 값이 있을 때만 변환하려면 `map`을 사용할 수 있다.

```swift
let text: String? = "42"
let decorated = text.map { "입력값: \($0)" }
// Optional("입력값: 42")
```

변환 함수 자체가 Optional을 반환한다면 `flatMap`이 Optional의 중첩을 막아 준다.

```swift
let number = text.flatMap(Int.init)
// Int? — Optional(Optional(42))가 아니다
```

다만 단순한 조건 분기에 함수형 연산을 억지로 사용하면 오히려 읽기 어려워질 수 있다. 변환은 `map`과 `flatMap`, 제어 흐름은 `if let`과 `guard let`이라는 기준으로 시작하면 선택하기 쉽다.

## 그 밖의 선택지

- 기본값이 자연스러우면 nil 병합 연산자 `??`를 사용한다.
- 여러 단계의 Optional 접근은 optional chaining `?.`으로 연결한다.
- `map`과 `flatMap`은 값을 변환하는 흐름에 유용하다.
- 강제 언래핑 `!`은 값이 없으면 런타임 오류가 발생하므로, 불변 조건을 확실히 증명할 수 있는 제한된 경우에만 사용한다.

`if let`과 `guard let` 중 하나가 항상 더 좋은 것은 아니다. 값의 유무가 두 개의 정상적인 분기라면 `if let`, 값이 없으면 더 진행할 수 없다면 `guard let`이 읽기 쉽다.

## 참고

- [The Swift Programming Language: The Basics](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/thebasics/)
- [The Swift Programming Language: Control Flow](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/controlflow/)
