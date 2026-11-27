package com.example.todo.todo;

import com.example.todo.todo.TodoDtos.CreateRequest;
import com.example.todo.todo.TodoDtos.Response;
import jakarta.validation.Valid;
import java.net.URI;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/todos")
public class TodoController {

    private final TodoService service;

    public TodoController(TodoService service) {
        this.service = service;
    }

    @GetMapping
    public List<Response> list(@RequestParam(required = false) Boolean done) {
        return service.findAll(done).stream().map(Response::from).toList();
    }

    @GetMapping("/{id}")
    public Response get(@PathVariable Long id) {
        return Response.from(service.get(id));
    }

    @PostMapping
    public ResponseEntity<Response> create(@Valid @RequestBody CreateRequest request) {
        Todo todo = service.create(request.title());
        return ResponseEntity.created(URI.create("/api/todos/" + todo.getId())).body(Response.from(todo));
    }

    @PatchMapping("/{id}/complete")
    public Response complete(@PathVariable Long id) {
        return Response.from(service.complete(id));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        service.delete(id);
        return ResponseEntity.noContent().build();
    }
}
