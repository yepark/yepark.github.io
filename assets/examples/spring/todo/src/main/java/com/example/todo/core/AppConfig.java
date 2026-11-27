package com.example.todo.core;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class AppConfig {
    @Bean
    public MessageSender messageSender() {
        return new EmailSender();
    }

    @Bean
    public ReminderService reminderService(MessageSender messageSender) {
        return new ReminderService(messageSender);
    }
}
