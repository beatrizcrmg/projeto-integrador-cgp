import tempfile
import unittest
from datetime import date
from pathlib import Path

from cgp.domain import Transaction
from cgp.storage import CategoryInUseError, SQLiteRepository, StorageError


class SQLiteRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = Path(self.directory.name) / "nested" / "test.sqlite3"
        self.repository = SQLiteRepository(self.database)

    def tearDown(self):
        self.directory.cleanup()

    def test_initializes_repeatedly_and_preserves_transactions(self):
        transaction_id = self.repository.add_transaction(Transaction("income", "Salário", "Salário", 200000, date(2026, 1, 5)))
        SQLiteRepository(self.database)
        values = SQLiteRepository(self.database).list_transactions()
        self.assertEqual([(item.id, item.amount_cents) for item in values], [(transaction_id, 200000)])

    def test_crud_and_filters(self):
        transaction_id = self.repository.add_transaction(Transaction("expense", "Mercado semanal", "Alimentação", 5500, date(2026, 5, 2)))
        self.repository.add_transaction(Transaction("expense", "Ônibus", "Transporte", 500, date(2026, 5, 3)))
        self.assertEqual(len(self.repository.list_transactions(keyword="MERCADO", kind="expense", category="Alimentação", start_date="2026-05-01", end_date="2026-05-02")), 1)
        changed = Transaction("income", "Reembolso", "Outros", 5500, date(2026, 5, 4))
        self.repository.update_transaction(transaction_id, changed)
        self.assertEqual(self.repository.list_transactions(kind="income")[0].description, "Reembolso")
        self.repository.delete_transaction(transaction_id)
        self.assertEqual(len(self.repository.list_transactions()), 1)

    def test_category_management_and_prevents_deleting_used_category(self):
        category = self.repository.create_category("Bônus", "income")
        self.repository.add_transaction(Transaction("income", "Prêmio", category.name, 100, date.today()))
        with self.assertRaises(CategoryInUseError):
            self.repository.delete_category(category.id)
        renamed = self.repository.rename_category(category.id, "Premiação")
        self.assertEqual(renamed.name, "Premiação")
        self.assertEqual(self.repository.list_transactions()[0].category, "Premiação")

    def test_rejects_category_for_wrong_transaction_type(self):
        with self.assertRaises(StorageError):
            self.repository.add_transaction(Transaction("income", "Conta", "Alimentação", 100, date.today()))

    def test_reports_invalid_database_without_replacing_it(self):
        damaged = Path(self.directory.name) / "damaged.sqlite3"
        damaged.write_text("preservar", encoding="utf-8")
        with self.assertRaises(StorageError):
            SQLiteRepository(damaged)
        self.assertEqual(damaged.read_text(encoding="utf-8"), "preservar")


if __name__ == "__main__":
    unittest.main()
