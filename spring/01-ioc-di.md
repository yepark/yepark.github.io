---
title: "IoC 컨테이너와 의존성 주입"
description: "Spring의 출발점인 IoC 컨테이너와 의존성 주입(DI)을 직접 조립하는 코드와 비교해 설명합니다. 빈, @Configuration과 @Bean, 컴포넌트 스캔, 생성자 주입, 싱글턴 스코프를 실행 결과로 확인합니다."
parent: Spring
nav_order: 1
permalink: /spring/ioc-di/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Spring, IoC, DI, Bean]
---

# IoC 컨테이너와 의존성 주입
{: .no_toc }

{% include article-toc.md %}

할 일 앱에 "마감 전에 알림을 보낸다"는 기능을 넣는다고 하자. 지금은 이메일로 보내지만, 나중에는 문자나 앱 푸시로 바꿀 수도 있다. 알림 기능이 이메일 발송 코드를 직접 만들어 쓰면, 발송 방법을 바꿀 때마다 알림 기능 코드도 고쳐야 한다.

Spring의 가장 기본이 되는 생각은 이 문제에서 출발한다. **객체가 필요한 다른 객체를 직접 만들지 말고, 밖에서 넣어 받자.** 이것을 **의존성 주입(DI, Dependency Injection)**이라고 하고, 객체를 만들고 연결하는 일을 대신 맡아 주는 것을 **IoC 컨테이너**라고 한다.

## 의존성이란

`ReminderService`가 알림을 보내려면 메시지를 보내는 객체가 필요하다. 이때 "`ReminderService`는 `MessageSender`에 **의존**한다"고 말한다.

```java
public interface MessageSender {
    String send(String to, String text);
}

public class EmailSender implements MessageSender {
    @Override
    public String send(String to, String text) {
        return "email to " + to + ": " + text;
    }
}

public class SmsSender implements MessageSender {
    @Override
    public String send(String to, String text) {
        return "sms to " + to + ": " + text;
    }
}
```

### 직접 만들면 생기는 문제

```java
public class ReminderService {
    private final MessageSender sender = new EmailSender(); // 직접 생성

    public String remind(String user, String task) {
        return sender.send(user, "잊지 마세요: " + task);
    }
}
```

이 코드는 `EmailSender`에 묶여 있다. 문자로 바꾸려면 `ReminderService`를 고쳐야 하고, 테스트할 때 진짜 이메일 대신 가짜 발송기를 넣을 방법도 없다.

### 생성자로 받기

```java
public class ReminderService {
    private final MessageSender sender;

    // 필요한 객체를 직접 만들지 않고 생성자로 받는다
    public ReminderService(MessageSender sender) {
        this.sender = sender;
    }

    public String remind(String user, String task) {
        return sender.send(user, "잊지 마세요: " + task);
    }
}
```

이제 `ReminderService`는 `MessageSender`라는 **약속(인터페이스)**만 안다. 어떤 구현을 쓸지는 이 객체를 만드는 쪽이 정한다. 이것이 의존성 주입이다. 프레임워크가 없어도 할 수 있다.

```java
ReminderService service = new ReminderService(new SmsSender());
service.remind("kim", "보고서");   // "sms to kim: 잊지 마세요: 보고서"
```

## 컨테이너가 조립하게 하기

객체가 수십, 수백 개가 되면 "누가 누구를 만들어 어디에 넣는지"를 `main` 함수에서 손으로 관리하기 어려워진다. **IoC(Inversion of Control, 제어의 역전) 컨테이너**는 이 조립을 대신한다. 원래는 내 코드가 객체를 만들고 연결했는데, 그 제어권이 컨테이너로 넘어갔다고 해서 "제어의 역전"이라고 부른다.

컨테이너가 만들고 관리하는 객체를 **빈(bean)**이라고 한다. 어떤 빈을 어떻게 만들지는 설정 클래스에 적는다.

```java
@Configuration
public class AppConfig {
    @Bean
    public MessageSender messageSender() {
        return new EmailSender();
    }

    @Bean
    public ReminderService reminderService(MessageSender messageSender) {
        return new ReminderService(messageSender);
    }
}
```

- `@Configuration`: 빈 설정을 담은 클래스라는 표시
- `@Bean`: 이 메서드가 돌려주는 객체를 빈으로 등록한다. 메서드 이름이 빈 이름이 된다
- `reminderService(MessageSender messageSender)`: 매개변수에 필요한 빈을 적으면 컨테이너가 찾아서 넣어 준다

컨테이너를 만들어 빈을 꺼내 보자.

```java
try (var context = new AnnotationConfigApplicationContext(AppConfig.class)) {
    ReminderService service = context.getBean(ReminderService.class);
    System.out.println(service.remind("kim", "보고서"));
    System.out.println(Arrays.stream(context.getBeanDefinitionNames())
            .filter(n -> !n.startsWith("org.springframework")).toList());
    System.out.println(context.getBean(ReminderService.class) == service);
}
```

```text
email to kim: 잊지 마세요: 보고서
[appConfig, messageSender, reminderService]
true
```

컨테이너는 `AppConfig`를 읽어 `messageSender`와 `reminderService` 빈을 만들고, `reminderService`를 만들 때 `messageSender`를 넣어 주었다. 발송 방법을 문자로 바꾸려면 `AppConfig`의 한 줄만 고치면 된다. `ReminderService`는 그대로다.

