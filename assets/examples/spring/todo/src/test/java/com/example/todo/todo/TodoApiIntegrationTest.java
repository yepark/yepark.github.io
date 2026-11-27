package com.example.todo.todo;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.assertj.MockMvcTester;

@SpringBootTest
@AutoConfigureMockMvc
class TodoApiIntegrationTest {

    @Autowired
    MockMvcTester mvc;

    @Autowired
    TodoService service;

    @Autowired
    TodoRepository repository;

    @Test
    void 만들고_완료하고_목록에서_확인() {
        var created = mvc.post().uri("/api/todos")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"title\": \"블로그 쓰기\"}").exchange();
        assertThat(created).hasStatus(201);
        String location = created.getResponse().getHeader("Location");
        System.out.println("[201 Location] " + location);

        assertThat(mvc.patch().uri(location + "/complete")).hasStatusOk()
                .bodyJson().extractingPath("$.done").isEqualTo(true);

        assertThat(mvc.get().uri("/api/todos?done=true")).hasStatusOk()
                .bodyJson().extractingPath("$[*].title").asArray().contains("블로그 쓰기");
    }

    @Test
    void 트랜잭션_안에서_예외가_나면_모두_취소() {
        long before = repository.count();
        assertThatThrownBy(() -> service.createAll(List.of("하나", "둘", "")))
                .isInstanceOf(IllegalArgumentException.class);
        System.out.println("[rollback] before=" + before + " after=" + repository.count());
        assertThat(repository.count()).isEqualTo(before);
    }
}
