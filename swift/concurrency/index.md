---
title: Concurrency
parent: Swift
nav_order: 1
has_children: true
permalink: /swift/concurrency/
---

# Swift Concurrency

Swift에서 여러 일을 동시에 안전하게 처리하는 방법을 기초부터 하루에 하나씩 정리한다.

## 순서

| 편 | 내용 |
| --- | --- |
| 1 | 왜 Swift Concurrency인가: 콜백에서 async/await로 |
| 2 | async/await 기초: 기다리는 함수 만들고 부르기 |
| 3 | Task: 비동기 작업 시작하고 취소하기 |
| 4 | 여러 작업 한꺼번에: async let과 TaskGroup |
| 5 | actor: 여러 곳에서 같은 데이터를 건드릴 때 |
| 6 | @MainActor: 화면 업데이트는 메인 스레드에서 |
| 7 | Sendable과 Swift 6의 엄격한 동시성 검사 |
