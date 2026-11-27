---
title: "Spring"
nav_order: 6
has_children: true
has_toc: false
permalink: /spring/
last_modified_date: 2026-11-27
---

# Spring

**Spring**은 Java(와 Kotlin)로 서버 애플리케이션을 만들 때 가장 널리 쓰이는 프레임워크다. 핵심은 객체를 누가 만들고 서로 어떻게 연결할지를 개발자 대신 관리해 주는 **컨테이너**이고, 그 위에 웹, 데이터베이스, 트랜잭션, 보안, 테스트를 위한 모듈이 얹혀 있다.

**Spring Boot**는 Spring으로 실제 서비스를 빨리 시작할 수 있게 해 주는 도구다. 필요한 라이브러리 묶음(스타터), 상황에 맞는 기본 설정(자동 구성), 내장 웹 서버를 제공해서 `java -jar` 한 줄로 서버가 뜬다. 지금 새로 시작하는 Spring 프로젝트는 대부분 Spring Boot로 만든다.

이 연재는 **할 일(Todo) 관리 REST API** 하나를 만들어 가며 Spring의 핵심을 차례로 다룬다. 모든 예제는 아래 환경에서 실제로 빌드하고 테스트를 통과시킨 코드이며, 글에 실린 응답과 로그도 실제 실행 결과다.

| 항목 | 버전 |
| --- | --- |
| Spring Boot | 4.2.0 |
| Spring Framework | 7.1.0 |
| Spring Data JPA / Hibernate | 4.2.0 / 7.4 |
| Java | 21 (Boot 4는 Java 17 이상 필요) |
| 빌드 도구 | Maven 3.9 |

{% include series-list.html heading="연재 목차" %}

## 예제 프로젝트 받기

연재 전체에서 쓰는 프로젝트다. 파일을 같은 폴더 구조로 내려받아 실행한다.

```text
todo/
├── pom.xml
└── src/
    ├── main/java/com/example/todo/
    │   ├── TodoApplication.java
    │   ├── core/   (1편: 컨테이너와 DI)
    │   └── todo/   (3~5편: REST API, JPA, 트랜잭션)
    ├── main/resources/application.yml
    └── test/java/com/example/todo/  (6편: 테스트)
```

```bash
mvn test                              # 테스트 10개 실행
mvn package                           # target/todo-0.0.1.jar 생성
java -jar target/todo-0.0.1.jar       # http://localhost:8080 에서 실행
```

- [pom.xml]({{ '/assets/examples/spring/todo/pom.xml' | relative_url }})
- [application.yml]({{ '/assets/examples/spring/todo/src/main/resources/application.yml' | relative_url }})
- 소스 파일 링크는 각 글의 "실습 소스"에 있다.

## Spring 생태계에서 이 연재가 다루는 범위

| 모듈 | 하는 일 | 다루는 글 |
| --- | --- | --- |
| Spring Framework (Core) | 컨테이너, DI, AOP | 1편 |
| Spring Boot | 자동 구성, 내장 서버, 설정, 운영 기능 | 2편 |
| Spring MVC | HTTP 요청을 받아 응답하는 웹 계층 | 3편 |
| Spring Data JPA | 데이터베이스 접근 | 4편 |
| Spring 트랜잭션 | 여러 DB 작업을 하나로 묶기 | 5편 |
| Spring Test | 계층별 테스트 | 6편 |
| Spring Security | 인증·인가 | 7편 (별도 예제) |

이 밖에 Spring Batch(대량 일괄 처리), Spring Cloud(마이크로서비스), Spring AI(LLM 연동) 같은 모듈이 있다.
