package com.example.todo.core;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;

class ContainerTest {

    @Test
    void 직접_조립하기() {
        ReminderService service = new ReminderService(new SmsSender());
        assertThat(service.remind("kim", "보고서")).isEqualTo("sms to kim: 잊지 마세요: 보고서");
    }

    @Test
    void 컨테이너가_조립하기() {
        try (var context = new AnnotationConfigApplicationContext(AppConfig.class)) {
            ReminderService service = context.getBean(ReminderService.class);
            System.out.println("[container] " + service.remind("kim", "보고서"));
            System.out.println("[container] beans = " + java.util.Arrays.stream(context.getBeanDefinitionNames())
                    .filter(n -> !n.startsWith("org.springframework")).toList());
            System.out.println("[container] same = " + (context.getBean(ReminderService.class) == service));
            assertThat(service.remind("kim", "보고서")).startsWith("email to kim");
            // 같은 빈을 두 번 꺼내도 같은 객체다 (싱글턴 스코프)
            assertThat(context.getBean(ReminderService.class)).isSameAs(service);
        }
    }
}
