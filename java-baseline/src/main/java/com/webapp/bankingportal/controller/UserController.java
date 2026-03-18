package com.webapp.bankingportal.controller;

import com.webapp.bankingportal.service.EmailService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.ModelAndView;

import com.webapp.bankingportal.dto.LoginRequest;
import com.webapp.bankingportal.dto.OtpRequest;
import com.webapp.bankingportal.dto.OtpVerificationRequest;
import com.webapp.bankingportal.entity.User;
import com.webapp.bankingportal.exception.InvalidTokenException;
import com.webapp.bankingportal.service.UserService;

import jakarta.servlet.http.HttpServletRequest;

import lombok.RequiredArgsConstructor;

import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;
    private final EmailService emailService;

    @PostMapping("/register")
    public ResponseEntity<Map<String, Object>> registerUser(@Valid @RequestBody User user) {
        User registeredUser = userService.registerUser(user);

        // Manually build the map to include the success message
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("name", registeredUser.getName());
        response.put("email", registeredUser.getEmail());
        response.put("countryCode", registeredUser.getCountryCode());
        response.put("phoneNumber", registeredUser.getPhoneNumber());
        response.put("address", registeredUser.getAddress());

        if (registeredUser.getAccount() != null) {
            response.put("accountNumber", registeredUser.getAccount().getAccountNumber());
            response.put("ifscCode", registeredUser.getAccount().getIfscCode());
            response.put("branch", registeredUser.getAccount().getBranch());
            response.put("accountType", registeredUser.getAccount().getAccountType());
        }

        response.put("msg", "User registered successfully");

        return ResponseEntity.ok(response);
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, String>> login(@Valid @RequestBody LoginRequest loginRequest, HttpServletRequest request)
            throws InvalidTokenException {
        String token = userService.login(loginRequest, request);
        return ResponseEntity.ok(Map.of("token", token));
    }

    @PostMapping("/generate-otp")
    public ResponseEntity<Map<String, String>> generateOtp(@RequestBody OtpRequest otpRequest) {
        String msg = userService.generateOtp(otpRequest);
        return ResponseEntity.ok(Map.of("msg", msg));
    }

    @PostMapping("/verify-otp")
    public ResponseEntity<Map<String, String>> verifyOtpAndLogin(@RequestBody OtpVerificationRequest otpVerificationRequest)
            throws InvalidTokenException {
        String token = userService.verifyOtpAndLogin(otpVerificationRequest);
        return ResponseEntity.ok(Map.of("token", token));
    }

    @PostMapping("/update")
    public ResponseEntity<Map<String, Object>> updateUser(@RequestBody User user) {
        User updatedUser = userService.updateUser(user);
        Map<String, Object> response = new LinkedHashMap<>();
        response.put("name", updatedUser.getName());
        response.put("email", updatedUser.getEmail());
        response.put("msg", "User updated successfully");
        return ResponseEntity.ok(response);
    }

    @GetMapping("/logout")
    public ModelAndView logout(@RequestHeader("Authorization") String token)
            throws InvalidTokenException {
        return userService.logout(token);
    }
}
