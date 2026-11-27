package com.example.todo.todo;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.data.jpa.test.autoconfigure.DataJpaTest;

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
