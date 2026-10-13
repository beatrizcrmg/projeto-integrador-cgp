from datetime import date, datetime

from cgp.domain import Transaction, parse_amount, summarize


class FinanceService:
    def __init__(self, repository):
        self.repository = repository

    def categories(self, kind=None):
        return self.repository.categories(kind)

    def add(self, kind, description, category, amount, occurred_on):
        transaction = Transaction(kind, description, category, parse_amount(amount), self._parse_date(occurred_on))
        transaction_id = self.repository.add_transaction(transaction)
        return Transaction(transaction.kind, transaction.description, transaction.category, transaction.amount_cents, transaction.occurred_on, transaction_id)

    def update(self, transaction_id, kind, description, category, amount, occurred_on):
        transaction = Transaction(kind, description, category, parse_amount(amount), self._parse_date(occurred_on), transaction_id)
        self.repository.update_transaction(transaction_id, transaction)
        return transaction

    def delete(self, transaction_id):
        self.repository.delete_transaction(transaction_id)

    def transactions(self, keyword="", kind=None, category=None, start_date=None, end_date=None):
        return self.repository.list_transactions(keyword, kind, category, self._optional_date(start_date), self._optional_date(end_date))

    def summary(self, transactions):
        return summarize(transactions)

    @staticmethod
    def _parse_date(value):
        if isinstance(value, date):
            return value
        value = value.strip()
        for date_format in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                pass
        raise ValueError("Informe uma data válida no formato DD/MM/AAAA.")

    @classmethod
    def _optional_date(cls, value):
        if value is None or not str(value).strip():
            return None
        return cls._parse_date(value)
