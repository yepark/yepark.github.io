package com.example.todo.todo;

import java.util.List;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class TodoService {

    private final TodoRepository repository;

    public TodoService(TodoRepository repository) {
        this.repository = repository;
    }

    public List<Todo> findAll(Boolean done) {
        if (done == null) {
            return repository.findAll();
        }
        return repository.findByDoneOrderByCreatedAtDesc(done);
    }

    public Todo get(Long id) {
        return repository.findById(id).orElseThrow(() -> new TodoNotFoundException(id));
    }

    @Transactional
    public Todo create(String title) {
        return repository.save(new Todo(title));
    }

    @Transactional
    public Todo complete(Long id) {
        Todo todo = get(id);
        todo.complete(); // save()를 부르지 않아도 트랜잭션이 끝날 때 UPDATE가 실행된다
        return todo;
    }

    @Transactional
    public void delete(Long id) {
        repository.delete(get(id));
    }

    @Transactional
    public List<Todo> createAll(List<String> titles) {
        List<Todo> saved = titles.stream().map(t -> repository.save(new Todo(t))).toList();
        if (titles.contains("")) {
            // 하나라도 잘못되면 앞에서 저장한 것까지 모두 취소된다
            throw new IllegalArgumentException("빈 제목이 있습니다");
        }
        return saved;
    }
}
