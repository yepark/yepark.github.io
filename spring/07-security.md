---
title: "Spring Security 기초"
description: "인증과 인가의 차이, Spring Security의 필터 체인 구조, SecurityFilterChain 설정, 비밀번호 저장(BCrypt), 401과 403, @PreAuthorize 메서드 보안, CSRF와 세션 정책을 작은 예제와 실제 curl 응답·테스트로 설명합니다."
parent: Spring
nav_order: 7
permalink: /spring/security/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [Spring, Spring-Security, Authentication, Authorization]
---

# Spring Security 기초
{: .no_toc }

{% include article-toc.md %}

지금까지 만든 할 일 API는 누구나 호출할 수 있다. 실제 서비스라면 "로그인한 사람만 자기 목록을 보고, 관리자만 삭제할 수 있다" 같은 규칙이 필요하다. **Spring Security**는 Spring 애플리케이션에 이런 보안 규칙을 거는 표준 모듈이다.

## 인증과 인가

보안 규칙은 두 질문으로 나뉜다.

| | 질문 | 실패하면 |
| --- | --- | --- |
| **인증(Authentication)** | 너는 누구냐? (로그인) | 401 Unauthorized |
| **인가(Authorization)** | 너는 이걸 해도 되냐? (권한) | 403 Forbidden |

건물로 비유하면 인증은 출입증 확인, 인가는 "이 층에 들어갈 권한이 있나" 확인이다. 401은 이름과 달리 "인증 안 됨"이고, 403이 "권한 없음"이다.

## 동작 방식: 필터 체인

Spring Security는 컨트롤러 앞에 **필터(filter)** 여러 개를 줄 세워 둔다. 요청은 컨트롤러에 닿기 전에 이 필터들을 차례로 지나며, 인증 정보를 읽고, 규칙을 검사하고, 통과하지 못하면 그 자리에서 401이나 403으로 돌려보낸다.

```text
HTTP 요청
 → [인증 정보 읽기 필터 (Basic, 세션, JWT 등)]
 → [예외를 401/403 응답으로 바꾸는 필터]
 → [주소별 권한 검사 필터]
 → DispatcherServlet → 컨트롤러 (@PreAuthorize 검사)
```

스타터(`spring-boot-starter-security`)를 추가하기만 해도 Boot의 자동 구성이 모든 주소에 로그인을 요구하고, 시작할 때 무작위 비밀번호를 로그에 찍는다. 실제 규칙은 `SecurityFilterChain` 빈을 직접 만들어 정한다. 직접 만들면 Boot의 기본 설정은 물러난다.

## 설정

