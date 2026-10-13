import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from cgp.domain import Transaction, TransactionType


class StorageError(RuntimeError):
    pass


class NotFoundError(StorageError):
    pass


class CategoryInUseError(StorageError):
    pass


@dataclass(frozen=True, slots=True)
class Category:
    id: int
    name: str
    kind: TransactionType


class SQLiteRepository:
    schema_version = 1

    def __init__(self, database_path=None):
        if database_path is None:
            data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
            database_path = data_home / "cgp" / "cgp.sqlite3"
        self.database_path = Path(database_path).expanduser()
        if str(self.database_path) != ":memory:":
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(str(self.database_path), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self):
        try:
            with self._connect() as connection:
                current = connection.execute("PRAGMA user_version").fetchone()[0]
                if current > self.schema_version:
                    raise StorageError("O banco foi criado por uma versão mais recente do CGP.")
                if current < 1:
                    connection.executescript(
                        "CREATE TABLE categories ("
                        "id INTEGER PRIMARY KEY, "
                        "name TEXT NOT NULL COLLATE NOCASE, "
                        "kind TEXT NOT NULL CHECK (kind IN ('income', 'expense')), "
                        "UNIQUE (name, kind));"
                        "CREATE TABLE transactions ("
                        "id INTEGER PRIMARY KEY, "
                        "kind TEXT NOT NULL CHECK (kind IN ('income', 'expense')), "
                        "description TEXT NOT NULL CHECK (length(trim(description)) > 0), "
                        "category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT, "
                        "amount_cents INTEGER NOT NULL CHECK (amount_cents > 0), "
                        "occurred_on TEXT NOT NULL);"
                        "CREATE INDEX transactions_date_idx ON transactions(occurred_on, id);"
                    )
                    connection.executemany(
                        "INSERT INTO categories(name, kind) VALUES (?, ?)",
                        [(name, kind.value) for kind, names in self._default_categories().items() for name in names],
                    )
                    connection.execute(f"PRAGMA user_version = {self.schema_version}")
        except sqlite3.Error as error:
            raise StorageError(f"Não foi possível preparar o banco de dados: {error}") from error

    @staticmethod
    def _default_categories():
        return {
            TransactionType.INCOME: ("Salário", "Investimentos", "Freelance", "Outros"),
            TransactionType.EXPENSE: ("Alimentação", "Transporte", "Moradia", "Saúde", "Lazer", "Educação", "Outros"),
        }

    def categories(self, kind=None):
        try:
            with self._connect() as connection:
                if kind is None:
                    rows = connection.execute("SELECT id, name, kind FROM categories ORDER BY kind, name COLLATE NOCASE").fetchall()
                else:
                    kind = TransactionType(kind)
                    rows = connection.execute("SELECT id, name, kind FROM categories WHERE kind = ? ORDER BY name COLLATE NOCASE", (kind.value,)).fetchall()
            return [Category(row["id"], row["name"], TransactionType(row["kind"])) for row in rows]
        except (sqlite3.Error, ValueError) as error:
            raise StorageError(f"Não foi possível listar as categorias: {error}") from error

    def create_category(self, name, kind):
        name = self._category_name(name)
        kind = TransactionType(kind)
        try:
            with self._connect() as connection:
                cursor = connection.execute("INSERT INTO categories(name, kind) VALUES (?, ?)", (name, kind.value))
                row = connection.execute("SELECT id, name, kind FROM categories WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return Category(row["id"], row["name"], TransactionType(row["kind"]))
        except (sqlite3.IntegrityError, ValueError) as error:
            raise StorageError(f"Não foi possível criar a categoria: {error}") from error
        except sqlite3.Error as error:
            raise StorageError(f"Não foi possível criar a categoria: {error}") from error

    def rename_category(self, category_id, name):
        name = self._category_name(name)
        try:
            with self._connect() as connection:
                cursor = connection.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))
                if cursor.rowcount == 0:
                    raise NotFoundError("A categoria não existe mais.")
                row = connection.execute("SELECT id, name, kind FROM categories WHERE id = ?", (category_id,)).fetchone()
            return Category(row["id"], row["name"], TransactionType(row["kind"]))
        except NotFoundError:
            raise
        except (sqlite3.Error, ValueError) as error:
            raise StorageError(f"Não foi possível renomear a categoria: {error}") from error

    def delete_category(self, category_id):
        try:
            with self._connect() as connection:
                used = connection.execute("SELECT 1 FROM transactions WHERE category_id = ? LIMIT 1", (category_id,)).fetchone()
                if used:
                    raise CategoryInUseError("A categoria possui movimentações e não pode ser excluída.")
                cursor = connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))
                if cursor.rowcount == 0:
                    raise NotFoundError("A categoria não existe mais.")
        except (CategoryInUseError, NotFoundError):
            raise
        except sqlite3.Error as error:
            raise StorageError(f"Não foi possível excluir a categoria: {error}") from error

    def add_transaction(self, transaction):
        if not isinstance(transaction, Transaction):
            raise TypeError("A movimentação deve ser uma instância de Transaction.")
        try:
            with self._connect() as connection:
                category = self._find_category(connection, transaction.category, transaction.kind)
                cursor = connection.execute(
                    "INSERT INTO transactions(kind, description, category_id, amount_cents, occurred_on) VALUES (?, ?, ?, ?, ?)",
                    (transaction.kind.value, transaction.description, category["id"], transaction.amount_cents, transaction.occurred_on.isoformat()),
                )
                return cursor.lastrowid
        except StorageError:
            raise
        except sqlite3.Error as error:
            raise StorageError(f"Não foi possível salvar a movimentação: {error}") from error

    def update_transaction(self, transaction_id, transaction):
        if not isinstance(transaction, Transaction):
            raise TypeError("A movimentação deve ser uma instância de Transaction.")
        try:
            with self._connect() as connection:
                category = self._find_category(connection, transaction.category, transaction.kind)
                cursor = connection.execute(
                    "UPDATE transactions SET kind = ?, description = ?, category_id = ?, amount_cents = ?, occurred_on = ? WHERE id = ?",
                    (transaction.kind.value, transaction.description, category["id"], transaction.amount_cents, transaction.occurred_on.isoformat(), transaction_id),
                )
                if cursor.rowcount == 0:
                    raise NotFoundError("A movimentação não existe mais.")
        except (StorageError, NotFoundError):
            raise
        except sqlite3.Error as error:
            raise StorageError(f"Não foi possível atualizar a movimentação: {error}") from error

    def delete_transaction(self, transaction_id):
        try:
            with self._connect() as connection:
                cursor = connection.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
                if cursor.rowcount == 0:
                    raise NotFoundError("A movimentação não existe mais.")
        except NotFoundError:
            raise
        except sqlite3.Error as error:
            raise StorageError(f"Não foi possível excluir a movimentação: {error}") from error

    def list_transactions(self, keyword="", kind=None, category=None, start_date=None, end_date=None):
        clauses = []
        values = []
        if keyword.strip():
            escaped = keyword.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            clauses.append("t.description LIKE ? ESCAPE '\\'")
            values.append(f"%{escaped}%")
        if kind:
            clauses.append("t.kind = ?")
            values.append(TransactionType(kind).value)
        if category:
            clauses.append("c.name = ? COLLATE NOCASE")
            values.append(category)
        if start_date:
            clauses.append("t.occurred_on >= ?")
            values.append(start_date.isoformat() if hasattr(start_date, "isoformat") else str(start_date))
        if end_date:
            clauses.append("t.occurred_on <= ?")
            values.append(end_date.isoformat() if hasattr(end_date, "isoformat") else str(end_date))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT t.id, t.kind, t.description, c.name AS category, t.amount_cents, t.occurred_on "
                    "FROM transactions t JOIN categories c ON c.id = t.category_id "
                    f"{where} ORDER BY t.occurred_on DESC, t.id DESC",
                    values,
                ).fetchall()
            return [
                Transaction(row["kind"], row["description"], row["category"], row["amount_cents"], row["occurred_on"], row["id"])
                for row in rows
            ]
        except (sqlite3.Error, ValueError) as error:
            raise StorageError(f"Não foi possível consultar as movimentações: {error}") from error

    @staticmethod
    def _find_category(connection, name, kind):
        row = connection.execute("SELECT id FROM categories WHERE name = ? COLLATE NOCASE AND kind = ?", (name, kind.value)).fetchone()
        if row is None:
            raise StorageError("A categoria não existe para o tipo de movimentação selecionado.")
        return row

    @staticmethod
    def _category_name(name):
        if not isinstance(name, str) or not name.strip():
            raise StorageError("Informe o nome da categoria.")
        return name.strip()
