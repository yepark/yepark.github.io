---
title: "구조체와 클래스: 값 타입과 참조 타입"
description: "Swift의 struct와 class가 복사될 때 어떻게 다르게 동작하는지 값 타입과 참조 타입으로 설명하고, let과 mutating, 상속, 식별성, Copy-on-Write, 어느 쪽을 고를지 기준을 예제로 정리합니다."
parent: Swift
nav_order: 1
permalink: /swift/struct-class/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Swift, Struct, Class, Value-Type, Reference-Type]
---

# 구조체와 클래스: 값 타입과 참조 타입
{: .no_toc }

{% include article-toc.md %}

Swift로 데이터를 표현할 때 가장 먼저 고르는 것이 `struct`(구조체)와 `class`(클래스)다. 둘 다 프로퍼티와 메서드를 가질 수 있어 비슷해 보이지만, **변수에 대입하거나 함수에 넘길 때의 동작**이 완전히 다르다. Swift 표준 라이브러리의 `String`, `Array`, `Dictionary`가 모두 구조체이고, Apple이 "기본은 구조체로 시작하라"고 권하는 이유도 이 차이에 있다.

이 글을 쓴 환경에는 Swift 툴체인이 없어 예제를 직접 실행하지 못했다. 주석의 출력은 Swift 언어 규칙으로 결정되는 값이다.

## 대입하면 무슨 일이 일어나나

같은 모양의 구조체와 클래스를 만들어 비교해 보자.

```swift
struct PointS {
    var x: Int
}

final class PointC {
    var x: Int
    init(x: Int) { self.x = x }
}

var a = PointS(x: 1)
var b = a          // 값이 복사된다
b.x = 100
print(a.x, b.x)    // 1 100

let c = PointC(x: 1)
let d = c          // 같은 객체를 가리키는 참조가 복사된다
d.x = 100
print(c.x, d.x)    // 100 100
```

| | 구조체 (값 타입) | 클래스 (참조 타입) |
| --- | --- | --- |
| 대입·전달 시 | 값 전체가 복사된다 | 같은 객체를 가리키는 참조만 복사된다 |
| 한쪽을 바꾸면 | 다른 쪽은 그대로 | 다른 쪽도 바뀐다 |
| 비유 | 문서 사본을 건네기 | 같은 구글 문서 링크를 건네기 |

구조체는 사본을 건네므로 받은 쪽이 아무리 고쳐도 원본이 안전하다. 클래스는 링크를 건네므로 누가 고치든 모두에게 반영된다. 이것이 편할 때도 있지만, "내가 넘긴 객체를 다른 곳에서 몰래 바꾸는" 버그의 원인이 된다.

## let의 의미도 다르다

```swift
let p = PointS(x: 1)
// p.x = 2            // 컴파일 오류: let으로 선언한 구조체는 내부도 바꿀 수 없다

let q = PointC(x: 1)
q.x = 2               // 가능: q가 가리키는 대상을 바꾸지 않았을 뿐, 객체 내부는 바꿀 수 있다
// q = PointC(x: 3)   // 컴파일 오류: 다른 객체를 가리키게 할 수는 없다
```

구조체의 `let`은 "이 값 전체가 바뀌지 않는다"이고, 클래스의 `let`은 "이 변수가 다른 객체를 가리키지 않는다"이다. 클래스는 `let`으로 선언해도 내용이 바뀔 수 있다는 점을 기억한다.

## mutating: 구조체가 자기 자신을 바꿀 때

구조체의 메서드는 기본적으로 자기 프로퍼티를 바꿀 수 없다. 바꾸는 메서드에는 `mutating`을 붙인다.

```swift
struct Counter {
    private(set) var count = 0

    mutating func increment() {
        count += 1
    }
}

var counter = Counter()
counter.increment()
print(counter.count)   // 1

let fixed = Counter()
// fixed.increment()   // 컴파일 오류: let 값에는 mutating 메서드를 부를 수 없다
```

`mutating`은 "이 메서드는 값을 바꾼다"는 표시라서, 컴파일러가 `let` 값에 대한 호출을 막아 준다. 어디서 값이 바뀔 수 있는지가 코드에 드러난다.

## 클래스만 할 수 있는 것

