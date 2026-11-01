---
layout: single
title: "[Swift] 프로퍼티 한 번에 정리하기"
date: 2021-04-11
last_modified_at: 2026-11-01
comments: true
categories:
  - Swift
tags: [Swift, Property]
toc: true
toc_sticky: true
toc_label: "목차"
---

Swift의 프로퍼티는 타입이나 인스턴스에 값을 연결한다. 값을 직접 저장하는 저장 프로퍼티뿐 아니라, 값을 계산하는 연산 프로퍼티와 변경을 감지하는 프로퍼티 옵저버도 제공한다.

## 저장 프로퍼티

저장 프로퍼티는 클래스와 구조체의 인스턴스에 값을 보관한다. `var`는 변경 가능한 값, `let`은 초기화 후 변경할 수 없는 값을 선언한다.

```swift
struct User {
    let id: Int
    var name: String
}

var user = User(id: 1, name: "yep")
user.name = "YEP"
```

구조체는 값 타입이므로 인스턴스를 `let`으로 선언하면 내부의 `var` 프로퍼티도 변경할 수 없다.

```swift
let user = User(id: 1, name: "yep")
// user.name = "YEP" // 컴파일 오류
```

클래스는 참조 타입이다. 클래스 인스턴스를 가리키는 참조가 `let`이어도 인스턴스의 `var` 프로퍼티는 변경할 수 있다.

## 지연 저장 프로퍼티

`lazy` 프로퍼티는 처음 접근할 때 초기값을 만든다. 초기화 비용이 크거나, 인스턴스 초기화가 끝난 뒤에야 필요한 값이 있을 때 유용하다.

```swift
final class DataManager {
    lazy var importer = DataImporter()
}
```

지연 저장 프로퍼티는 초기화 시점이 늦기 때문에 반드시 `var`로 선언한다. 여러 스레드가 초기화되지 않은 `lazy` 프로퍼티에 동시에 접근하면 한 번만 초기화된다는 보장이 없다. 동시 접근 가능성이 있다면 별도의 동기화가 필요하다.

## 연산 프로퍼티

연산 프로퍼티는 값을 저장하지 않고 getter와 선택적 setter를 통해 값을 계산한다. 클래스, 구조체, 열거형에서 사용할 수 있다.

```swift
struct Rectangle {
    var width: Double
    var height: Double

    var area: Double {
        width * height
    }
}
```

setter가 필요한 경우 `newValue`를 사용하거나 이름을 직접 지정한다.

```swift
struct Temperature {
    var celsius: Double

    var fahrenheit: Double {
        get { celsius * 9 / 5 + 32 }
        set { celsius = (newValue - 32) * 5 / 9 }
    }
}
```

## 프로퍼티 옵저버

`willSet`은 새 값이 저장되기 직전에, `didSet`은 저장된 직후에 호출된다.

```swift
final class Progress {
    var value = 0 {
        willSet {
            print("변경 예정: \(newValue)")
        }
        didSet {
            print("변경 완료: \(oldValue) → \(value)")
        }
    }
}
```

자신이 선언한 저장 프로퍼티뿐 아니라 상속받은 프로퍼티에도 옵저버를 추가할 수 있다. 다만 프로퍼티 옵저버는 일반적인 이벤트 시스템을 대신하는 기능이 아니다. 상태 변경의 부수 효과가 커지면 메서드나 별도 타입으로 책임을 분리하는 편이 읽기 쉽다.

## 프로퍼티 래퍼

프로퍼티 래퍼는 저장과 검증 같은 공통 로직을 재사용할 수 있게 한다. 래퍼 타입은 `wrappedValue`를 제공해야 한다.

```swift
@propertyWrapper
struct Clamped<Value: Comparable> {
    private var value: Value
    private let range: ClosedRange<Value>

    init(wrappedValue: Value, _ range: ClosedRange<Value>) {
        self.range = range
        self.value = min(max(wrappedValue, range.lowerBound), range.upperBound)
    }

    var wrappedValue: Value {
        get { value }
        set { value = min(max(newValue, range.lowerBound), range.upperBound) }
    }
}

struct AudioSettings {
    @Clamped(0...100) var volume = 50
}
```

## 타입 프로퍼티

타입 프로퍼티는 특정 인스턴스가 아니라 타입 자체에 속한다. `static`으로 선언하며, 클래스에서 재정의를 허용하는 연산 타입 프로퍼티는 `class`를 사용할 수 있다.

```swift
enum API {
    static let baseURL = URL(string: "https://example.com")!
}
```

저장 타입 프로퍼티는 처음 접근할 때 한 번만 초기화되며, 여러 스레드가 동시에 접근해도 초기화는 한 번만 수행된다.

## 전역 변수와 지역 변수

전역 변수는 함수·메서드·클로저·타입 바깥에 선언하고, 지역 변수는 그 안에 선언한다. Swift는 전역 변수와 지역 변수에도 연산 기능과 옵저버를 지원한다.

전역 상수와 변수는 별도의 `lazy` 표기 없이 지연 초기화된다. 반면 지역 변수는 지연 초기화되지 않는다.

## 참고 자료

- [The Swift Programming Language: Properties](https://docs.swift.org/swift-book/LanguageGuide/Properties.html)
