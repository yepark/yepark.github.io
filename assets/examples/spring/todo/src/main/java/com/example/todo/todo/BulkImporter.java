package com.example.todo.todo;

import java.util.List;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

// 트랜잭션 함정을 보여 주는 예: 같은 클래스 안의 메서드를 직접 호출하면 @Transactional이 무시된다
@Component
public class BulkImporter {

    private final TodoRepository repository;

    public BulkImporter(TodoRepository repository) {
        this.repository = repository;
    }

    public void importAll(List<String> titles) {
        saveAll(titles); // this.saveAll(...) : 프록시를 거치지 않는다
    }

    @Transactional
    public void saveAll(List<String> titles) {
        for (String title : titles) {
            if (title.isBlank()) {
                throw new IllegalArgumentException("빈 제목이 있습니다");
            }
            repository.save(new Todo(title));
        }
    }
}
