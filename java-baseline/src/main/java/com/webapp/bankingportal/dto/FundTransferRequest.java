package com.webapp.bankingportal.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record FundTransferRequest(
        @NotBlank(message = "Target account number cannot be empty")
        String targetAccountNumber,

        @NotNull(message = "Amount cannot be empty")
        @Positive(message = "Amount must be greater than 0")
        Double amount,

        @NotBlank(message = "PIN cannot be empty")
        String pin
) {}