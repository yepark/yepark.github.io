---
layout: single
title: "[Swift] 자바스크립트와 스위프트 클로저 차이"
date: 2021-04-20
last_modified_at: 2026-11-01
comments: true
categories:
  - Swift
tags: [Swift, JavaScript, Closure]
toc: true
toc_sticky: true
toc_label: "목차"
---

Swift와 JavaScript는 모두 함수를 값처럼 전달할 수 있고, 함수가 선언된 주변 스코프의 값을 캡처할 수 있다. 두 언어에서 클로저의 핵심 개념은 같지만, 문서에서 사용하는 용어와 메모리 관리 방식에는 차이가 있다.

## 클로저란 무엇인가

클로저는 **함수와 그 함수가 선언될 당시의 렉시컬 환경을 함께 보존한 것**이다. 바깥 함수의 실행이 끝난 뒤에도 안쪽 함수가 외부 변수를 사용할 수 있는 이유가 바로 이 환경을 캡처하기 때문이다.

```javascript
function makeCounter() {
  let count = 0;

  return function () {
    count += 1;
    return count;
  };
}

const counter = makeCounter();
counter(); // 1
counter(); // 2
```

반환된 함수는 `makeCounter()` 실행이 끝난 뒤에도 `count`에 접근한다. 함수와 `count`가 포함된 렉시컬 환경이 함께 유지되기 때문이다.

## Swift에서 말하는 클로저

Swift 문서는 다음 세 가지를 모두 클로저의 형태로 설명한다.

- 전역 함수: 이름이 있고 값을 캡처하지 않는 클로저
- 중첩 함수: 이름이 있고 주변 값을 캡처할 수 있는 클로저
- 클로저 표현식: 이름이 없고 주변 값을 캡처할 수 있는 클로저

```swift
func makeCounter() -> () -> Int {
    var count = 0

    return {
        count += 1
        return count
    }
}

let counter = makeCounter()
counter() // 1
counter() // 2
```

Swift에서는 `{ ... }` 형태의 익명 함수 문법을 “클로저 표현식”이라고 부른다. 현재 캡처하는 값이 없더라도 이 문법으로 만든 값은 클로저다.

## JavaScript에서 말하는 클로저

JavaScript 함수는 생성될 때 자신의 렉시컬 환경과 연결된다. 따라서 기술적으로는 함수가 만들어질 때마다 클로저가 형성된다. 실무 문서에서는 특히 내부 함수가 외부 스코프의 변수를 계속 사용하는 상황을 설명할 때 “클로저”라는 표현을 강조하는 경우가 많다.

JavaScript의 변수가 모두 전역인 것은 아니다. `let`과 `const`는 블록 스코프를, `var`는 함수 스코프를 가진다. 현대 JavaScript에는 `class` 문법과 `#privateField` 형태의 private element도 있다. 클로저는 private 상태를 구현하는 유일한 방법이 아니라, 렉시컬 스코프를 활용하는 여러 도구 중 하나다.

```javascript
class Counter {
  #count = 0;

  increment() {
    this.#count += 1;
    return this.#count;
  }
}
```

## 두 언어의 차이

| 구분 | Swift | JavaScript |
| --- | --- | --- |
| 용어 | 전역 함수, 중첩 함수, 클로저 표현식을 클로저의 형태로 설명 | 함수와 렉시컬 환경의 결합을 클로저로 설명 |
| 캡처 | 주변의 상수와 변수를 캡처하며 캡처 목록으로 동작을 조정 | 함수 생성 시 렉시컬 환경에 연결 |
| 메모리 | ARC를 사용하므로 `self`의 강한 캡처가 참조 순환을 만들 수 있음 | 가비지 컬렉션이 도달 가능한 렉시컬 환경을 유지 |
| 명시적 제어 | `[weak self]`, `[unowned self]`, `[value]` 같은 캡처 목록 제공 | Swift와 같은 캡처 목록 문법은 없음 |

## Swift 캡처 목록

Swift의 클로저는 기본적으로 클래스 인스턴스를 강하게 캡처한다. 인스턴스가 클로저도 강하게 보유하면 참조 순환이 생길 수 있다.

```swift
final class Loader {
    var onFinish: (() -> Void)?

    func start() {
        onFinish = { [weak self] in
            self?.handleFinish()
        }
    }

    private func handleFinish() {
        print("완료")
    }
}
```

값을 클로저 생성 시점에 복사해 고정하고 싶다면 캡처 목록에 값을 명시할 수 있다.

```swift
var value = 0
let printCapturedValue = { [value] in
    print(value)
}

value = 10
printCapturedValue() // 0
```

## 정리

Swift와 JavaScript의 클로저는 서로 다른 개념이 아니다. 둘 다 렉시컬 스코프의 값을 함수와 함께 유지한다. 차이는 Swift가 여러 함수 형태를 클로저라는 큰 범주로 명시하고 캡처 목록과 ARC 규칙을 제공하는 반면, JavaScript는 모든 함수가 렉시컬 환경과 연결되고 가비지 컬렉션으로 수명을 관리한다는 점이다.

## 참고 자료

- [The Swift Programming Language: Closures](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/closures/)
- [MDN: Closures](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Closures)
- [MDN: Classes](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes)
- [MDN: Private elements](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Classes/Private_elements)
