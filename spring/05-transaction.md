---
title: "트랜잭션과 @Transactional"
description: "트랜잭션이 필요한 이유와 Spring의 @Transactional이 프록시로 동작하는 방식, 롤백 규칙, readOnly, 전파를 설명하고, 같은 클래스 안에서 메서드를 호출하면 트랜잭션이 무시되는 함정을 실행 결과로 확인합니다."
parent: Spring
nav_order: 5
permalink: /spring/transaction/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Spring, Transaction, AOP, Proxy]
---

# 트랜잭션과 @Transactional
{: .no_toc }

{% include article-toc.md %}

할 일 세 개를 한꺼번에 등록하는데 세 번째 제목이 비어 있어 실패했다고 하자. 앞의 두 개는 저장된 채로 남아야 할까, 모두 취소돼야 할까? "한 묶음으로 들어온 요청은 모두 성공하거나 모두 없던 일이 돼야 한다"면 트랜잭션이 필요하다.

**트랜잭션(transaction)**은 여러 DB 작업을 하나의 단위로 묶어, 전부 반영하거나(commit) 전부 취소하는(rollback) 장치다. 계좌 이체에서 출금만 되고 입금이 안 되는 일을 막는 것이 대표적인 예다.

## @Transactional

Spring에서는 메서드에 `@Transactional`을 붙이면 메서드 시작 시 트랜잭션을 열고, 정상 종료하면 커밋, 예외가 나면 롤백한다.

```java
@Service
@Transactional(readOnly = true)
public class TodoService {

    @Transactional
    public List<Todo> createAll(List<String> titles) {
        List<Todo> saved = titles.stream().map(t -> repository.save(new Todo(t))).toList();
        if (titles.contains("")) {
            // 하나라도 잘못되면 앞에서 저장한 것까지 모두 취소된다
            throw new IllegalArgumentException("빈 제목이 있습니다");
        }
        return saved;
    }
    ...
}
```

통합 테스트로 확인했다.

```java
long before = repository.count();
assertThatThrownBy(() -> service.createAll(List.of("하나", "둘", "")))
        .isInstanceOf(IllegalArgumentException.class);
assertThat(repository.count()).isEqualTo(before);
```

```text
[rollback] before=0 after=0
```

"하나", "둘"을 `save()`했지만 예외로 롤백되어 남지 않았다.

클래스에 `@Transactional(readOnly = true)`를 붙이고 쓰기 메서드에만 `@Transactional`을 다시 붙였다. 조회 메서드는 읽기 전용 트랜잭션으로 실행되어, JPA가 변경 감지를 위한 비교 작업을 하지 않고 DB 드라이버에도 읽기 전용임을 알려 최적화할 여지를 준다. 실수로 조회 메서드에서 엔티티를 바꿔도 DB에 반영되지 않는다.

## 어떻게 동작하나: 프록시

`@Transactional`은 메서드 안의 코드를 바꾸지 않는다. Spring은 `@Transactional`이 붙은 빈을 등록할 때, 원래 객체를 감싼 **프록시(proxy)** 객체를 만들어 대신 등록한다.

```text
호출하는 쪽 → [프록시: 트랜잭션 시작] → 원래 객체의 메서드 → [프록시: 커밋 또는 롤백]
```

다른 빈이 `TodoService`를 주입받으면 실제로는 이 프록시를 받는다. 프록시가 메서드 호출을 가로채 앞뒤에 트랜잭션 처리를 붙인다. 이렇게 공통 기능을 코드 밖에서 끼워 넣는 기법을 **AOP(Aspect-Oriented Programming, 관점 지향 프로그래밍)**라고 하며, 트랜잭션·로깅·보안 검사 같은 기능이 이 방식으로 동작한다.

테스트에서 빈의 실제 클래스를 출력해 보면 프록시인 것이 보인다.

```text
[proxy] BulkImporter$$SpringCGLIB$$0 aop=true
```

`$$SpringCGLIB$$`는 Spring이 원래 클래스를 상속해 만든 프록시 클래스라는 표시다.

## 함정: 같은 클래스 안에서 부르면 무시된다

프록시 방식에는 유명한 함정이 있다. 다음 클래스를 보자.

```java
@Component
public class BulkImporter {

    public void importAll(List<String> titles) {
        saveAll(titles); // this.saveAll(...) : 프록시를 거치지 않는다
    }

    @Transactional
    public void saveAll(List<String> titles) {
        for (String title : titles) {
            if (title.isBlank()) {
                throw new IllegalArgumentException("빈 제목이 있습니다");
            }
            repository.save(new Todo(title));
        }
    }
}
```

같은 입력을 두 메서드로 넣어 봤다.

