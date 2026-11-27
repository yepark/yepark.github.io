package com.example.todo.todo;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TodoRepository extends JpaRepository<Todo, Long> {

    // 메서드 이름으로 쿼리를 만든다: where done = ? order by createdAt desc
    List<Todo> findByDoneOrderByCreatedAtDesc(boolean done);

    long countByDone(boolean done);
}
