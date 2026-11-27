---
title: "Spring Data JPA로 데이터 다루기"
description: "JPA와 Hibernate, Spring Data JPA의 관계와 엔티티·리포지토리 작성법, 메서드 이름 쿼리, 영속성 컨텍스트와 변경 감지, 실제로 실행된 SQL, N+1 문제와 open-in-view 설정을 할 일 API 예제로 설명합니다."
parent: Spring
nav_order: 4
permalink: /spring/data-jpa/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Spring, JPA, Hibernate, Spring-Data-JPA]
---

# Spring Data JPA로 데이터 다루기
{: .no_toc }

{% include article-toc.md %}

할 일 API는 데이터를 어딘가에 저장해야 한다. 관계형 데이터베이스는 표(테이블)로, Java는 객체로 데이터를 다룬다. 둘 사이를 오가며 SQL을 직접 쓰고 결과를 객체에 옮겨 담는 코드는 길고 반복적이다.

이 간격을 메우는 세 층이 있다.

| 이름 | 무엇인가 |
| --- | --- |
| **JPA** (Jakarta Persistence) | Java 객체를 DB 테이블에 대응시키는 방법을 정한 **표준 명세**. 인터페이스와 어노테이션의 모음이다 |
| **Hibernate** | JPA 명세를 실제로 구현한 라이브러리. SQL을 만들고 실행한다 |
| **Spring Data JPA** | JPA 위에서 리포지토리 인터페이스만 선언하면 구현을 자동으로 만들어 주는 Spring 모듈 |

객체와 테이블을 대응시키는 기술을 일반적으로 **ORM(Object-Relational Mapping)**이라고 부른다. JPA는 Java의 표준 ORM 명세다.

## 엔티티: 테이블에 대응하는 클래스

```java
@Entity
public class Todo {

    @Id
    @GeneratedValue
    private Long id;

    @Column(nullable = false, length = 100)
    private String title;

    private boolean done;

    private Instant createdAt;

    protected Todo() {
        // JPA가 객체를 만들 때 쓰는 기본 생성자
    }

    public Todo(String title) {
        this.title = title;
        this.createdAt = Instant.now();
    }

    public void complete() {
        this.done = true;
    }

    // getter 생략
}
```

| 어노테이션 | 뜻 |
| --- | --- |
| `@Entity` | 이 클래스는 `todo` 테이블에 대응한다 |
| `@Id` | 기본 키 |
| `@GeneratedValue` | 키 값을 DB 쪽에서 만든다 |
| `@Column(nullable = false, length = 100)` | 컬럼 제약 |

세터를 열어 두지 않고 `complete()`처럼 **의미 있는 메서드**로만 상태를 바꾸게 했다. "완료 처리"라는 규칙이 엔티티 안에 모여, 어디서든 같은 방식으로만 바뀐다. 기본 생성자는 JPA가 DB에서 읽은 행으로 객체를 만들 때 필요하므로 `protected`로 숨겨 둔다.

이 예제는 개발용이라 Hibernate가 시작할 때 엔티티를 보고 테이블을 자동으로 만들게 두었다(메모리 DB의 기본 동작). 운영 DB에서는 자동 생성을 끄고 Flyway나 Liquibase 같은 마이그레이션 도구로 테이블 변경 이력을 관리한다.

## 리포지토리: 인터페이스만 선언한다

```java
public interface TodoRepository extends JpaRepository<Todo, Long> {

    // 메서드 이름으로 쿼리를 만든다: where done = ? order by createdAt desc
    List<Todo> findByDoneOrderByCreatedAtDesc(boolean done);

    long countByDone(boolean done);
}
```

구현 클래스를 쓰지 않았는데도 동작한다. Spring Data JPA가 실행 시점에 이 인터페이스의 구현을 만들어 빈으로 등록하기 때문이다.

`JpaRepository`를 상속하면 기본 메서드가 따라온다.

| 메서드 | 하는 일 |
| --- | --- |
| `save(entity)` | 새 객체면 INSERT, 이미 있는 객체면 병합 |
| `findById(id)` | 키로 하나 조회 (`Optional`) |
| `findAll()` | 전체 조회 |
| `delete(entity)`, `deleteById(id)` | 삭제 |
| `count()`, `existsById(id)` | 개수, 존재 여부 |

### 메서드 이름이 쿼리가 된다

`findByDoneOrderByCreatedAtDesc`는 이름을 해석해 쿼리를 만든다. `findBy` 뒤의 `Done`이 조건, `OrderByCreatedAtDesc`가 정렬이다. 실제로 실행된 SQL이다.

```sql
select t1_0.id,t1_0.created_at,t1_0.done,t1_0.title
from todo t1_0
where t1_0.done=?
order by t1_0.created_at desc
```

| 이름 조각 | SQL |
| --- | --- |
| `findByTitle` | `where title = ?` |
| `findByTitleContaining` | `where title like %?%` |
| `findByDoneAndCreatedAtAfter` | `where done = ? and created_at > ?` |
| `countByDone` | `select count(*) ... where done = ?` |
| `existsByTitle` | 존재 여부 |

