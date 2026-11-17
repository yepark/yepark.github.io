---
title: Concurrency
parent: Swift
nav_order: 1
has_children: true
has_toc: false
permalink: /swift/concurrency/
last_modified_date: 2026-11-16
---

# Swift Concurrency

Swift에서 오래 걸리는 일을 멈추지 않고 기다리고, 여러 작업을 함께 실행하고, 공유 상태를 안전하게 다루는 방법을 기초부터 순서대로 정리한다. GCD의 Queue 개념부터 시작해 Swift의 `async`/`await`, Task, actor로 이어진다.

이 시리즈는 Swift 6의 데이터 경쟁 안전성까지 다룬다. 예제의 핵심 문법은 Swift 5.5 이상에서 사용할 수 있고, 마지막 편은 Swift 6 언어 모드를 기준으로 설명한다.

{% include series-list.html %}


## 먼저 기억할 것

- `sync`/`async`는 호출자가 기다리는지를, Serial/Concurrent는 큐가 작업을 처리하는 방식을 말한다.
- `async`는 함수가 **중간에 멈췄다가 다시 이어질 수 있다**는 뜻이지, 자동으로 병렬 실행된다는 뜻이 아니다.
- `Task`는 비동기 코드가 실행되는 작업 단위다. Task 하나는 한 순간에 한 코드만 실행한다.
- actor는 공유 가변 상태에 동시에 접근하지 못하도록 격리한다.
- Swift 6의 `Sendable` 검사는 격리 영역 사이로 안전하지 않은 값이 넘어가는 일을 컴파일 단계에서 막는다.
