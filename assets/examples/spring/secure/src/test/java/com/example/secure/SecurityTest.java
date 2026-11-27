package com.example.secure;

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.web.servlet.assertj.MockMvcTester;

@SpringBootTest
@AutoConfigureMockMvc
class SecurityTest {

    @Autowired
    MockMvcTester mvc;

    @Test
    void 공개_주소는_로그인_없이() {
        assertThat(mvc.get().uri("/api/public/hello")).hasStatusOk();
    }

    @Test
    void 로그인_안하면_401() {
        assertThat(mvc.get().uri("/api/notes")).hasStatus(401);
    }

    @Test
    @WithMockUser(username = "kim", roles = "USER")
    void 로그인하면_200() {
        assertThat(mvc.get().uri("/api/notes")).hasStatusOk()
                .bodyJson().extractingPath("$.user").isEqualTo("kim");
    }

    @Test
    @WithMockUser(username = "kim", roles = "USER")
    void 일반_사용자는_삭제_403() {
        assertThat(mvc.delete().uri("/api/notes/1")).hasStatus(403);
    }

    @Test
    @WithMockUser(username = "lee", roles = {"USER", "ADMIN"})
    void 관리자는_삭제_204() {
        assertThat(mvc.delete().uri("/api/notes/1")).hasStatus(204);
    }
}
