---
title: "Spring MVC로 REST API 만들기"
description: "@RestController와 요청 매핑, 경로·쿼리 변수, 요청·응답 DTO, @Valid 입력 검증, ProblemDetail로 일관된 오류 응답을 만드는 방법을 할 일 API와 실제 curl 응답으로 설명합니다. Boot 기본 처리기와 충돌하는 함정도 다룹니다."
parent: Spring
nav_order: 3
permalink: /spring/rest-api/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Spring, Spring-MVC, REST, Validation, ProblemDetail]
---

# Spring MVC로 REST API 만들기
{: .no_toc }

{% include article-toc.md %}

**REST API**는 HTTP의 메서드(GET, POST, PATCH, DELETE)와 주소(`/api/todos/1`)로 "무엇을 어떻게 하려는지"를 표현하는 웹 API 설계 방식이다. 앱이나 웹 프런트엔드가 서버와 JSON을 주고받을 때 가장 흔히 쓴다. 이 글에서는 Spring MVC로 할 일 API를 만든다.

| 요청 | 하는 일 | 성공 응답 |
| --- | --- | --- |
| `GET /api/todos` | 목록 (`?done=true`로 거르기) | 200 |
| `GET /api/todos/{id}` | 하나 조회 | 200, 없으면 404 |
| `POST /api/todos` | 만들기 | 201 + `Location` 헤더 |
| `PATCH /api/todos/{id}/complete` | 완료 처리 | 200 |
| `DELETE /api/todos/{id}` | 삭제 | 204 |

## 요청이 처리되는 흐름

```text
HTTP 요청
  → DispatcherServlet (Spring MVC의 입구)
  → 주소와 메서드에 맞는 컨트롤러 메서드 찾기
  → JSON 본문을 Java 객체로 변환, @Valid 검증
  → 컨트롤러 → 서비스 → 리포지토리
  → 반환한 객체를 JSON으로 변환
HTTP 응답
```

**DispatcherServlet**은 모든 요청을 받아 알맞은 컨트롤러 메서드로 나눠 주는 Spring MVC의 중심 객체다. Spring Boot가 자동 구성으로 등록해 주므로 직접 만들 일은 없다.

## 컨트롤러

```java
@RestController
@RequestMapping("/api/todos")
public class TodoController {

    private final TodoService service;

    public TodoController(TodoService service) {
        this.service = service;
    }

    @GetMapping
    public List<Response> list(@RequestParam(required = false) Boolean done) {
        return service.findAll(done).stream().map(Response::from).toList();
    }

    @GetMapping("/{id}")
    public Response get(@PathVariable Long id) {
        return Response.from(service.get(id));
    }

    @PostMapping
    public ResponseEntity<Response> create(@Valid @RequestBody CreateRequest request) {
        Todo todo = service.create(request.title());
        return ResponseEntity.created(URI.create("/api/todos/" + todo.getId())).body(Response.from(todo));
    }

    @PatchMapping("/{id}/complete")
    public Response complete(@PathVariable Long id) {
        return Response.from(service.complete(id));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}
```

| 어노테이션 | 하는 일 |
| --- | --- |
| `@RestController` | 메서드가 돌려준 객체를 JSON 응답 본문으로 쓴다 |
| `@RequestMapping("/api/todos")` | 이 클래스의 모든 주소 앞에 붙는 공통 경로 |
| `@GetMapping`, `@PostMapping` ... | HTTP 메서드와 주소를 메서드에 연결 |
| `@PathVariable` | 주소의 `{id}` 부분을 매개변수로 |
| `@RequestParam` | `?done=true` 같은 쿼리 문자열을 매개변수로 |
| `@RequestBody` | JSON 본문을 객체로 |
| `ResponseEntity` | 상태 코드와 헤더를 직접 정할 때 |

컨트롤러는 HTTP와 관련된 일(주소, 상태 코드, 변환)만 하고, 실제 처리는 서비스에 맡긴다. 그래야 같은 기능을 다른 입구(배치 작업, 메시지 큐)에서도 재사용할 수 있다.

## 요청·응답 DTO

엔티티(`Todo`)를 그대로 JSON으로 내보내지 않고, 주고받을 모양을 따로 정한다. 이런 객체를 **DTO(Data Transfer Object)**라고 한다. Java의 `record`로 짧게 쓸 수 있다.

