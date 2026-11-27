package com.example.todo.core;

public class EmailSender implements MessageSender {
    @Override
    public String send(String to, String text) {
        return "email to " + to + ": " + text;
    }
}
