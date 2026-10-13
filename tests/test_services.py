import tempfile
import unittest
from pathlib import Path

from cgp.services import FinanceService
from cgp.storage import SQLiteRepository


class FinanceServiceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.service = FinanceService(SQLiteRepository(Path(self.directory.name) / "finance.sqlite3"))

    def tearDown(self):
        self.directory.cleanup()

    def test_creates_updates_filters_and_summarizes(self):
        income = self.service.add("income", "Salário", "Salário", "2.000,00", "13/10/2026")
        expense = self.service.add("expense", "Mercado", "Alimentação", "250,50", "2026-10-12")
        filtered = self.service.transactions(kind="expense", start_date="01/10/2026", end_date="31/10/2026")
        self.assertEqual([item.id for item in filtered], [expense.id])
        searched = self.service.transactions(keyword="Mercado", kind="expense", category="Alimentação", start_date="12/10/2026", end_date="12/10/2026")
        self.assertEqual([item.id for item in searched], [expense.id])
        summary = self.service.summary(self.service.transactions())
        self.assertEqual((summary.income_cents, summary.expense_cents, summary.balance_cents), (200000, 25050, 174950))
        changed = self.service.update(income.id, "income", "Pagamento", "Salário", "2.100,00", "13/10/2026")
        self.assertEqual(changed.amount_cents, 210000)
        self.service.delete(expense.id)
        self.assertEqual(len(self.service.transactions()), 1)

    def test_rejects_invalid_values_and_dates(self):
        for values in (("income", "Trabalho", "Salário", "0,00", "13/10/2026"), ("expense", "Conta", "Moradia", "10,00", "31/02/2026")):
            with self.subTest(values=values), self.assertRaises(ValueError):
                self.service.add(*values)

    def test_rejects_reversed_date_range(self):
        with self.assertRaises(ValueError):
            self.service.transactions(start_date="02/11/2026", end_date="01/11/2026")


if __name__ == "__main__":
    unittest.main()