## 싱글턴 스코프

마지막 줄이 `true`다. 같은 빈을 두 번 꺼냈는데 같은 객체였다. Spring 빈은 기본적으로 컨테이너당 **하나만** 만들어진다(싱글턴 스코프). 웹 서버에서 요청이 수천 개 들어와도 `TodoService` 객체는 하나이고, 모든 요청이 그 하나를 함께 쓴다.

그래서 빈에는 **요청마다 달라지는 값을 필드에 저장하면 안 된다.** 여러 요청이 동시에 같은 필드를 고치면 값이 섞인다([데이터 경쟁]({{ '/swift/concurrency/actor/' | relative_url }})과 같은 문제). 빈은 보통 다른 빈에 대한 참조만 필드로 두고, 요청별 데이터는 메서드의 매개변수와 지역 변수로 다룬다.

필요하면 다른 스코프를 쓸 수 있다.

| 스코프 | 객체 개수 |
| --- | --- |
| singleton (기본) | 컨테이너에 하나 |
| prototype | 꺼낼 때마다 새로 |
| request | HTTP 요청마다 하나 |
| session | HTTP 세션마다 하나 |

## 컴포넌트 스캔: 설정 클래스 없이 등록하기

빈마다 `@Bean` 메서드를 쓰는 것은 번거롭다. 클래스에 표시만 해 두면 컨테이너가 패키지를 뒤져(스캔해) 자동으로 등록하게 할 수 있다.

| 어노테이션 | 쓰는 곳 |
| --- | --- |
| `@Component` | 일반 빈 |
| `@Service` | 비즈니스 로직 |
| `@Repository` | 데이터 접근 |
| `@Controller` / `@RestController` | 웹 요청 처리 |
| `@Configuration` | 설정 클래스 |

`@Service`, `@Repository` 등은 모두 `@Component`의 다른 이름이다. 기능 차이보다는 역할을 드러내는 표시라고 보면 된다(`@Repository`는 데이터베이스 예외를 Spring 예외로 바꿔 주는 기능이 더 있다).

연재의 할 일 서비스는 이렇게 등록된다.

```java
@Service
public class TodoService {

    private final TodoRepository repository;

    public TodoService(TodoRepository repository) {
        this.repository = repository;
    }
    ...
}
```

생성자가 하나뿐이면 `@Autowired`를 붙이지 않아도 컨테이너가 그 생성자로 의존성을 넣어 준다.

## 주입 방법은 생성자로

의존성을 넣는 방법은 세 가지다.

| 방법 | 예 | 권장 |
| --- | --- | --- |
| 생성자 주입 | 생성자 매개변수 | **권장** |
| 세터 주입 | `@Autowired setX(...)` | 선택적 의존성에만 |
| 필드 주입 | `@Autowired private X x;` | 피함 |

생성자 주입을 쓰면 필드를 `final`로 만들 수 있어 객체가 만들어진 뒤 바뀌지 않고, 필요한 의존성이 빠지면 객체 자체를 만들 수 없어 실수가 바로 드러난다. 무엇보다 Spring 없이 `new`로 만들어 테스트할 수 있다. 앞의 `new ReminderService(new SmsSender())`가 그 예다.

## 같은 타입의 빈이 여럿이면

`EmailSender`와 `SmsSender`를 둘 다 빈으로 등록하면, `MessageSender`를 원하는 곳에서 컨테이너는 무엇을 넣어야 할지 모른다. 시작할 때 "`MessageSender` 타입 빈이 2개"라는 오류가 난다. 해결 방법은 이렇다.

- 기본으로 쓸 빈에 `@Primary`를 붙인다.
- 받는 쪽에서 `@Qualifier("smsSender")`로 이름을 지정한다.
- `List<MessageSender>`로 받아 전부 쓴다(여러 채널로 동시에 알림 보내기 등).

## 정리

- 의존성 주입은 객체가 필요한 다른 객체를 직접 만들지 않고 밖에서 받는 것이다. 프레임워크 없이도 생성자로 할 수 있다.
- IoC 컨테이너는 객체(빈)를 만들고 의존성을 연결하는 일을 대신한다.
- `@Configuration` + `@Bean`으로 직접 등록하거나, `@Component` 계열 어노테이션과 컴포넌트 스캔으로 자동 등록한다.
- 빈은 기본이 싱글턴이므로 요청마다 달라지는 값을 필드에 두지 않는다.
- 생성자 주입을 기본으로 쓴다.

## 실습 소스

- [MessageSender.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/core/MessageSender.java' | relative_url }}), [EmailSender.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/core/EmailSender.java' | relative_url }}), [SmsSender.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/core/SmsSender.java' | relative_url }})
- [ReminderService.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/core/ReminderService.java' | relative_url }}), [AppConfig.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/core/AppConfig.java' | relative_url }})
- [ContainerTest.java]({{ '/assets/examples/spring/todo/src/test/java/com/example/todo/core/ContainerTest.java' | relative_url }}): 위 실행 결과를 확인하는 테스트

## 참고

- [Spring Framework: The IoC Container](https://docs.spring.io/spring-framework/reference/core/beans.html)
- [Spring Framework: Dependency Injection](https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html)