조건이 복잡해져 이름이 길어지면 `@Query("select t from Todo t where ...")`로 JPQL(엔티티 기준 쿼리 언어)을 직접 쓴다.

## 영속성 컨텍스트와 변경 감지

서비스의 완료 처리 코드를 보자.

```java
@Transactional
public Todo complete(Long id) {
    Todo todo = get(id);
    todo.complete(); // save()를 부르지 않아도 트랜잭션이 끝날 때 UPDATE가 실행된다
    return todo;
}
```

`save()`를 부르지 않았는데 앱 로그에는 UPDATE가 찍혔다.

```sql
select t1_0.id,t1_0.created_at,t1_0.done,t1_0.title from todo t1_0 where t1_0.id=?
update todo set created_at=?,done=?,title=? where id=?
```

JPA는 트랜잭션 동안 읽어 온 엔티티를 **영속성 컨텍스트**라는 작업 공간에 기억해 둔다. 트랜잭션이 끝날 때 처음 읽은 상태와 지금 상태를 비교해 바뀐 엔티티에 대해 UPDATE를 만든다. 이것을 **변경 감지(dirty checking)**라고 한다. 같은 트랜잭션 안에서 같은 ID를 다시 조회하면 DB에 가지 않고 이 작업 공간의 객체를 돌려준다.

그래서 JPA에서는 "객체를 바꾸면 DB가 따라 바뀐다"고 생각하면 된다. 단, **트랜잭션 안에서만** 그렇다. 트랜잭션은 [5편]({{ '/spring/transaction/' | relative_url }})에서 다룬다.

## 조심할 것 두 가지

### N+1 문제

할 일에 "카테고리"가 연관돼 있다고 하자(`@ManyToOne Category category`). 할 일 목록 100개를 조회한 뒤 각 할 일의 카테고리 이름을 읽으면, 목록 조회 1번에 카테고리 조회가 100번 더 실행될 수 있다. 쿼리가 1 + N번 나간다고 해서 **N+1 문제**라고 한다.

연관 객체는 기본적으로 실제로 접근할 때까지 불러오기를 미루는데(지연 로딩), 반복문 안에서 하나씩 접근하면 그때마다 쿼리가 나가기 때문이다. 해결 방법은 처음 조회할 때 함께 가져오는 것이다.

- JPQL의 `join fetch`: `select t from Todo t join fetch t.category`
- `@EntityGraph(attributePaths = "category")`를 리포지토리 메서드에 붙이기
- 목록 화면에 필요한 값만 DTO로 바로 조회하기

개발 중에는 이 예제처럼 SQL 로그를 켜 두고, 화면 하나를 열 때 쿼리가 몇 번 나가는지 확인하는 습관이 가장 효과적이다.

### open-in-view는 끈다

Spring Boot는 기본적으로 **open-in-view**를 켜 둔다. 웹 요청이 끝날 때까지 영속성 컨텍스트와 DB 연결을 유지해, 컨트롤러나 JSON 변환 중에도 지연 로딩이 되게 하는 설정이다. 편하지만, 요청 처리 내내 DB 연결을 붙잡아 트래픽이 많을 때 연결이 모자라고, 어디서 쿼리가 나가는지 추적하기 어렵게 만든다. 그래서 시작할 때 경고 로그도 찍힌다.

이 연재는 `spring.jpa.open-in-view: false`로 끄고, 서비스 안(트랜잭션 안)에서 필요한 데이터를 모두 읽어 DTO로 바꿔 내보낸다.

## 정리

- JPA는 객체와 테이블을 대응시키는 표준 명세, Hibernate는 그 구현, Spring Data JPA는 리포지토리 구현을 자동으로 만들어 주는 모듈이다.
- 엔티티는 `@Entity`와 `@Id`로 선언하고, 상태 변경은 의미 있는 메서드로만 한다.
- 리포지토리는 인터페이스만 선언하면 되고, 메서드 이름이 쿼리가 된다.
- 트랜잭션 안에서 엔티티를 바꾸면 변경 감지로 UPDATE가 자동 실행된다.
- 연관 객체를 반복문에서 읽을 때 N+1 쿼리가 생기지 않는지 SQL 로그로 확인하고, open-in-view는 끈다.

## 실습 소스

- [Todo.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/Todo.java' | relative_url }})
- [TodoRepository.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/TodoRepository.java' | relative_url }})
- [TodoService.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/TodoService.java' | relative_url }})
- [TodoRepositoryTest.java]({{ '/assets/examples/spring/todo/src/test/java/com/example/todo/todo/TodoRepositoryTest.java' | relative_url }})

## 참고

- [Spring Data JPA Reference](https://docs.spring.io/spring-data/jpa/reference/)
- [Spring Data JPA: Query Methods](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html)
- [Hibernate ORM Documentation](https://hibernate.org/orm/documentation/)
- [Jakarta Persistence](https://jakarta.ee/specifications/persistence/)
