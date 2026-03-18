package com.webapp.bankingportal.entity;

import java.util.ArrayList;
import java.util.List;
import com.fasterxml.jackson.annotation.JsonIgnore;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OneToOne;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Entity
@Data
public class Account {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @NotEmpty
    @Column(unique = true)
    private String accountNumber;

    @NotEmpty
    private String accountType = "Savings";

    private String accountStatus;
    private double balance;
    private String branch = "NIT";
    private String ifscCode = "NIT001";
    @JsonIgnore
    private String Pin;

    @JsonIgnore // FIX: Prevents User profile from leaking into Account JSON
    @NotNull
    @OneToOne
    @JoinColumn(name = "user_id")
    private User user;

    @JsonIgnore // FIX: Prevents security tokens from leaking into Account JSON
    @OneToMany(mappedBy = "account", cascade = CascadeType.ALL)
    private List<Token> tokens = new ArrayList<>();

}
