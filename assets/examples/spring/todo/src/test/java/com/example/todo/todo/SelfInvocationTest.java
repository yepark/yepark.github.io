package com.example.todo.todo;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.aop.support.AopUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class SelfInvocationTest {

    @Autowired
    BulkImporter importer;

    @Autowired
    TodoRepository repository;

    @BeforeEach
    void clean() {
        repository.deleteAll();
    }

    @Test
    void 프록시를_거치면_롤백된다() {
        System.out.println("[proxy] " + importer.getClass().getSimpleName() + " aop=" + AopUtils.isAopProxy(importer));
        assertThatThrownBy(() -> importer.saveAll(List.of("하나", "둘", " ")))
                .isInstanceOf(IllegalArgumentException.class);
        System.out.println("[saveAll 직접 호출] 남은 행 = " + repository.count());
        assertThat(repository.count()).isZero();
    }

    @Test
    void 내부_호출은_트랜잭션이_없어_앞의_저장이_남는다() {
        assertThatThrownBy(() -> importer.importAll(List.of("하나", "둘", " ")))
                .isInstanceOf(IllegalArgumentException.class);
        System.out.println("[importAll 내부 호출] 남은 행 = " + repository.count());
        assertThat(repository.count()).isEqualTo(2);
    }
}
