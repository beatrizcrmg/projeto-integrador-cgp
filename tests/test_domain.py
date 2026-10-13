import unittest
from datetime import date

from cgp.domain import MoneyError, Transaction, TransactionType, ValidationError, format_brl, parse_amount, summarize


class MoneyTests(unittest.TestCase):
    def test_parses_brazilian_and_international_decimal_values(self):
        self.assertEqual(parse_amount("R$ 1.234,56"), 123456)
        self.assertEqual(parse_amount("1234.56"), 123456)
        self.assertEqual(parse_amount("10,5"), 1050)
        self.assertEqual(parse_amount("1.234"), 123400)

    def test_formats_exact_cents(self):
        self.assertEqual(format_brl(123456789), "R$ 1.234.567,89")
        self.assertEqual(format_brl(-5), "-R$ 0,05")

    def test_rejects_invalid_amounts(self):
        for value in ("", "0", "-1,00", "1,234", "abc", 0, -1, 1.2, True):
            with self.subTest(value=value), self.assertRaises(MoneyError):
                parse_amount(value)


class TransactionTests(unittest.TestCase):
    def test_normalizes_valid_transaction(self):
        transaction = Transaction("income", " Salário ", " Trabalho ", 100, "2026-10-13")
        self.assertEqual(transaction.kind, TransactionType.INCOME)
        self.assertEqual(transaction.description, "Salário")
        self.assertEqual(transaction.category, "Trabalho")
        self.assertEqual(transaction.occurred_on, date(2026, 10, 13))

    def test_rejects_invalid_transaction_fields(self):
        values = [
            {"kind": "other", "description": "a", "category": "b", "amount_cents": 1, "occurred_on": date.today()},
            {"kind": "income", "description": " ", "category": "b", "amount_cents": 1, "occurred_on": date.today()},
            {"kind": "income", "description": "a", "category": " ", "amount_cents": 1, "occurred_on": date.today()},
            {"kind": "income", "description": "a", "category": "b", "amount_cents": 0, "occurred_on": date.today()},
            {"kind": "income", "description": "a", "category": "b", "amount_cents": 100.0, "occurred_on": date.today()},
            {"kind": "income", "description": "a", "category": "b", "amount_cents": 1, "occurred_on": "2026-99-99"},
        ]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                Transaction(**value)

    def test_summarizes_without_float(self):
        items = [
            Transaction("income", "A", "B", 10001, date.today()),
            Transaction("income", "C", "B", 99, date.today()),
            Transaction("expense", "D", "B", 2500, date.today()),
        ]
        result = summarize(items)
        self.assertEqual((result.income_cents, result.expense_cents, result.balance_cents), (10100, 2500, 7600))


if __name__ == "__main__":
    unittest.main()
