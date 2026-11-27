package com.example.todo.core;

public class ReminderService {
    private final MessageSender sender;

    // 필요한 객체를 직접 만들지 않고 생성자로 받는다
    public ReminderService(MessageSender sender) {
        this.sender = sender;
    }

    public String remind(String user, String task) {
        return sender.send(user, "잊지 마세요: " + task);
    }
}
