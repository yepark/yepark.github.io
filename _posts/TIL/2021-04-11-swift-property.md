---
layout: single
title: "[TIL] Swift 프로퍼티"
date: 2021-04-11
comments: true
categories:
  - TIL
tags: [Swift]
# 목차
toc: true
toc_sticky: true
---
### draft 작성중
Swift 프로퍼티에 대해 공부한 내용을 정리해 본다.


- 저장 프로퍼티(Stored Properties)
저장 프로퍼티는 특정 클래스 또는 구조체 인스턴스의 일부로 저장된 상수 또는 변수다.
저장 프로퍼티는 변수 저장 프로퍼티(var 키워드로 된것) 또는 상수 저장 프로퍼티(let 키워드로 된것)일수 있습니다.
```swift
struct FixedLengthRange {
    var firstValue: Int
    let length: Int
}
var rangeOfThreeItems = FixedLengthRange(firstValue: 0, length: 3)
// 0,1,2
rangeOfThreeItems.firstValue = 6
// 6,7,8로 변경됨
```  

  1. 상수 구조체 인스턴스의 저장 프로퍼티(Stored Properties of Constant Structure Instances)
  구조체의 인스턴스를 상수로 할당하면 변수 프로퍼티로 선언 된 경우에도 인스턴스의 프로퍼티를 수정할 수 없습니다.  
  ```swift
  let rangeOfFourItems = FixedLengthRange(firstValue: 0, length: 4)
  // 0,1,2,3
  rangeOfFourItems.firstValue = 6
  // 에러, firstValue는 변수이지만 변경 불가능 
  ```  
  이 동작은 구조체가 값 타입이기 때문입니다. 값 타입은 인스턴스가 상수로 표시되면 모든 프로퍼티도 마찬가지 변경 불가능 합니다.(클래스는 레퍼런스 타입이라서 상수로 인스턴스를 생성하더라도 인스턴스의 변수 프로퍼티는 변경 할수 있습니다.)

  2. 지연 저장 프로퍼티(Lazy Stored Properties)
  3. 저장 프로퍼티 와 인스턴스 변수(Stored Properties and Instance Variables)


- 연산 프로퍼티(Computed Properties)
- 프로퍼티 옵저버(Property Observers)
- 프로퍼티 랩퍼(Property Wrappers)
- 전역 변수 와 지역 변수(Global and Local Variables)
- 타입 프로퍼티(Type Properties)


## 참고 사이트
- [Properties](https://docs.swift.org/swift-book/LanguageGuide/Properties.html)
