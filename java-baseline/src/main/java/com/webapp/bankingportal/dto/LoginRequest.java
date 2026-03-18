package com.webapp.bankingportal.dto;

import jakarta.validation.constraints.NotBlank;

public record LoginRequest(
        @NotBlank(message = "Identifier must not be empty")
        String identifier,

        @NotBlank(message = "Password must not be empty")
        String password
) {
}