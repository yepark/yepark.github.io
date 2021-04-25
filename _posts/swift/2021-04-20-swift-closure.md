---
layout: single
title: "[Swift] Swift 클로저"
date: 2021-04-20
comments: true
categories:
  - Swift
tags: [Swift]
# 목차
toc: true
toc_sticky: true
---

### draft 작성중
## Swift 클로저 ##
내가 클로저를 처음 접한게 자바스크립트 였었는데, 클로저에 대해서 든 생각은 클로저 선언시 해당 상황의 변수들을 캡쳐해서 클로저 함수안에서 사용한다고 이해했었다. 어떻게 보면 Objective-c에 블록이라고 이해하면 되겠다.(정확히는 블록 + 블록함수 선언시 주변의 __block변수)

자바스크립트에서의 클로저
- 자유변수를 클로저가 선언될 당시에 묶인 변수로 만든다.(열린 람다 -> 닫힌 람다로)

1. swift 기본 클로저
```
// 기본 선언 방식
{ (파라메터) -> 리턴타입 in
  
}
```
//위는 일단 자바스크립트 익명함수 형태임.. 차이점은 function키워드가 없고 중괄호가 밖으로 나왔으며 in 키워드가 있다




~~클로저는 중첩함수 + 익명함수~~

그러나 스위프트는 이보다 더 나아가 여러가지 개념이 생겨난거 같다. 클로저는 기본적으로 참조 타입이고 일급 객체의 역할을 한다.
1. 기본 클로저
2. Trailing Closures (후행 클로저)
```
reversedNames = names.sorted() { $0 > $1 } // ()뒤에 선언 생략 가능
```
5. Escaping Closures(탈출 클로저)
6. Autoclosures(자동 클로저)

https://docs.swift.org/swift-book/LanguageGuide/Closures.html
https://hyunseob.github.io/2016/09/17/lambda-anonymous-function-closure/
