import enum


class TransactionType(str, enum.Enum):
    CASH_CREDIT = "CASH_CREDIT"
    CASH_DEPOSIT = "CASH_DEPOSIT"
    CASH_TRANSFER = "CASH_TRANSFER"
    CASH_WITHDRAWAL = "CASH_WITHDRAWAL"
