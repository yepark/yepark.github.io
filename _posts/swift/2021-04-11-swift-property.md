---
layout: single
title: "[Swift] Swift 프로퍼티"
date: 2021-04-11
comments: true
categories:
  - Swift
tags: [Swift]
# 목차
toc: true
toc_sticky: true
---

Swift 프로퍼티 정리

## 저장 프로퍼티(Stored Properties)
- 클래스 또는 구조체에서만 사용 가능
- let(상수), var(변수) 키워드를 이용하여 변수로 선언
- 구조체를 let으로 선언시 구조체 내부 프로퍼티가 var이어도 변경할수 없지만, 클래스는 변경 가능(참조타입)
- 지연 저장 프로퍼티(lazy)는 var키워드만 사용
- 지연 저장 프로퍼티는 다중 스레드에서 사용시 여러번 초기화 될수 있다.
## 연산 프로퍼티(Computed Properties)
- 
## 프로퍼티 옵저버(Property Observers)  
## 프로퍼티 랩퍼(Property Wrappers)  
## 전역변수와 지역변수(Global and Local Variables)  
## 타입 프로퍼티(Type Properties)  


## 참고 사이트
- [Properties](https://docs.swift.org/swift-book/LanguageGuide/Properties.html)
- [한글번역](https://jusung.gitbook.io/the-swift-language-guide/language-guide/10-properties)
