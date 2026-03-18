package com.webapp.bankingportal.dto;

import com.webapp.bankingportal.entity.User;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class UserResponse {

    private String name;
    private String email;
    private String countryCode;
    private String phoneNumber; // Standardized to camelCase
    private String address;
    private String accountNumber; // Standardized to camelCase
    private String ifscCode; // Standardized to camelCase
    private String branch;
    private String accountType; // Standardized to camelCase

    public UserResponse(User user) {
        this.name = user.getName();
        this.email = user.getEmail();
        this.countryCode = user.getCountryCode();
        this.phoneNumber = user.getPhoneNumber();
        this.address = user.getAddress();
        this.accountNumber = user.getAccount().getAccountNumber();
        this.ifscCode = user.getAccount().getIfscCode();
        this.branch = user.getAccount().getBranch();
        this.accountType = user.getAccount().getAccountType();
    }
}