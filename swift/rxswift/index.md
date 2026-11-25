---
title: RxSwift
parent: Swift
nav_order: 10
has_children: true
has_toc: false
permalink: /swift/rxswift/
last_modified_date: 2026-11-25
---

# RxSwift

비동기 이벤트를 값의 흐름으로 다루는 방법을 익힌다. Observable이 이벤트를 내보내고, Operator가 흐름을 변환하고, Scheduler가 실행 맥락을 결정하고, Subject가 외부에서 이벤트를 주입하는 네 축을 중심으로 살펴본다.

Swift Concurrency(async/await)가 등장하면서 RxSwift의 역할이 줄었지만, 여전히 많은 프로덕션 코드베이스에서 쓰인다. Operator 조합으로 복잡한 비동기 흐름을 선언적으로 표현하는 방식은 Combine과 개념이 같아 함께 이해하면 도움이 된다.

{% include series-list.html %}
