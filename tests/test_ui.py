import importlib.util
import tempfile
import unittest
from pathlib import Path

from cgp.services import FinanceService
from cgp.storage import SQLiteRepository


@unittest.skipUnless(importlib.util.find_spec("tkinter"), "Tkinter não está instalado")
class UserInterfaceTests(unittest.TestCase):
    def setUp(self):
        import tkinter as tk

        self.tk = tk
        self.directory = tempfile.TemporaryDirectory()
        self.root = tk.Tk()
        self.root.withdraw()
        self.service = FinanceService(SQLiteRepository(Path(self.directory.name) / "ui.sqlite3"))

    def tearDown(self):
        self.root.destroy()
        self.directory.cleanup()

    def test_initializes_dashboard_and_refreshes_rows(self):
        from cgp.ui.app import CGPApplication

        application = CGPApplication(self.root, self.service)
        income = self.service.add("income", "Salário", "Salário", "1.250,00", "13/10/2026")
        self.service.add("expense", "Mercado", "Alimentação", "250,00", "12/10/2026")
        application.refresh()
        self.assertEqual(len(application.table.get_children()), 2)
        self.assertEqual(application.income_value.cget("text"), "R$ 1.250,00")
        self.assertEqual(self.root.title(), "CGP — Controle de Gastos Pessoais")
        application.search_var.set("Salário")
        application.type_filter_var.set("Receitas")
        application.refresh()
        self.assertEqual(application.table.get_children(), (str(income.id),))
        application.table.selection_set(str(income.id))
        application.begin_edit()
        application.amount_var.set("1.300,00")
        application.add_transaction()
        self.assertEqual(self.service.transactions(keyword="Salário")[0].amount_cents, 130000)


if __name__ == "__main__":
    unittest.main()