```java
public record CreateRequest(
        @NotBlank(message = "제목은 비어 있을 수 없습니다")
        @Size(max = 100, message = "제목은 100자 이하여야 합니다")
        String title) {}

public record Response(Long id, String title, boolean done, Instant createdAt) {
    static Response from(Todo todo) {
        return new Response(todo.getId(), todo.getTitle(), todo.isDone(), todo.getCreatedAt());
    }
}
```

엔티티를 바로 노출하면 DB 구조가 바뀔 때 API도 함께 바뀌고, 비밀번호 같은 내부 필드가 실수로 나가거나, 클라이언트가 보내면 안 되는 필드(`id`, `done`)를 요청 본문으로 바꿀 위험이 생긴다. 요청 DTO에는 클라이언트가 정할 수 있는 값만 둔다.

## 실제로 호출해 보기

앱을 실행하고 curl로 호출한 실제 응답이다.

```bash
curl -i -X POST localhost:8089/api/todos -H 'Content-Type: application/json' -d '{"title":"장보기"}'
```

```text
HTTP/1.1 201
Location: /api/todos/1
{"id":1,"title":"장보기","done":false,"createdAt":"2026-11-27T11:41:53.056935102Z"}
```

```bash
curl -X POST localhost:8089/api/todos -H 'Content-Type: application/json' -d '{"title":"운동"}'
curl -X PATCH localhost:8089/api/todos/2/complete
curl "localhost:8089/api/todos?done=true"
```

```json
{"id":2,"title":"운동","done":false,"createdAt":"2026-11-27T11:41:53.181693364Z"}
{"id":2,"title":"운동","done":true,"createdAt":"2026-11-27T11:41:53.181693Z"}
[{"id":2,"title":"운동","done":true,"createdAt":"2026-11-27T11:41:53.181693Z"}]
```

`createdAt`의 소수점 자릿수가 만들 때와 다시 읽을 때 다른 것이 보인다. 만들 때는 Java의 `Instant` 값을 그대로 돌려줬고, 다시 읽을 때는 DB에 저장된 값(마이크로초 정밀도)을 읽었기 때문이다. 시간 값을 비교하는 코드가 있다면 이런 정밀도 차이를 염두에 둔다.

## 입력 검증

`CreateRequest`의 `@NotBlank`, `@Size`는 **Bean Validation**(Jakarta Validation) 규칙이다. 컨트롤러 매개변수에 `@Valid`를 붙이면 Spring이 메서드를 호출하기 전에 검사하고, 어기면 `MethodArgumentNotValidException`을 던진다.

| 어노테이션 | 검사 |
| --- | --- |
| `@NotNull` | null 아님 |
| `@NotBlank` | null 아니고 공백만도 아님 (문자열) |
| `@Size(min, max)` | 길이·개수 |
| `@Min`, `@Max` | 숫자 범위 |
| `@Email`, `@Pattern` | 형식 |

## 오류 응답을 일관되게: ProblemDetail

오류마다 응답 모양이 다르면 클라이언트가 처리하기 어렵다. **ProblemDetail**은 HTTP API의 오류 응답 형식을 정한 표준(RFC 9457)을 Spring이 구현한 클래스다. 응답의 `Content-Type`은 `application/problem+json`이고, `status`, `title`, `detail` 같은 정해진 필드를 가진다.

```java
@RestControllerAdvice
public class ApiExceptionHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler(TodoNotFoundException.class)
    public ProblemDetail notFound(TodoNotFoundException e) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, e.getMessage());
        problem.setTitle("Todo Not Found");
        return problem;
    }

    // @Valid 검증 실패: 기본 응답에 필드별 오류를 더한다
    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
            MethodArgumentNotValidException e, HttpHeaders headers, HttpStatusCode status, WebRequest request) {
        Map<String, String> errors = e.getBindingResult().getFieldErrors().stream()
                .collect(Collectors.toMap(FieldError::getField, FieldError::getDefaultMessage, (a, b) -> a));
        ProblemDetail problem = e.getBody();
        problem.setDetail("입력값을 확인하세요");
        problem.setProperty("errors", errors);
        return handleExceptionInternal(e, problem, headers, status, request);
    }
}
```

