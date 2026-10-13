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

    def test_category_manager_creates_renames_and_deletes_categories(self):
        from cgp.ui.categories import CategoryManager

        changes = []
        manager = CategoryManager(self.root, self.service, lambda: changes.append(True))
        manager.kind_var.set("Receita")
        manager._load()
        manager.name_var.set("Rendimentos")
        manager._create()
        manager.listbox.selection_set(manager.listbox.get(0, "end").index("Rendimentos"))
        manager._select()
        manager.name_var.set("Renda extra")
        manager._rename()
        manager.listbox.selection_set(manager.listbox.get(0, "end").index("Renda extra"))
        from unittest.mock import patch

        with patch("tkinter.messagebox.askyesno", return_value=True):
            manager._delete()
        self.assertEqual(len(changes), 3)
        self.assertFalse(any(category.name == "Renda extra" for category in self.service.categories("income")))
        manager.window.destroy()


if __name__ == "__main__":
    unittest.main()
