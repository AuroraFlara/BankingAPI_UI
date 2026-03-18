package com.webapp.bankingportal.controller;

import com.webapp.bankingportal.service.AccountService;
import org.springframework.http.ResponseEntity;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.webapp.bankingportal.service.DashboardService;
import com.webapp.bankingportal.util.JsonUtil;
import com.webapp.bankingportal.util.LoggedinUser;
import com.webapp.bankingportal.entity.Account;

import java.util.Map;
import java.util.LinkedHashMap;

import lombok.RequiredArgsConstructor;
import lombok.val;

@RestController
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
public class DashboardController {

    private final DashboardService dashboardService;
    private final AccountService accountService;

    @GetMapping("/user")
    public ResponseEntity<Map<String, Object>> getUserDetails() {
        val accountNumber = LoggedinUser.getAccountNumber();
        val userResponse = dashboardService.getUserDetails(accountNumber);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("user", userResponse);
        response.put("msg", "User details retrieved successfully");

        return ResponseEntity.ok(response);
    }

    @GetMapping("/account")
    public ResponseEntity<Map<String, Object>> getAccountDetails() {
        // Ensure this utility is returning the correct ID for the logged-in session
        String accountNumber = LoggedinUser.getAccountNumber();
        Account account = accountService.getAccountByAccountNumber(accountNumber);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("account", account);
        response.put("msg", "Account details retrieved successfully");

        return ResponseEntity.ok(response);
    }
}
