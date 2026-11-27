package com.example.todo.todo;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;

import java.time.Instant;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.assertj.MockMvcTester;

@WebMvcTest(TodoController.class)
class TodoControllerTest {

    @Autowired
    MockMvcTester mvc;

    @MockitoBean
    TodoService service;

    @Test
    void 할_일_하나_조회() {
        Todo todo = new Todo("장보기");
        given(service.get(1L)).willReturn(todo);

        assertThat(mvc.get().uri("/api/todos/1"))
                .hasStatusOk()
                .bodyJson().extractingPath("$.title").isEqualTo("장보기");
    }

    @Test
    void 빈_제목이면_400() throws Exception {
        var result = mvc.post().uri("/api/todos")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"title\": \"\"}");
        assertThat(result).hasStatus(400)
                .bodyJson().extractingPath("$.errors.title").isEqualTo("제목은 비어 있을 수 없습니다");
        System.out.println("[400 body] " + result.exchange().getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8));
    }

    @Test
    void 없는_id면_404_ProblemDetail() throws Exception {
        given(service.get(99L)).willThrow(new TodoNotFoundException(99L));

        var result = mvc.get().uri("/api/todos/99");
        assertThat(result).hasStatus(404)
                .bodyJson().extractingPath("$.detail").isEqualTo("할 일을 찾을 수 없습니다: 99");
        System.out.println("[404 body] " + result.exchange().getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8));
    }
}
