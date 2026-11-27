---
title: "Spring Boot 시작하기"
description: "Spring Boot 프로젝트의 구조와 스타터, 자동 구성이 하는 일, application.yml 설정과 프로파일, 실행 가능한 jar와 Actuator 상태 확인을 Spring Boot 4.2.0 예제를 실제로 실행한 결과로 설명합니다."
parent: Spring
nav_order: 2
permalink: /spring/spring-boot/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Spring, Spring-Boot, Auto-Configuration, Actuator]
---

# Spring Boot 시작하기
{: .no_toc }

{% include article-toc.md %}

[1편]({{ '/spring/ioc-di/' | relative_url }})에서는 컨테이너를 직접 만들고 설정 클래스를 넘겼다. 실제 웹 서비스를 만들려면 여기에 웹 서버, JSON 변환, 데이터베이스 연결, 로그 설정까지 해야 한다. 이 설정들은 프로젝트마다 거의 같다.

**Spring Boot**는 이 반복되는 준비를 대신한다. 필요한 라이브러리를 고르면 그에 맞는 기본 설정을 알아서 만들고, 웹 서버까지 내장해 `java -jar` 한 줄로 실행되는 애플리케이션을 만든다.

## 프로젝트 만들기

[start.spring.io](https://start.spring.io)에서 빌드 도구, Java 버전, 필요한 기능(의존성)을 고르면 프로젝트 뼈대를 내려받을 수 있다. IntelliJ IDEA의 새 프로젝트 마법사도 같은 서비스를 쓴다. 이 연재의 `pom.xml` 핵심은 이렇다.

```xml
<parent>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-parent</artifactId>
  <version>4.2.0</version>
</parent>

<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-webmvc</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-jpa</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
  </dependency>
  <dependency>
    <groupId>com.h2database</groupId>
    <artifactId>h2</artifactId>
    <scope>runtime</scope>
  </dependency>
  <!-- 테스트 스타터는 6편에서 -->
</dependencies>
```

### 부모 POM과 스타터

- **`spring-boot-starter-parent`**: 수백 개 라이브러리의 서로 맞는 버전을 정해 둔 부모 설정이다. 그래서 각 의존성에 버전을 적지 않는다. Boot 버전 하나만 올리면 함께 검증된 버전 조합으로 바뀐다.
- **스타터(starter)**: 기능 하나에 필요한 라이브러리를 묶은 의존성이다. `spring-boot-starter-webmvc` 하나에 Spring MVC, 내장 Tomcat, JSON 처리(Jackson)가 함께 들어온다.

Spring Boot 4부터는 모듈이 기능별로 잘게 나뉘었다. Spring MVC용 웹 스타터의 새 이름은 `spring-boot-starter-webmvc`이고(Boot 3까지는 `spring-boot-starter-web`), 테스트도 `spring-boot-starter-webmvc-test`처럼 기능별 테스트 스타터를 추가하는 방식이 됐다. 인터넷의 Boot 3 예제를 따라 할 때 이 차이를 기억해 둔다.

## 진입점

```java
@SpringBootApplication
public class TodoApplication {
    public static void main(String[] args) {
        SpringApplication.run(TodoApplication.class, args);
    }
}
```

`@SpringBootApplication`은 세 가지를 합친 것이다.

| 포함된 것 | 하는 일 |
| --- | --- |
| `@Configuration` | 이 클래스도 설정 클래스다 |
| `@ComponentScan` | 이 클래스가 있는 패키지와 그 아래를 스캔해 빈을 등록한다 |
| `@EnableAutoConfiguration` | 자동 구성을 켠다 |

컴포넌트 스캔은 진입점 클래스의 패키지부터 시작하므로, 진입점을 최상위 패키지(`com.example.todo`)에 두고 다른 클래스는 그 아래에 둔다. 진입점과 다른 패키지 줄기에 둔 `@Service`는 등록되지 않는다.

## 자동 구성: Boot가 대신 만드는 빈

**자동 구성(auto-configuration)**은 "클래스패스에 이 라이브러리가 있고, 개발자가 같은 빈을 직접 만들지 않았다면, 기본 빈을 만들어 준다"는 규칙의 모음이다.

| 클래스패스에 있으면 | Boot가 만드는 것 |
| --- | --- |
| Spring MVC + Tomcat | 내장 웹 서버, 요청 분배기(DispatcherServlet), JSON 변환기 |
| JPA + H2 | 메모리 DB 연결(DataSource), JPA 설정, 트랜잭션 관리자 |
| Bean Validation | `@Valid` 검증기 |
| Actuator | `/actuator/health` 같은 운영용 엔드포인트 |

핵심은 **"직접 만들지 않았다면"**이다. 개발자가 같은 종류의 빈을 등록하면 Boot는 물러난다. [3편]({{ '/spring/rest-api/' | relative_url }})에서 오류 처리기를 직접 만들었을 때 Boot의 기본 처리기가 물러나는 것을 실제로 보게 된다.

어떤 자동 구성이 적용됐고 왜 빠졌는지 궁금하면 `--debug`로 실행한다. 시작 로그에 조건 평가 보고서(Conditions Evaluation Report)가 찍힌다.

## 설정: application.yml

```yaml
spring:
  application:
    name: todo
  datasource:
    url: jdbc:h2:mem:todo
  jpa:
    open-in-view: false
    show-sql: false
logging:
  level:
    org.hibernate.SQL: debug
```

| 설정 | 뜻 |
| --- | --- |
| `spring.datasource.url` | DB 주소. 여기서는 메모리 DB(H2)라 앱을 끄면 데이터가 사라진다 |
| `spring.jpa.open-in-view: false` | 웹 요청이 끝날 때까지 DB 연결을 붙잡지 않게 한다. 4편에서 설명 |
| `logging.level.org.hibernate.SQL: debug` | 실행되는 SQL을 로그로 본다 |

같은 설정을 환경에 따라 바꿔야 할 때가 많다. Boot는 여러 곳의 설정을 정해진 우선순위로 합친다. 대표적인 순서는 이렇다(아래로 갈수록 우선).

1. `application.yml`
2. `application-{프로파일}.yml` (예: `application-prod.yml`)
3. 환경 변수 (`SPRING_DATASOURCE_URL`)
4. 명령줄 인자 (`--server.port=8089`)

비밀번호 같은 값은 파일에 적지 않고 환경 변수나 비밀 관리 도구로 넣는다. **프로파일**은 `--spring.profiles.active=prod`처럼 켜며, 개발·운영 설정을 나눌 때 쓴다.

## 실행하기

```bash
mvn package
java -jar target/todo-0.0.1.jar --server.port=8089
```

`mvn package`는 테스트를 돌린 뒤 라이브러리와 내장 Tomcat까지 모두 담은 **실행 가능한 jar**(fat jar)를 만든다. 이 예제는 약 57MB가 나왔다. 서버에 Tomcat을 따로 설치할 필요가 없다.

실제 시작 로그의 일부다.

```text
 :: Spring Boot ::                (v4.2.0)
o.s.boot.tomcat.TomcatWebServer          : Tomcat started on port 8089 (http) with context path '/'
com.example.todo.TodoApplication         : Started TodoApplication in 4.785 seconds (process running for 5.291)
```

## 운영 기능: Actuator

Actuator 스타터를 넣으면 애플리케이션 상태를 확인하는 엔드포인트가 생긴다.

```bash
curl localhost:8089/actuator/health
```

```json
{"groups":["liveness","readiness"],"status":"UP"}
```

`status`가 `UP`이면 앱과 DB 연결이 정상이라는 뜻이다. 로드 밸런서나 Kubernetes는 이 주소로 서버 상태를 확인한다. `liveness`(살아 있나)와 `readiness`(요청을 받을 준비가 됐나)를 나눠 볼 수도 있다. 기본으로는 `health`만 웹에 공개되며, 메트릭이나 환경 정보 같은 다른 엔드포인트는 `management.endpoints.web.exposure.include`로 골라 공개한다. 환경 정보에는 비밀 값이 섞일 수 있으므로 외부에 그대로 공개하지 않는다.

## 정리

- Spring Boot는 스타터(라이브러리 묶음), 자동 구성(기본 빈), 내장 서버로 Spring 애플리케이션의 반복 준비를 없앤다.
- 부모 POM이 라이브러리 버전 조합을 관리하므로 Boot 버전 하나만 관리하면 된다. Boot 4는 모듈이 기능별로 나뉘어 스타터 이름이 일부 바뀌었다.
- `@SpringBootApplication`은 설정 + 컴포넌트 스캔 + 자동 구성이며, 진입점 패키지 아래만 스캔한다.
- 자동 구성은 개발자가 같은 빈을 만들면 물러난다.
- 설정은 파일 → 프로파일 파일 → 환경 변수 → 명령줄 순으로 덮어쓴다.
- `mvn package`로 만든 jar 하나로 실행하고, Actuator로 상태를 확인한다.

## 실습 소스

- [pom.xml]({{ '/assets/examples/spring/todo/pom.xml' | relative_url }})
- [TodoApplication.java]({{ '/assets/examples/spring/todo/src/main/java/com/example/todo/TodoApplication.java' | relative_url }})
- [application.yml]({{ '/assets/examples/spring/todo/src/main/resources/application.yml' | relative_url }})

## 참고

- [Spring Boot Reference: Auto-configuration](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html)
- [Spring Boot Reference: Externalized Configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html)
- [Spring Boot Reference: Actuator Endpoints](https://docs.spring.io/spring-boot/reference/actuator/endpoints.html)
- [Spring Boot 4.0 Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide)