`@RestControllerAdvice`는 모든 컨트롤러에서 던진 예외를 한곳에서 처리하는 클래스라는 표시다. 서비스는 "없다"는 사실만 `TodoNotFoundException`으로 알리고, 그것을 404로 바꾸는 일은 이 클래스가 맡는다.

실제 응답이다.

```text
$ curl -i localhost:8089/api/todos/99
HTTP/1.1 404
Content-Type: application/problem+json
{"detail":"할 일을 찾을 수 없습니다: 99","status":404,"title":"Todo Not Found"}

$ curl -i -X POST localhost:8089/api/todos -H 'Content-Type: application/json' -d '{"title":""}'
HTTP/1.1 400
{"detail":"입력값을 확인하세요","status":400,"title":"Bad Request","errors":{"title":"제목은 비어 있을 수 없습니다"}}
```

### 함정: 내 처리기가 동작하지 않을 때

처음에는 `ResponseEntityExceptionHandler`를 상속하지 않고, 404 처리 메서드 옆에 `@ExceptionHandler(MethodArgumentNotValidException.class)` 메서드를 그냥 추가했다. 테스트를 돌리자 400 응답이 이렇게 나왔다.

```json
{"detail":"Invalid request content.","status":400,"title":"Bad Request"}
```

내 처리기가 아니라 다른 처리기가 응답한 것이다. `spring.mvc.problemdetails.enabled: true`를 켜 두면 Boot가 Spring MVC의 표준 예외들을 ProblemDetail로 바꾸는 기본 처리기(`ResponseEntityExceptionHandler`를 상속한 클래스)를 등록하는데, 이 처리기가 같은 예외를 먼저 잡았다. 404 처리는 Boot 처리기가 모르는 내 예외라서 문제없이 동작했기 때문에 원인을 찾기 더 어려웠다.

해결은 위 코드처럼 **내 처리기가 `ResponseEntityExceptionHandler`를 상속**하는 것이다. 이 타입의 빈을 개발자가 직접 만들면 Boot의 기본 처리기는 물러난다([2편]({{ '/spring/spring-boot/' | relative_url }})의 "직접 만들지 않았다면" 규칙). 그리고 표준 예외는 상속한 메서드를 재정의해 원하는 정보를 더한다. 같은 예외를 처리하는 곳이 두 군데 생기지 않게 하는 것이 핵심이다.

## 상태 코드 고르기

| 상황 | 코드 |
| --- | --- |
| 조회 성공 | 200 OK |
| 만들기 성공 | 201 Created + `Location` |
| 삭제 성공, 본문 없음 | 204 No Content |
| 입력 형식·검증 오류 | 400 Bad Request |
| 인증 안 됨 / 권한 없음 | 401 / 403 |
| 대상 없음 | 404 Not Found |
| 현재 상태와 충돌(이미 완료됨 등) | 409 Conflict |
| 서버 오류 | 500 (내부 정보는 응답에 넣지 않는다) |

## 정리

- `@RestController`와 매핑 어노테이션으로 HTTP 메서드·주소를 메서드에 연결한다. 컨트롤러는 HTTP 일만 하고 처리는 서비스에 맡긴다.
- 엔티티 대신 요청·응답 DTO(`record`)를 쓴다.
- `@Valid`와 Bean Validation 어노테이션으로 입력을 검증한다.
- `@RestControllerAdvice`와 ProblemDetail로 오류 응답 형식을 통일한다.
- 표준 예외 처리를 바꾸려면 `ResponseEntityExceptionHandler`를 상속해 재정의한다. 같은 예외를 따로 잡으면 Boot의 기본 처리기가 먼저 응답할 수 있다.

## 실습 소스

- [TodoController.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/TodoController.java' | relative_url }})
- [TodoDtos.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/TodoDtos.java' | relative_url }})
- [ApiExceptionHandler.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/ApiExceptionHandler.java' | relative_url }})
- [TodoNotFoundException.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/todo/TodoNotFoundException.java' | relative_url }})

## 참고

- [Spring Framework: Annotated Controllers](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller.html)
- [Spring Framework: Error Responses (ProblemDetail)](https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html)
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)
- [Jakarta Bean Validation](https://beanvalidation.org/)
