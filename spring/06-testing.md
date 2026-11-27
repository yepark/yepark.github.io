---
title: "Spring Boot 테스트"
description: "Spring Boot 4의 테스트를 계층별로 나눠 설명합니다. 컨테이너 없는 단위 테스트, @WebMvcTest와 MockMvcTester로 웹 계층만, @DataJpaTest로 JPA만, @SpringBootTest로 전체를 시험하는 방법과 @MockitoBean, Boot 4에서 바뀐 테스트 모듈을 실행 결과로 다룹니다."
parent: Spring
nav_order: 6
permalink: /spring/testing/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Spring, Testing, JUnit, MockMvc, Mockito]
---

# Spring Boot 테스트
{: .no_toc }

{% include article-toc.md %}

할 일 API를 고칠 때마다 서버를 띄우고 curl로 하나씩 확인할 수는 없다. 테스트 코드는 이 확인을 자동으로, 매번 같은 방식으로 해 준다. Spring Boot는 애플리케이션 전체를 띄우는 테스트부터 웹 계층만, DB 계층만 떼어 시험하는 테스트까지 범위별 도구를 제공한다.

이 연재의 프로젝트는 테스트 10개를 가지고 있고, 모두 통과한다.

```text
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0 -- in com.example.todo.core.ContainerTest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0 -- in com.example.todo.todo.TodoControllerTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0 -- in com.example.todo.todo.SelfInvocationTest
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0 -- in com.example.todo.todo.TodoRepositoryTest
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0 -- in com.example.todo.todo.TodoApiIntegrationTest
[INFO] Tests run: 10, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

## 테스트 범위 고르기

| 종류 | 띄우는 것 | 속도 | 확인하는 것 |
| --- | --- | --- | --- |
| 단위 테스트 | 없음 (`new`로 객체 생성) | 가장 빠름 | 클래스 하나의 로직 |
| `@WebMvcTest` | 웹 계층 빈만 | 빠름 | 주소 매핑, 입력 검증, JSON, 오류 응답 |
| `@DataJpaTest` | JPA·DB 관련 빈만 | 빠름 | 엔티티 매핑, 쿼리 |
| `@SpringBootTest` | 애플리케이션 전체 | 느림 | 계층이 함께 맞물려 동작하는지 |

로직 대부분은 단위 테스트로, 계층의 경계는 슬라이스 테스트(`@WebMvcTest`, `@DataJpaTest`)로, 핵심 흐름 몇 개만 전체 테스트로 확인하는 것이 일반적이다. 전체 테스트만 많으면 느리고, 실패했을 때 어느 계층 문제인지 찾기 어렵다.

## 테스트 의존성: Boot 4에서 바뀐 점

Boot 4부터는 기능별로 테스트 스타터를 추가한다.

```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-test</artifactId>
  <scope>test</scope>
</dependency>
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-webmvc-test</artifactId>
  <scope>test</scope>
</dependency>
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-data-jpa-test</artifactId>
  <scope>test</scope>
</dependency>
```

어노테이션의 패키지도 기능별로 옮겨졌다. Boot 3 예제를 복사했는데 import가 안 된다면 이 표를 확인한다(4.2.0의 jar에서 직접 확인한 위치다).

| 어노테이션 | Boot 4 패키지 |
| --- | --- |
| `@WebMvcTest`, `@AutoConfigureMockMvc` | `org.springframework.boot.webmvc.test.autoconfigure` |
| `@DataJpaTest` | `org.springframework.boot.data.jpa.test.autoconfigure` |
| `@SpringBootTest` | `org.springframework.boot.test.context` |
| `@MockitoBean` | `org.springframework.test.context.bean.override.mockito` |
| `MockMvcTester` | `org.springframework.test.web.servlet.assertj` |

## 단위 테스트: 컨테이너 없이

생성자 주입을 쓰면 Spring 없이 `new`로 객체를 만들어 시험할 수 있다. [1편]({{ '/spring/ioc-di/' | relative_url }})의 예다.

```java
@Test
void 직접_조립하기() {
    ReminderService service = new ReminderService(new SmsSender());
    assertThat(service.remind("kim", "보고서")).isEqualTo("sms to kim: 잊지 마세요: 보고서");
}
```

컨테이너를 띄우지 않으니 밀리초 단위로 끝난다. 의존 객체는 위처럼 간단한 구현을 넣거나 Mockito로 가짜를 만든다.

## @WebMvcTest: 웹 계층만

컨트롤러, `@RestControllerAdvice`, JSON 변환, 검증만 띄우고 서비스는 가짜로 바꾼다.

```java
@WebMvcTest(TodoController.class)
class TodoControllerTest {

    @Autowired
    MockMvcTester mvc;

    @MockitoBean
    TodoService service;

    @Test
    void 할_일_하나_조회() {
        given(service.get(1L)).willReturn(new Todo("장보기"));

        assertThat(mvc.get().uri("/api/todos/1"))
                .hasStatusOk()
                .bodyJson().extractingPath("$.title").isEqualTo("장보기");
    }

