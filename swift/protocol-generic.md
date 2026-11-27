---
title: "프로토콜과 제네릭"
description: "Swift의 프로토콜로 타입이 지켜야 할 약속을 정하고, 프로토콜 확장으로 기본 구현을 주며, 제네릭과 제약으로 여러 타입에 쓰는 코드를 만드는 방법을 설명합니다. some과 any의 차이, associatedtype까지 예제로 정리합니다."
parent: Swift
nav_order: 7
permalink: /swift/protocol-generic/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Swift, Protocol, Generic, some, any]
---

# 프로토콜과 제네릭
{: .no_toc }

{% include article-toc.md %}

결제 화면을 만든다고 하자. 카드, 계좌이체, 간편결제가 있고 앞으로 더 늘어난다. 화면 코드가 결제 수단마다 `if`로 분기하면 수단이 늘 때마다 화면을 고쳐야 한다. "결제 수단이라면 이름이 있고 결제할 수 있다"는 **약속**만 정해 두고, 화면은 그 약속에만 의존하게 만들 수 있다. 이 약속이 **프로토콜**이다.

이 글을 쓴 환경에는 Swift 툴체인이 없어 예제를 직접 실행하지 못했다. 주석의 출력은 코드에서 결정되는 값이다.

## 프로토콜: 지켜야 할 약속

```swift
protocol PaymentMethod {
    var name: String { get }
    func pay(amount: Int) -> String
}

struct Card: PaymentMethod {
    let last4: String
    var name: String { "카드(\(last4))" }
    func pay(amount: Int) -> String { "\(name)로 \(amount)원 결제" }
}

struct BankTransfer: PaymentMethod {
    let bank: String
    var name: String { "\(bank) 계좌이체" }
    func pay(amount: Int) -> String { "\(name)로 \(amount)원 결제" }
}
```

프로토콜은 "무엇이 있어야 하는가"만 정하고 구현은 하지 않는다. `Card: PaymentMethod`처럼 프로토콜을 **채택(conform)**한 타입은 요구 사항을 모두 구현해야 하며, 빠뜨리면 컴파일 오류가 난다. 구조체, 클래스, 열거형 모두 프로토콜을 채택할 수 있다.

화면 코드는 구체 타입이 아니라 프로토콜만 안다.

```swift
func checkout(with method: any PaymentMethod, amount: Int) {
    print(method.pay(amount: amount))
}

checkout(with: Card(last4: "1234"), amount: 5000)            // 카드(1234)로 5000원 결제
checkout(with: BankTransfer(bank: "국민"), amount: 12000)     // 국민 계좌이체로 12000원 결제
```

새 결제 수단을 추가해도 `checkout`은 고칠 필요가 없다. 이것이 [의존성 주입]({{ '/spring/ioc-di/' | relative_url }})이나 [MVVM의 테스트용 서비스]({{ '/swift/mvvm-swift/' | relative_url }})가 프로토콜을 쓰는 이유다. 테스트에서는 가짜 구현을 넣으면 된다.

## 프로토콜 확장: 기본 구현 주기

여러 타입이 같은 구현을 반복한다면 프로토콜 **확장(extension)**에 기본 구현을 둔다.

```swift
extension PaymentMethod {
    func pay(amount: Int) -> String {
        "\(name)로 \(amount)원 결제"
    }

    var receiptTitle: String { "[\(name)] 영수증" }
}

struct EasyPay: PaymentMethod {
    var name: String { "간편결제" }
    // pay는 확장의 기본 구현을 쓴다
}

print(EasyPay().pay(amount: 3000))    // 간편결제로 3000원 결제
print(EasyPay().receiptTitle)          // [간편결제] 영수증
```

상속 없이 여러 타입에 공통 기능을 붙일 수 있어서, 구조체 중심의 Swift 코드에서 상속을 대신한다. Swift 표준 라이브러리의 `map`, `filter` 같은 메서드도 `Sequence` 프로토콜의 확장으로 구현돼 있어, `Sequence`를 따르는 모든 타입이 그대로 쓴다.

## 제네릭: 타입을 매개변수로

두 값을 바꾸는 함수를 `Int`용, `String`용으로 따로 만들 필요는 없다.

```swift
func swapValues<T>(_ a: inout T, _ b: inout T) {
    let temp = a
    a = b
    b = temp
}

var x = 1, y = 2
swapValues(&x, &y)
print(x, y)        // 2 1

var s1 = "A", s2 = "B"
swapValues(&s1, &s2)
print(s1, s2)      // B A
```

