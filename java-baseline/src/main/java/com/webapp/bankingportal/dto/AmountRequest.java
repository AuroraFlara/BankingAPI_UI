package com.webapp.bankingportal.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record AmountRequest(
        @NotBlank(message = "PIN cannot be empty")
        String pin,

        @NotNull(message = "Amount cannot be empty")
        Double amount // Use Double object to allow @NotNull validation
) {}