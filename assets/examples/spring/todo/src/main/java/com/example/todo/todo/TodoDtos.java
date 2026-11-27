package com.example.todo.todo;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import java.time.Instant;

public final class TodoDtos {

    private TodoDtos() {}

    public record CreateRequest(
            @NotBlank(message = "제목은 비어 있을 수 없습니다")
            @Size(max = 100, message = "제목은 100자 이하여야 합니다")
            String title) {}

    public record Response(Long id, String title, boolean done, Instant createdAt) {
        static Response from(Todo todo) {
            return new Response(todo.getId(), todo.getTitle(), todo.isDone(), todo.getCreatedAt());
        }
    }
}