```java
// 1) 밖에서 saveAll을 직접 호출
importer.saveAll(List.of("하나", "둘", " "));   // 예외

// 2) 밖에서 importAll을 호출 → 안에서 saveAll 호출
importer.importAll(List.of("하나", "둘", " ")); // 예외
```

```text
[saveAll 직접 호출] 남은 행 = 0
[importAll 내부 호출] 남은 행 = 2
```

똑같이 `saveAll`이 실행됐는데, 두 번째는 롤백되지 않고 "하나", "둘"이 남았다. 외부에서 `importAll`을 부르면 프록시를 지나지만 `importAll`에는 `@Transactional`이 없어 그냥 원래 객체로 넘어간다. 그 안에서 `saveAll`을 부르는 것은 원래 객체 자신(`this`)의 메서드 호출이라 **프록시를 거치지 않는다.** 그래서 `saveAll`의 `@Transactional`이 아예 적용되지 않았다. 각 `save()`는 리포지토리의 기본 트랜잭션으로 하나씩 따로 커밋됐다.

이 문제는 컴파일 오류도 경고도 없이, 실패 상황에서만 데이터가 어긋나는 형태로 드러나서 찾기 어렵다. 피하는 방법은 이렇다.

- 트랜잭션 경계가 되는 메서드(밖에서 처음 부르는 메서드)에 `@Transactional`을 붙인다. 위 예에서는 `importAll`에 붙인다.
- 트랜잭션이 필요한 메서드를 다른 빈으로 분리해, 주입받은 빈(프록시)을 통해 호출한다.
- `private` 메서드나 `final` 메서드에는 `@Transactional`이 적용되지 않는다는 점도 기억한다. 프록시가 가로챌 수 없기 때문이다.

## 롤백 규칙

기본적으로 **런타임 예외(`RuntimeException`)와 `Error`가 나면 롤백**하고, **체크 예외(`Exception`을 직접 상속한 예외)는 커밋**한다. 체크 예외는 "예상된 업무 상황"이라는 Java의 전통적인 해석을 따른 것이다. 체크 예외에도 롤백하려면 지정한다.

```java
@Transactional(rollbackFor = Exception.class)
```

예외를 `try-catch`로 잡아 삼키면 프록시는 예외를 보지 못하므로 커밋한다. 롤백이 필요한데 예외를 잡아야 한다면 다시 던지거나 명시적으로 롤백을 표시한다.

## 전파: 트랜잭션 안에서 트랜잭션 메서드를 부르면

`@Transactional` 메서드가 다른 `@Transactional` 메서드(다른 빈의)를 부르면 어떻게 될까? **전파(propagation)** 설정이 정한다.

| 전파 | 이미 트랜잭션이 있으면 | 없으면 |
| --- | --- | --- |
| `REQUIRED` (기본) | 그 트랜잭션에 참여한다 | 새로 시작한다 |
| `REQUIRES_NEW` | 기존 것을 잠시 멈추고 새로 시작한다 | 새로 시작한다 |
| `MANDATORY` | 참여한다 | 예외 |
| `SUPPORTS` | 참여한다 | 트랜잭션 없이 실행 |

대부분은 기본값 `REQUIRED`로 충분하다. 바깥 작업이 실패해도 반드시 남겨야 하는 감사 로그 기록처럼, 독립적으로 커밋돼야 하는 작업에만 `REQUIRES_NEW`를 쓴다. `REQUIRED`로 참여한 안쪽 메서드에서 런타임 예외가 나면, 바깥에서 그 예외를 잡더라도 트랜잭션 전체가 롤백 전용으로 표시되어 결국 롤백된다(`UnexpectedRollbackException`).

## 정리

- 트랜잭션은 여러 DB 작업을 전부 반영하거나 전부 취소하는 단위다.
- `@Transactional`은 프록시가 메서드 호출을 가로채 트랜잭션을 여닫는 방식(AOP)으로 동작한다.
- 같은 클래스 안의 메서드 호출은 프록시를 거치지 않아 `@Transactional`이 무시된다. 실제로 롤백되지 않고 데이터 2건이 남는 것을 확인했다.
- 런타임 예외는 롤백, 체크 예외는 커밋이 기본이다. 예외를 삼키면 커밋된다.
- 전파의 기본값 `REQUIRED`는 바깥 트랜잭션에 참여하고, 독립 커밋이 필요할 때만 `REQUIRES_NEW`를 쓴다.

## 실습 소스

- [TodoService.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/TodoService.java' | relative_url }})
- [BulkImporter.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/BulkImporter.java' | relative_url }})
- [SelfInvocationTest.java]({{ '/assets/examples/spring/todo/src/test/java/com/example/todo/todo/SelfInvocationTest.java' | relative_url }})

## 참고

- [Spring Framework: Declarative Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html)
- [Spring Framework: Transaction Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html)
- [Spring Framework: Understanding AOP Proxies](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html)
