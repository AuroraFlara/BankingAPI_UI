package com.webapp.bankingportal.service;

import org.springframework.web.servlet.ModelAndView;
import com.webapp.bankingportal.dto.LoginRequest;
import com.webapp.bankingportal.dto.OtpRequest;
import com.webapp.bankingportal.dto.OtpVerificationRequest;
import com.webapp.bankingportal.entity.User;
import com.webapp.bankingportal.exception.InvalidTokenException;
import jakarta.servlet.http.HttpServletRequest;

public interface UserService {

    // 1. Updated: Returns User object for successful registration
    User registerUser(User user);

    // 2. Updated: Returns the Token string directly
    String login(LoginRequest loginRequest, HttpServletRequest request) throws InvalidTokenException;

    // 3. Updated: Returns success message or Otp identifier
    String generateOtp(OtpRequest otpRequest);

    // 4. Updated: Returns the Token string directly
    String verifyOtpAndLogin(OtpVerificationRequest otpVerificationRequest) throws InvalidTokenException;

    // 5. Updated: Returns the updated User object
    User updateUser(User user);

    public ModelAndView logout(String token) throws InvalidTokenException;

    public boolean resetPassword(User user, String newPassword);

    public User saveUser(User user);

    public User getUserByIdentifier(String identifier);

    public User getUserByAccountNumber(String accountNo);

    public User getUserByEmail(String email);
}