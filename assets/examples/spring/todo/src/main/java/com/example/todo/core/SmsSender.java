package com.example.todo.core;

public class SmsSender implements MessageSender {
    @Override
    public String send(String to, String text) {
        return "sms to " + to + ": " + text;
    }
}
