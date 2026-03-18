package com.webapp.bankingportal.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

/**
 * DTO for PIN creation and updates.
 * Removed accountNumber to prevent extra field processing.
 */
public record PinRequest(
        @NotBlank(message = "PIN cannot be empty")
        @Pattern(regexp = "[0-9]{4}", message = "PIN must be exactly 4 digits")
        String pin,

        @NotBlank(message = "Password cannot be empty")
        String password
) {
}