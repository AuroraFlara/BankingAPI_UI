package com.webapp.bankingportal.controller;

import jakarta.validation.Valid;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import org.springframework.cache.annotation.Cacheable;
import com.webapp.bankingportal.dto.AmountRequest;
import com.webapp.bankingportal.dto.FundTransferRequest;
import com.webapp.bankingportal.dto.PinRequest;
import com.webapp.bankingportal.dto.PinUpdateRequest;
import com.webapp.bankingportal.service.AccountService;
import com.webapp.bankingportal.service.TransactionService;
import com.webapp.bankingportal.util.ApiMessages;
import com.webapp.bankingportal.util.JsonUtil;
import com.webapp.bankingportal.util.LoggedinUser;

import lombok.RequiredArgsConstructor;
import lombok.val;

import java.util.LinkedHashMap;
import java.util.Map;
import com.webapp.bankingportal.entity.Transaction;
import java.util.List;

@RestController
@RequestMapping("/api/account")
@RequiredArgsConstructor
public class AccountController {

    private final AccountService accountService;
    private final TransactionService transactionService;

    @GetMapping("/pin/check")
    public ResponseEntity<Map<String, Object>> checkPin() {
        String accountNumber = LoggedinUser.getAccountNumber();
        boolean isCreated = accountService.isPinCreated(accountNumber);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("isPinCreated", isCreated);
        response.put("msg", isCreated ? "PIN has been created for this account" : "PIN has not been created for this account");

        return ResponseEntity.ok(response);
    }

    @GetMapping("/transactions")
    public ResponseEntity<Map<String, Object>> getTransactions() {
        // Service handles the logic and security check
        List<Transaction> transactions = accountService.getAllTransactionsByAccountNumber();

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("transactions", transactions);
        response.put("msg", transactions.isEmpty() ? "No transactions found" : "Transactions retrieved successfully");

        return ResponseEntity.ok(response);
    }

    @PostMapping("/pin/create")
    @Cacheable(value = "idempotency", key = "T(com.webapp.bankingportal.util.LoggedinUser).getAccountNumber() + ':' + '/api/account/pin/create' + ':' + (#pinRequest).hashCode()")
    public ResponseEntity<Map<String, Object>> createPIN(@Valid @RequestBody PinRequest pinRequest) {
        accountService.createPin(
                LoggedinUser.getAccountNumber(),
                pinRequest.password(),
                pinRequest.pin());

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("hasPIN", true);
        response.put("msg", ApiMessages.PIN_CREATION_SUCCESS.getMessage());

        return ResponseEntity.ok(response);
    }

    @PostMapping("/pin/update")
    @CacheEvict(value = "idempotency", allEntries = true)
    public ResponseEntity<Map<String, Object>> updatePIN(@Valid @RequestBody PinUpdateRequest pinUpdateRequest) {
        accountService.updatePin(
                LoggedinUser.getAccountNumber(),
                pinUpdateRequest.oldPin(),
                pinUpdateRequest.password(),
                pinUpdateRequest.newPin());

        // Use the dynamic check we discussed to verify the state
        boolean hasPin = accountService.isPinCreated(LoggedinUser.getAccountNumber());

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("hasPIN", hasPin);
        response.put("msg", ApiMessages.PIN_UPDATE_SUCCESS.getMessage());

        return ResponseEntity.ok(response);
    }

    @PostMapping("/deposit")
    public ResponseEntity<Map<String, Object>> cashDeposit(@Valid @RequestBody AmountRequest amountRequest) {
        // 1. Execute the deposit
        accountService.cashDeposit(
                LoggedinUser.getAccountNumber(),
                amountRequest.pin(),
                amountRequest.amount());

        // 2. Fetch the new balance using the method we just added
        double newBalance = accountService.getBalance(LoggedinUser.getAccountNumber());
        boolean hasPin = accountService.isPinCreated(LoggedinUser.getAccountNumber());

        // 3. Return the structured response
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("hasPIN", hasPin);
        response.put("currentBalance", newBalance);
        response.put("msg", ApiMessages.CASH_DEPOSIT_SUCCESS.getMessage());

        return ResponseEntity.ok(response);
    }

    @PostMapping("/withdraw")
    @CacheEvict(value = "idempotency", allEntries = true)
    public ResponseEntity<Map<String, Object>> cashWithdrawal(@Valid @RequestBody AmountRequest amountRequest) {
        // 1. Execute withdrawal logic
        accountService.cashWithdrawal(
                LoggedinUser.getAccountNumber(),
                amountRequest.pin(),
                amountRequest.amount());

        // 2. Fetch fresh state dynamically
        double newBalance = accountService.getBalance(LoggedinUser.getAccountNumber());
        boolean hasPin = accountService.isPinCreated(LoggedinUser.getAccountNumber());

        // 3. Build the standardized response map
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("hasPIN", hasPin);
        response.put("currentBalance", newBalance);
        response.put("msg", ApiMessages.CASH_WITHDRAWAL_SUCCESS.getMessage());

        return ResponseEntity.ok(response);
    }

    @PostMapping("/fund-transfer")
    @CacheEvict(value = "idempotency", allEntries = true)
    public ResponseEntity<Map<String, Object>> fundTransfer(@Valid @RequestBody FundTransferRequest fundTransferRequest) {
        // 1. Execute the transfer logic
        accountService.fundTransfer(
                LoggedinUser.getAccountNumber(),
                fundTransferRequest.targetAccountNumber(),
                fundTransferRequest.pin(),
                fundTransferRequest.amount());

        // 2. Fetch fresh state for the sender
        double newBalance = accountService.getBalance(LoggedinUser.getAccountNumber());
        boolean hasPin = accountService.isPinCreated(LoggedinUser.getAccountNumber());

        // 3. Build the standardized response map
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("hasPIN", hasPin);
        response.put("currentBalance", newBalance);
        response.put("msg", ApiMessages.CASH_TRANSFER_SUCCESS.getMessage());

        return ResponseEntity.ok(response);
    }

}