| 기능 | 구조체 | 클래스 |
| --- | --- | --- |
| 상속 | 없음 (프로토콜로 공통 기능 표현) | 있음 |
| `deinit` (해제 직전 정리) | 없음 | 있음 |
| 식별성 비교 `===` | 없음 | "같은 객체인가" 비교 |
| 여러 곳에서 같은 상태 공유 | 불가 (복사됨) | 가능 |
| 메모리 관리 | 대부분 스택이나 값 안에 저장 | 힙에 저장하고 ARC로 참조 개수 관리 |

```swift
let e = PointC(x: 1)
let f = PointC(x: 1)
print(e === f)   // false: 값은 같아도 서로 다른 객체
print(e === e)   // true
```

클래스는 ARC로 관리되므로 [클로저의 참조 순환]({{ '/swift/swift-closure/' | relative_url }}) 같은 메모리 누수를 신경 써야 하고, 여러 스레드가 같은 객체를 동시에 고치면 [데이터 경쟁]({{ '/swift/concurrency/actor/' | relative_url }})이 생길 수 있다. 구조체는 복사되므로 이런 문제가 훨씬 적고, [Sendable]({{ '/swift/concurrency/sendable-swift-6/' | relative_url }}) 조건도 쉽게 만족한다.

## 큰 배열을 복사하면 느리지 않나: Copy-on-Write

`Array`가 구조체라면, 원소 100만 개짜리 배열을 함수에 넘길 때마다 100만 개를 복사할까? 그렇지 않다.

```swift
var original = Array(repeating: 0, count: 1_000_000)
var copy = original   // 이 순간에는 실제 복사가 일어나지 않는다 (저장 공간 공유)
copy[0] = 1           // 처음 바꾸는 순간 copy만 새 저장 공간으로 복사된다
print(original[0], copy[0])   // 0 1
```

`Array`, `String`, `Dictionary`는 **Copy-on-Write(쓸 때 복사)**로 구현돼 있다. 대입할 때는 내부 저장 공간을 함께 쓰다가, 어느 한쪽이 처음 값을 바꾸는 순간에만 실제로 복사한다. 그래서 값 타입의 안전함을 유지하면서도 불필요한 복사 비용을 피한다. 직접 만든 구조체는 프로퍼티별로 복사되며, 내부에 큰 배열을 가지고 있으면 그 배열이 CoW로 동작한다.

## 무엇을 골라야 하나

Apple의 가이드를 정리하면 이렇다.

1. **기본은 구조체**로 시작한다. 데이터 모델, 설정 값, 화면 상태, API 응답 대부분이 해당한다.
2. Objective-C API와 함께 써야 하면 클래스(`NSObject` 상속)를 쓴다.
3. **식별성이 중요할 때**, 즉 여러 곳에서 "바로 그 하나의 객체"를 공유하고 변경을 함께 봐야 할 때 클래스를 쓴다. 예: 네트워크 연결 관리자, 파일 핸들, SwiftUI의 `@Observable` 모델.
4. 상속이 꼭 필요하면 클래스를 쓴다. 단, 공통 동작은 상속보다 [프로토콜]({{ '/swift/protocol-generic/' | relative_url }})로 표현할 수 있는지 먼저 본다.

클래스를 쓸 때는 상속을 의도하지 않았다면 `final`을 붙인다. 상속으로 동작이 바뀔 여지를 없애 읽기 쉽고, 컴파일러가 메서드 호출을 더 빠르게 처리할 수 있다.

## 정리

- 구조체는 값 타입이라 대입·전달 시 복사되고, 클래스는 참조 타입이라 같은 객체를 공유한다.
- 구조체의 `let`은 값 전체를 고정하고, 클래스의 `let`은 참조만 고정한다.
- 구조체가 자신을 바꾸는 메서드에는 `mutating`이 필요하다.
- 상속, `deinit`, 식별성(`===`), 상태 공유는 클래스만 가능하다. 대신 ARC와 동시성 문제를 신경 써야 한다.
- `Array` 같은 표준 컬렉션은 Copy-on-Write로 복사 비용을 줄인다.
- 기본은 구조체, 식별성이나 공유가 필요할 때 클래스를 고른다.

## 참고

- [The Swift Programming Language: Structures and Classes](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/classesandstructures/)
- [Apple: Choosing Between Structures and Classes](https://developer.apple.com/documentation/swift/choosing-between-structures-and-classes)
