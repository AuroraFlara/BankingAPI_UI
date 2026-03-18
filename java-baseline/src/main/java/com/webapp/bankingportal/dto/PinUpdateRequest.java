package com.webapp.bankingportal.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * DTO for updating an existing PIN.
 * accountNumber is removed to prevent "Extra Field" errors and ensure security
 * by using the logged-in user's context instead.
 */
public record PinUpdateRequest(
        @NotBlank(message = "Old PIN cannot be empty")
        String oldPin,

        @NotBlank(message = "New PIN cannot be empty")
        @Pattern(regexp = "[0-9]{4}", message = "PIN must be exactly 4 digits")
        String newPin,

        @NotBlank(message = "Password cannot be empty")
        String password
) {
}