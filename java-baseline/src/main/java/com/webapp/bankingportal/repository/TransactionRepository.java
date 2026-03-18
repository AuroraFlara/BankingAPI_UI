package com.webapp.bankingportal.repository;

import com.webapp.bankingportal.entity.Transaction;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TransactionRepository extends JpaRepository<Transaction, Long> {

    // Use underscores to navigate: SourceAccount -> AccountNumber
    List<Transaction> findBySourceAccount_AccountNumberOrTargetAccount_AccountNumberOrderByTransactionDateDesc(
            String sourceNo,
            String targetNo
    );
}