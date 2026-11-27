package com.example.todo.todo;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import java.time.Instant;

@Entity
public class Todo {

    @Id
    @GeneratedValue
    private Long id;

    @Column(nullable = false, length = 100)
    private String title;

    private boolean done;

    private Instant createdAt;

    protected Todo() {
        // JPA가 객체를 만들 때 쓰는 기본 생성자
    }

    public Todo(String title) {
        this.title = title;
        this.createdAt = Instant.now();
    }

    public void complete() {
        this.done = true;
    }

    public Long getId() { return id; }
    public String getTitle() { return title; }
    public boolean isDone() { return done; }
    public Instant getCreatedAt() { return createdAt; }
}