예제는 공개 주소 하나, 로그인한 사용자용 조회 하나, 관리자 전용 삭제 하나를 가진 작은 API다.

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain api(HttpSecurity http) throws Exception {
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .anyRequest().authenticated())
            .httpBasic(Customizer.withDefaults())
            .csrf(csrf -> csrf.disable()) // 브라우저 쿠키를 쓰지 않는 API 전용 서버이므로
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
        return http.build();
    }

    @Bean
    PasswordEncoder passwordEncoder() {
        return PasswordEncoderFactories.createDelegatingPasswordEncoder();
    }

    @Bean
    UserDetailsService users(PasswordEncoder encoder) {
        var user = User.withUsername("kim").password(encoder.encode("user-pass")).roles("USER").build();
        var admin = User.withUsername("lee").password(encoder.encode("admin-pass")).roles("USER", "ADMIN").build();
        return new InMemoryUserDetailsManager(user, admin);
    }
}
```

| 설정 | 뜻 |
| --- | --- |
| `authorizeHttpRequests` | 주소별 규칙. 위에서부터 처음 맞는 규칙이 적용된다 |
| `permitAll()` / `authenticated()` | 누구나 / 로그인한 사람만 |
| `httpBasic` | `Authorization: Basic base64(아이디:비밀번호)` 헤더로 인증 |
| `csrf.disable()` | 쿠키 기반 로그인을 쓰지 않는 API라 CSRF 방어를 끈다 (아래 설명) |
| `STATELESS` | 서버에 로그인 세션을 만들지 않는다. 요청마다 인증 정보를 보낸다 |
| `UserDetailsService` | 사용자 정보를 찾는 곳. 예제는 메모리, 실제로는 DB |

규칙은 순서가 중요하다. `anyRequest().authenticated()`를 맨 위에 두면 그 아래의 `permitAll()`은 적용되지 않는다. 좁은 규칙을 먼저, 넓은 규칙을 나중에 둔다.

## 비밀번호는 해시로 저장한다

비밀번호를 DB에 그대로 저장하면, DB가 유출되는 순간 모든 사용자의 비밀번호가 드러난다. 그래서 되돌릴 수 없는 **해시**로 바꿔 저장하고, 로그인할 때 입력값을 같은 방식으로 해시해 비교한다.

`PasswordEncoderFactories.createDelegatingPasswordEncoder()`는 기본으로 **BCrypt**를 쓴다. 실제로 저장된 값의 앞부분이다.

```text
{bcrypt}$2a$10$mb0We...
```

| 부분 | 뜻 |
| --- | --- |
| `{bcrypt}` | 어떤 알고리즘으로 만들었는지. 나중에 알고리즘을 바꿔도 예전 값을 읽을 수 있다 |
| `$2a$` | BCrypt 버전 |
| `10` | 비용(반복 횟수의 지수). 클수록 계산이 느려져 무차별 대입이 어렵다 |
| 나머지 | salt와 해시 값 |

같은 비밀번호라도 salt가 매번 달라 저장값이 달라진다. 패스워드 저장 해시의 원리는 [PKCS #5]({{ '/pki/pkcs5/' | relative_url }}) 글의 PBKDF2·Argon2 설명과 같다.

## 실제로 호출해 보기

```text
$ curl -i localhost:8090/api/public/hello
HTTP/1.1 200
{"message":"누구나 볼 수 있음"}

$ curl -i localhost:8090/api/notes
HTTP/1.1 401
WWW-Authenticate: Basic realm="Realm", charset="UTF-8"

$ curl -i -u kim:user-pass localhost:8090/api/notes
HTTP/1.1 200
{"user":"kim","notes":["장보기","운동"]}

$ curl -i -u kim:wrong localhost:8090/api/notes
HTTP/1.1 401

$ curl -i -u kim:user-pass -X DELETE localhost:8090/api/notes/1
HTTP/1.1 403

$ curl -i -u lee:admin-pass -X DELETE localhost:8090/api/notes/1
HTTP/1.1 204
```

- 인증 정보 없이, 또는 비밀번호가 틀리면 401이다. 응답의 `WWW-Authenticate` 헤더가 "Basic 방식으로 인증하라"고 알려 준다.
- `kim`은 로그인에는 성공했지만 관리자가 아니라 삭제에서 403을 받았다.
- 컨트롤러의 `Principal`로 로그인한 사용자 이름(`kim`)을 받았다.

HTTP Basic은 요청마다 아이디와 비밀번호를 Base64로(암호화가 아니다) 보내므로 반드시 HTTPS에서만 쓴다. 실제 서비스에서는 로그인 한 번으로 토큰을 받아 쓰는 방식(OAuth 2.0, JWT)이나 세션 쿠키 방식을 주로 쓴다.

## 메서드 보안: @PreAuthorize

주소 규칙 대신 메서드에 직접 권한을 걸 수도 있다. 설정 클래스에 `@EnableMethodSecurity`를 붙이면 동작한다.

```java
@DeleteMapping("/api/notes/{id}")
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<Void> delete(@PathVariable Long id) {
    return ResponseEntity.noContent().build();
}
```

`@PreAuthorize`도 [5편]({{ '/spring/transaction/' | relative_url }})의 `@Transactional`과 같은 **프록시** 방식으로 동작한다. 그래서 같은 클래스 안에서 직접 부르면 검사가 무시되는 함정도 똑같다. 서비스 계층에 걸면 컨트롤러 외의 입구(배치, 메시지 처리)에서 호출해도 같은 규칙이 적용된다.

`roles("ADMIN")`으로 만든 사용자는 내부적으로 `ROLE_ADMIN` 권한을 가지며, `hasRole('ADMIN')`은 이 `ROLE_` 접두사를 붙여 비교한다.

## CSRF와 세션 정책

**CSRF(Cross-Site Request Forgery)**는 사용자가 로그인해 둔 사이트의 쿠키를 악용해, 다른 사이트에서 몰래 요청을 보내게 하는 공격이다. 브라우저는 쿠키를 자동으로 붙여 보내기 때문에 생긴다. Spring Security는 기본적으로 CSRF 토큰 검사를 켜서 이를 막는다.

| 서버 종류 | CSRF 방어 |
| --- | --- |
| 브라우저가 세션 쿠키로 로그인하는 웹 서비스 | **켠다** (기본값 유지) |
| 앱이나 서버가 `Authorization` 헤더로 인증하는 API 전용 서버 | 끌 수 있다 |

이 예제는 쿠키를 쓰지 않고 요청마다 `Authorization` 헤더를 보내는 API라서 껐다. 쿠키 로그인을 쓰면서 CSRF를 끄면 바로 취약해진다. "403이 나서 일단 껐다"는 식으로 끄지 않는다.

## 테스트

`spring-boot-starter-security-test`를 추가하면 `@WithMockUser`로 로그인한 사용자를 흉내 낼 수 있다.

```java
@SpringBootTest
@AutoConfigureMockMvc
class SecurityTest {

