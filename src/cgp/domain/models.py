from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class TransactionType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Transaction:
    kind: TransactionType
    description: str
    category: str
    amount_cents: int
    occurred_on: date
    id: int | None = None

    def __post_init__(self):
        try:
            kind = TransactionType(self.kind)
        except (ValueError, TypeError):
            raise ValidationError("Selecione receita ou despesa.") from None
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValidationError("Informe a descrição da movimentação.")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValidationError("Selecione uma categoria.")
        if isinstance(self.amount_cents, bool) or not isinstance(self.amount_cents, int) or self.amount_cents <= 0:
            raise ValidationError("O valor deve ser maior que zero e ter precisão em centavos.")
        if isinstance(self.occurred_on, str):
            try:
                occurred_on = date.fromisoformat(self.occurred_on)
            except ValueError:
                raise ValidationError("Informe uma data válida.") from None
            object.__setattr__(self, "occurred_on", occurred_on)
        if not isinstance(self.occurred_on, date):
            raise ValidationError("Informe uma data válida.")
        if self.id is not None and (isinstance(self.id, bool) or not isinstance(self.id, int) or self.id <= 0):
            raise ValidationError("Identificador de movimentação inválido.")
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "category", self.category.strip())


@dataclass(frozen=True, slots=True)
class FinancialSummary:
    income_cents: int
    expense_cents: int

    @property
    def balance_cents(self):
        return self.income_cents - self.expense_cents


def summarize(transactions):
    income = 0
    expense = 0
    for transaction in transactions:
        if transaction.kind is TransactionType.INCOME:
            income += transaction.amount_cents
        else:
            expense += transaction.amount_cents
    return FinancialSummary(income, expense)
