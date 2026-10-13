import csv
import tempfile
import unittest
from datetime import date
from pathlib import Path

from cgp.domain import Transaction
from cgp.services import ExportError, export_transactions


class CSVExportTests(unittest.TestCase):
    def test_exports_brazilian_csv_with_exact_money_and_escaped_text(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "financas.csv"
            transactions = [
                Transaction("expense", 'Compra; "especial"', "Alimentação", 123456, date(2026, 10, 13)),
            ]
            export_transactions(transactions, destination)
            raw = destination.read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            with destination.open(encoding="utf-8-sig", newline="") as source:
                rows = list(csv.reader(source, delimiter=";"))
            self.assertEqual(rows[0], ["Tipo", "Descrição", "Categoria", "Data", "Valor"])
            self.assertEqual(rows[1], ["Despesa", 'Compra; "especial"', "Alimentação", "13/10/2026", "R$ 1.234,56"])

    def test_reports_file_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ExportError):
                export_transactions([], Path(directory) / "missing" / "financas.csv")


if __name__ == "__main__":
    unittest.main()