`<T>`가 **타입 매개변수**다. 호출할 때 컴파일러가 `T`를 `Int`나 `String`으로 정한다. `Array<Element>`, `Dictionary<Key, Value>`, `Optional<Wrapped>`가 모두 제네릭 타입이다.

### 제약: 이런 능력이 있는 타입만

제네릭 함수 안에서 `T`로 할 수 있는 일은 많지 않다. 비교나 덧셈이 필요하면 **제약**으로 "이 프로토콜을 따르는 타입만"이라고 정한다.

```swift
func largest<T: Comparable>(_ values: [T]) -> T? {
    guard var result = values.first else { return nil }
    for v in values where v > result {
        result = v
    }
    return result
}

print(largest([3, 9, 2]) ?? 0)            // 9
print(largest(["kiwi", "apple"]) ?? "")   // kiwi
```

`T: Comparable`이라서 `>`를 쓸 수 있다. 조건이 여럿이면 `where T: Comparable & Hashable`처럼 쓴다.

## some과 any

프로토콜을 타입처럼 쓸 때 앞에 `some`이나 `any`를 붙인다. 둘은 뜻이 다르다.

| | `some PaymentMethod` | `any PaymentMethod` |
| --- | --- | --- |
| 뜻 | "어떤 **하나의** 구체 타입이다. 컴파일러는 안다" | "PaymentMethod를 따르는 **아무** 타입이나 담는 상자" |
| 다른 타입 섞기 | 불가 | 가능 (`[any PaymentMethod]`) |
| 성능 | 구체 타입으로 바로 호출 | 상자를 거쳐 호출(약간의 비용) |
| 예 | SwiftUI의 `var body: some View` | 결제 수단 목록 |

```swift
let methods: [any PaymentMethod] = [Card(last4: "1234"), BankTransfer(bank: "국민"), EasyPay()]
for m in methods {
    print(m.name)
}
// 카드(1234)
// 국민 계좌이체
// 간편결제

func defaultMethod() -> some PaymentMethod {
    Card(last4: "0000")    // 항상 같은 구체 타입을 돌려줘야 한다
}
```

서로 다른 타입을 한 배열에 담으려면 `any`가 필요하다. 반대로 함수가 늘 같은 타입을 돌려준다면 `some`이 더 빠르고 타입 정보도 잃지 않는다. 매개변수의 `func f(_ m: some PaymentMethod)`는 제네릭 함수 `func f<T: PaymentMethod>(_ m: T)`를 짧게 쓴 것이다. 기본은 `some`으로 쓰고, 여러 타입을 섞어야 할 때만 `any`를 쓴다.

## associatedtype: 프로토콜 안의 제네릭

프로토콜이 "어떤 타입을 다룬다"는 것을 구현하는 쪽에 맡기고 싶을 때 `associatedtype`을 쓴다.

```swift
protocol Repository {
    associatedtype Item
    func findAll() -> [Item]
}

struct MemoRepository: Repository {
    func findAll() -> [String] { ["장보기", "운동"] }   // Item은 String으로 정해진다
}
```

`Collection`의 `Element`, SwiftUI `View`의 `Body`가 이런 연관 타입이다. 연관 타입이 있는 프로토콜은 Swift 5.7부터 `any Repository`처럼 상자로 쓸 수 있지만, 그 상자에서 `findAll()`의 결과 타입은 구체적으로 알 수 없게 된다. 연관 타입이 중요하다면 제네릭이나 `some`으로 다룬다.

## 정리

- 프로토콜은 타입이 지켜야 할 약속이다. 코드가 구체 타입 대신 프로토콜에 의존하면 교체와 테스트가 쉬워진다.
- 프로토콜 확장으로 기본 구현을 주면 상속 없이 공통 기능을 붙일 수 있다.
- 제네릭은 타입을 매개변수로 받아 여러 타입에 쓰는 코드를 만들고, 제약(`T: Comparable`)으로 필요한 능력을 요구한다.
- `some`은 "컴파일러가 아는 하나의 구체 타입", `any`는 "아무 타입이나 담는 상자"다. 기본은 `some`, 섞어야 할 때 `any`.
- `associatedtype`은 프로토콜 안의 타입 매개변수다.

## 참고

- [The Swift Programming Language: Protocols](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols/)
- [The Swift Programming Language: Generics](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/generics/)
- [The Swift Programming Language: Opaque and Boxed Protocol Types](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/opaquetypes/)
- [WWDC22: Embrace Swift generics](https://developer.apple.com/videos/play/wwdc2022/110352/)
