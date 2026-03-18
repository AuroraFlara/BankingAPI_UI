package com.webapp.bankingportal.entity;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;

import lombok.Data;

@Entity
@Data
public class Transaction {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private double amount;

    @Enumerated(EnumType.STRING)
    private TransactionType transactionType;

    // FIX 1: Format the date to be human-readable
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date transactionDate;

    @ManyToOne
    @JoinColumn(name = "source_account_id")
    @JsonIgnore // Prevents the whole Account/User object from showing up
    private Account sourceAccount;

    @ManyToOne
    @JoinColumn(name = "target_account_id")
    @JsonIgnore // Prevents the whole Account/User object from showing up
    private Account targetAccount;

    // Then use these for the clean "Short" version:
    @JsonProperty("sourceAccountNumber")
    public String getSourceNo() {
        return sourceAccount != null ? sourceAccount.getAccountNumber() : "N/A";
    }

    @JsonProperty("targetAccountNumber")
    public String getTargetAccountNumber() {
        return targetAccount != null ? targetAccount.getAccountNumber() : "N/A";
    }
}