    @Test
    void 빈_제목이면_400() {
        var result = mvc.post().uri("/api/todos")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"title\": \"\"}");
        assertThat(result).hasStatus(400)
                .bodyJson().extractingPath("$.errors.title").isEqualTo("제목은 비어 있을 수 없습니다");
    }

    @Test
    void 없는_id면_404_ProblemDetail() {
        given(service.get(99L)).willThrow(new TodoNotFoundException(99L));

        assertThat(mvc.get().uri("/api/todos/99")).hasStatus(404)
                .bodyJson().extractingPath("$.detail").isEqualTo("할 일을 찾을 수 없습니다: 99");
    }
}
```

| 도구 | 하는 일 |
| --- | --- |
| `MockMvcTester` | 실제 서버 없이 Spring MVC에 가짜 HTTP 요청을 보내고, AssertJ 방식으로 응답을 검사한다 (Spring Framework 6.2부터) |
| `@MockitoBean` | 컨테이너의 빈을 Mockito 가짜 객체로 바꿔 끼운다 (예전 `@MockBean`의 후속) |
| `given(...).willReturn(...)` | 가짜 객체의 응답을 정한다 |

이 테스트는 [3편]({{ '/spring/rest-api/' | relative_url }})의 오류 처리기 함정을 잡아낸 테스트이기도 하다. 처리기가 바뀌어 `errors` 필드가 빠지면 바로 실패한다.

## @DataJpaTest: JPA만

엔티티, 리포지토리, 메모리 DB만 띄운다. 각 테스트는 트랜잭션 안에서 실행되고 끝나면 롤백되어, 테스트끼리 데이터가 섞이지 않는다.

```java
@DataJpaTest
class TodoRepositoryTest {

    @Autowired
    TodoRepository repository;

    @Test
    void 완료_여부로_찾기() {
        repository.save(new Todo("장보기"));
        Todo done = repository.save(new Todo("운동"));
        done.complete();
        repository.flush();

        assertThat(repository.findByDoneOrderByCreatedAtDesc(true))
                .extracting(Todo::getTitle).containsExactly("운동");
        assertThat(repository.countByDone(false)).isEqualTo(1);
    }
}
```

`flush()`는 지금까지의 변경을 DB에 SQL로 보낸다. 메서드 이름 쿼리가 실제로 맞는 SQL을 만드는지, 변경 감지가 반영되는지를 실제 DB(여기서는 H2)로 확인한다. 운영 DB가 PostgreSQL이나 MySQL이라면 SQL 방언 차이가 있으므로, Testcontainers로 같은 DB를 컨테이너로 띄워 시험하는 방법을 쓴다.

## @SpringBootTest: 전체

모든 빈을 띄워 실제와 같은 흐름을 시험한다. `@AutoConfigureMockMvc`를 함께 쓰면 `MockMvcTester`로 요청을 보낼 수 있다.

```java
@SpringBootTest
@AutoConfigureMockMvc
class TodoApiIntegrationTest {

    @Autowired
    MockMvcTester mvc;

    @Test
    void 만들고_완료하고_목록에서_확인() {
        var created = mvc.post().uri("/api/todos")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"title\": \"블로그 쓰기\"}").exchange();
        assertThat(created).hasStatus(201);
        String location = created.getResponse().getHeader("Location");

        assertThat(mvc.patch().uri(location + "/complete")).hasStatusOk()
                .bodyJson().extractingPath("$.done").isEqualTo(true);

        assertThat(mvc.get().uri("/api/todos?done=true")).hasStatusOk()
                .bodyJson().extractingPath("$[*].title").asArray().contains("블로그 쓰기");
    }
}
```

`@SpringBootTest`는 기본적으로 테스트마다 롤백하지 않는다. 테스트가 만든 데이터가 다음 테스트에 남을 수 있으므로, 결과를 "정확히 몇 개"보다 "포함한다"로 검사하거나, [5편]({{ '/spring/transaction/' | relative_url }})의 `SelfInvocationTest`처럼 `@BeforeEach`에서 정리한다.

Spring은 같은 설정의 테스트끼리 컨테이너를 재사용(캐시)한다. 테스트 클래스마다 `@MockitoBean` 조합이나 설정이 달라지면 컨테이너를 새로 띄우므로 전체 테스트 시간이 늘어난다. 공통 설정을 묶어 두면 빨라진다.

## 정리

- 로직은 단위 테스트, 계층 경계는 슬라이스 테스트(`@WebMvcTest`, `@DataJpaTest`), 핵심 흐름만 `@SpringBootTest`로 시험한다.
- Boot 4는 기능별 테스트 스타터를 추가하고, 어노테이션 패키지도 기능별로 바뀌었다.
- `MockMvcTester`는 서버 없이 HTTP 요청·응답을 AssertJ로 검사하고, `@MockitoBean`은 빈을 가짜로 바꾼다.
- `@DataJpaTest`는 테스트마다 롤백되고, `@SpringBootTest`는 롤백되지 않으므로 데이터 정리가 필요하다.

## 실습 소스

- [ContainerTest.java]({{ '/assets/examples/spring/todo/src/test/java/com/example/todo/core/ContainerTest.java' | relative_url }})
- [TodoControllerTest.java]({{ '/assets/examples/spring/todo/src/test/java/com/example/todo/todo/TodoControllerTest.java' | relative_url }})
- [TodoRepositoryTest.java]({{ '/assets/examples/spring/todo/src/test/java/com/example/todo/todo/TodoRepositoryTest.java' | relative_url }})
- [TodoApiIntegrationTest.java]({{ '/assets/examples/spring/todo/src/test/java/com/example/todo/todo/TodoApiIntegrationTest.java' | relative_url }})
- [SelfInvocationTest.java]({{ '/assets/examples/spring/todo/src/test/java/com/example/todo/todo/SelfInvocationTest.java' | relative_url }})

## 참고

- [Spring Boot Reference: Testing](https://docs.spring.io/spring-boot/reference/testing/index.html)
- [Spring Framework: MockMvc AssertJ Integration](https://docs.spring.io/spring-framework/reference/testing/mockmvc/assertj.html)
- [Spring Framework: Bean Overriding in Tests](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/bean-overriding.html)