    @Autowired
    MockMvcTester mvc;

    @Test
    void 로그인_안하면_401() {
        assertThat(mvc.get().uri("/api/notes")).hasStatus(401);
    }

    @Test
    @WithMockUser(username = "kim", roles = "USER")
    void 일반_사용자는_삭제_403() {
        assertThat(mvc.delete().uri("/api/notes/1")).hasStatus(403);
    }

    @Test
    @WithMockUser(username = "lee", roles = {"USER", "ADMIN"})
    void 관리자는_삭제_204() {
        assertThat(mvc.delete().uri("/api/notes/1")).hasStatus(204);
    }
}
```

```text
[INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0
[INFO] BUILD SUCCESS
```

보안 규칙은 "허용돼야 하는 경우"보다 **"막혀야 하는 경우"**를 꼭 테스트한다. 규칙 순서를 바꾸다 관리자 전용 주소가 열려도, 허용 케이스 테스트만으로는 알아챌 수 없다.

## 정리

- 인증은 "누구냐"(실패 시 401), 인가는 "해도 되냐"(실패 시 403)다.
- Spring Security는 컨트롤러 앞의 필터 체인으로 동작하고, 규칙은 `SecurityFilterChain` 빈으로 정한다. 규칙은 좁은 것부터 쓴다.
- 비밀번호는 `{bcrypt}` 같은 접두사가 붙은 해시로 저장한다.
- `@PreAuthorize` 메서드 보안도 프록시 방식이라 같은 클래스 내부 호출에서는 동작하지 않는다.
- CSRF 방어는 쿠키 로그인을 쓰는 서비스에서는 반드시 켜 둔다.
- 막혀야 하는 경우(401, 403)를 테스트한다.

## 실습 소스

별도 예제 프로젝트다. `mvn test`로 테스트 5개를, `mvn package` 후 `java -jar target/secure-0.0.1.jar`로 실행한다.

- [pom.xml]({{ '/assets/examples/spring/secure/pom.xml' | relative_url }})
- [SecurityConfig.java]({{ '/assets/examples/spring/secure/src/main/java/com/example/secure/SecurityConfig.java' | relative_url }})
- [NoteController.java]({{ '/assets/examples/spring/secure/src/main/java/com/example/secure/NoteController.java' | relative_url }})
- [SecureApplication.java]({{ '/assets/examples/spring/secure/src/main/java/com/example/secure/SecureApplication.java' | relative_url }})
- [SecurityTest.java]({{ '/assets/examples/spring/secure/src/test/java/com/example/secure/SecurityTest.java' | relative_url }})

## 참고

- [Spring Security Reference: Servlet Architecture](https://docs.spring.io/spring-security/reference/servlet/architecture.html)
- [Spring Security Reference: Authorize HTTP Requests](https://docs.spring.io/spring-security/reference/servlet/authorization/authorize-http-requests.html)
- [Spring Security Reference: Password Storage](https://docs.spring.io/spring-security/reference/features/authentication/password-storage.html)
- [Spring Security Reference: CSRF](https://docs.spring.io/spring-security/reference/features/exploits/csrf.html)
