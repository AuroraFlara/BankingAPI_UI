package com.webapp.bankingportal.service;

import com.webapp.bankingportal.entity.Account;
import com.webapp.bankingportal.entity.User;
import com.webapp.bankingportal.entity.Transaction; // Add this import
import java.util.List; // Add this import

public interface AccountService {
	public Account createAccount(User user);
	public Account getAccountByAccountNumber(String accountNumber);
	public boolean isPinCreated(String accountNumber);
	public void createPin(String accountNumber, String password, String pin);
	public void updatePin(String accountNumber, String oldPIN, String password, String newPIN);
	public void cashDeposit(String accountNumber, String pin, double amount);
	public void cashWithdrawal(String accountNumber, String pin, double amount);
	public void fundTransfer(String sourceAccountNumber, String targetAccountNumber, String pin, double amount);
	public double getBalance(String accountNumber);

	// NEW METHOD: Add this to retrieve transaction history
	public List<Transaction> getAllTransactionsByAccountNumber();
}