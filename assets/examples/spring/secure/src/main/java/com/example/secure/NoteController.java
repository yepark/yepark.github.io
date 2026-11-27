package com.example.secure;

import java.security.Principal;
import java.util.List;
import java.util.Map;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class NoteController {

    @GetMapping("/api/public/hello")
    public Map<String, String> hello() {
        return Map.of("message", "누구나 볼 수 있음");
    }

    @GetMapping("/api/notes")
    public Map<String, Object> notes(Principal principal) {
        return Map.of("user", principal.getName(), "notes", List.of("장보기", "운동"));
    }

    @DeleteMapping("/api/notes/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        return ResponseEntity.noContent().build();
    }
}
