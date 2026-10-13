import csv
from pathlib import Path

from cgp.domain import TransactionType, format_brl


class ExportError(RuntimeError):
    pass


def export_transactions(transactions, destination):
    path = Path(destination).expanduser()
    try:
        with path.open("w", encoding="utf-8-sig", newline="") as output:
            writer = csv.writer(output, delimiter=";", quoting=csv.QUOTE_MINIMAL)
            writer.writerow(("Tipo", "Descrição", "Categoria", "Data", "Valor"))
            for transaction in transactions:
                kind = "Receita" if transaction.kind is TransactionType.INCOME else "Despesa"
                writer.writerow((kind, transaction.description, transaction.category, transaction.occurred_on.strftime("%d/%m/%Y"), format_brl(transaction.amount_cents)))
        return path
    except (OSError, csv.Error) as error:
        raise ExportError(f"Não foi possível exportar o arquivo CSV: {error}") from error
