from datetime import date

from cgp.domain import TransactionType, format_brl
from cgp.services.finance import FinanceService
from cgp.storage import SQLiteRepository


class CGPApplication:
    def __init__(self, root, service):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = root
        self.service = service
        self.root.title("CGP — Controle de Gastos Pessoais")
        self.root.geometry("1240x820")
        self.root.minsize(920, 680)
        self.root.configure(bg="#f4f7fb")
        self.kind_var = tk.StringVar(value=TransactionType.EXPENSE.value)
        self.kind_display_var = tk.StringVar(value="Despesa")
        self.description_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        self.status_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.type_filter_var = tk.StringVar(value="Todos")
        self.category_filter_var = tk.StringVar(value="Todas")
        self.start_date_var = tk.StringVar()
        self.end_date_var = tk.StringVar()
        self.editing_id = None
        self._configure_style()
        self._build()
        self._load_categories()
        self.refresh()

    def _configure_style(self):
        style = self.ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#f4f7fb")
        style.configure("Card.TFrame", background="#ffffff", relief="solid", borderwidth=1)
        style.configure("Header.TLabel", background="#174b86", foreground="#ffffff", font=("TkDefaultFont", 22, "bold"))
        style.configure("Section.TLabel", background="#ffffff", foreground="#174b86", font=("TkDefaultFont", 13, "bold"))
        style.configure("Field.TLabel", background="#ffffff", foreground="#174b86", font=("TkDefaultFont", 10, "bold"))
        style.configure("MetricTitle.TLabel", background="#ffffff", foreground="#174b86", font=("TkDefaultFont", 11, "bold"))
        style.configure("Income.TLabel", background="#ffffff", foreground="#27835f", font=("TkDefaultFont", 20, "bold"))
        style.configure("Expense.TLabel", background="#ffffff", foreground="#d94c4c", font=("TkDefaultFont", 20, "bold"))
        style.configure("Balance.TLabel", background="#ffffff", foreground="#1264c8", font=("TkDefaultFont", 20, "bold"))
        style.configure("Primary.TButton", font=("TkDefaultFont", 10, "bold"), padding=(14, 9))
        style.map("Primary.TButton", background=[("active", "#0f58ad")])
        style.configure("Treeview", rowheight=32, font=("TkDefaultFont", 10), background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"), background="#eaf2fc", foreground="#174b86", padding=8)

    def _build(self):
        outer = self.ttk.Frame(self.root, style="App.TFrame", padding=(18, 18))
        outer.pack(fill="both", expand=True)
        header = self.ttk.Frame(outer, style="Card.TFrame", padding=(20, 17))
        header.pack(fill="x", pady=(0, 14))
        self.ttk.Label(header, text="CGP — Controle de Gastos Pessoais", style="Header.TLabel", padding=(12, 4)).pack(anchor="w", fill="x")

        form = self.ttk.Frame(outer, style="Card.TFrame", padding=(16, 14))
        form.pack(fill="x", pady=(0, 14))
        self.ttk.Label(form, text="Nova movimentação", style="Section.TLabel").grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 12))
        fields = (("Tipo", 0), ("Descrição", 1), ("Categoria", 2), ("Valor (R$)", 3), ("Data", 4))
        for label, column in fields:
            self.ttk.Label(form, text=label, style="Field.TLabel").grid(row=1, column=column, sticky="w", padx=(0, 10), pady=(0, 5))
        self.kind_box = self.ttk.Combobox(form, textvariable=self.kind_display_var, values=("Despesa", "Receita"), state="readonly", width=13)
        self.kind_box.grid(row=2, column=0, sticky="ew", padx=(0, 10))
        self.kind_box.bind("<<ComboboxSelected>>", self._on_kind_changed)
        self.description_entry = self.ttk.Entry(form, textvariable=self.description_var)
        self.description_entry.grid(row=2, column=1, sticky="ew", padx=(0, 10))
        self.category_box = self.ttk.Combobox(form, textvariable=self.category_var, state="readonly")
        self.category_box.grid(row=2, column=2, sticky="ew", padx=(0, 10))
        self.ttk.Entry(form, textvariable=self.amount_var, width=14).grid(row=2, column=3, sticky="ew", padx=(0, 10))
        self.ttk.Entry(form, textvariable=self.date_var, width=12).grid(row=2, column=4, sticky="ew", padx=(0, 10))
        self.submit_button = self.ttk.Button(form, text="Adicionar movimentação", style="Primary.TButton", command=self.add_transaction)
        self.submit_button.grid(row=2, column=5, sticky="ew")
        for column, weight in enumerate((1, 2, 1, 1, 1, 0)):
            form.columnconfigure(column, weight=weight)
        self.root.bind("<Return>", self._on_return)

        metrics = self.ttk.Frame(outer, style="App.TFrame")
        metrics.pack(fill="x", pady=(0, 14))
        self.income_value = self._metric(metrics, "Receitas", "Income.TLabel", 0)
        self.expense_value = self._metric(metrics, "Despesas", "Expense.TLabel", 1)
        self.balance_value = self._metric(metrics, "Saldo", "Balance.TLabel", 2)
        for column in range(3):
            metrics.columnconfigure(column, weight=1, uniform="metrics")

        listing = self.ttk.Frame(outer, style="Card.TFrame", padding=(14, 12))
        listing.pack(fill="both", expand=True)
        heading = self.ttk.Frame(listing, style="Card.TFrame")
        heading.pack(fill="x", pady=(0, 8))
        self.ttk.Label(heading, text="Movimentações cadastradas", style="Section.TLabel").pack(side="left")
        self.period_label = self.ttk.Label(heading, text="Todos os períodos", style="Field.TLabel")
        self.period_label.pack(side="right")
        filters = self.ttk.Frame(listing, style="Card.TFrame")
        filters.pack(fill="x", pady=(0, 8))
        filter_fields = (
            ("Buscar", self.ttk.Entry(filters, textvariable=self.search_var), 20),
            ("Tipo", self.ttk.Combobox(filters, textvariable=self.type_filter_var, values=("Todos", "Receitas", "Despesas"), state="readonly"), 12),
            ("Categoria", self.ttk.Combobox(filters, textvariable=self.category_filter_var, values=("Todas",), state="readonly"), 16),
            ("De (DD/MM/AAAA)", self.ttk.Entry(filters, textvariable=self.start_date_var), 14),
            ("Até (DD/MM/AAAA)", self.ttk.Entry(filters, textvariable=self.end_date_var), 14),
        )
        self.category_filter_box = filter_fields[2][1]
        for column, (label, widget, width) in enumerate(filter_fields):
            self.ttk.Label(filters, text=label, style="Field.TLabel").grid(row=0, column=column, sticky="w", padx=(0, 6))
            widget.configure(width=width)
            widget.grid(row=1, column=column, sticky="ew", padx=(0, 8))
        self.ttk.Button(filters, text="Aplicar", command=self.refresh).grid(row=1, column=5, sticky="ew", padx=(0, 5))
        self.ttk.Button(filters, text="Limpar", command=self.clear_filters).grid(row=1, column=6, sticky="ew")
        for column, weight in enumerate((2, 1, 1, 1, 1, 0, 0)):
            filters.columnconfigure(column, weight=weight)
        columns = ("kind", "description", "category", "date", "amount")
        self.table = self.ttk.Treeview(listing, columns=columns, show="headings", selectmode="browse")
        headings = (("kind", "Tipo", 105), ("description", "Descrição", 360), ("category", "Categoria", 220), ("date", "Data", 130), ("amount", "Valor (R$)", 150))
        for column, title, width in headings:
            self.table.heading(column, text=title)
            self.table.column(column, width=width, minwidth=80, anchor="w" if column in ("description", "category") else "center", stretch=True)
        self.table.pack(fill="both", expand=True)
        self.empty_label = self.ttk.Label(listing, text="Nenhuma movimentação cadastrada ainda.", style="Field.TLabel")
        actions = self.ttk.Frame(listing, style="Card.TFrame")
        actions.pack(fill="x", pady=(10, 0))
        self.ttk.Button(actions, text="Editar selecionada", style="Primary.TButton", command=self.begin_edit).pack(side="left", padx=(0, 8))
        self.ttk.Button(actions, text="Excluir movimentação selecionada", style="Primary.TButton", command=self.delete_transaction).pack(side="left")
        self.ttk.Button(actions, text="Gerenciar categorias", style="Primary.TButton", command=self.open_categories).pack(side="left", padx=(8, 0))
        self.ttk.Button(actions, text="Exportar CSV", style="Primary.TButton", command=self.export_csv).pack(side="left", padx=(8, 0))
        self.status_label = self.ttk.Label(actions, textvariable=self.status_var, style="Field.TLabel")
        self.status_label.pack(side="right")

    def _metric(self, parent, title, style, column):
        card = self.ttk.Frame(parent, style="Card.TFrame", padding=(17, 15))
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0 if column == 2 else 6))
        self.ttk.Label(card, text=title, style="MetricTitle.TLabel").pack(anchor="w")
        value = self.ttk.Label(card, text="R$ 0,00", style=style)
        value.pack(anchor="w", pady=(4, 0))
        return value

    def _load_categories(self):
        categories = self.service.categories(self.kind_var.get())
        self.category_box.configure(values=tuple(category.name for category in categories))
        if categories and self.category_var.get() not in self.category_box.cget("values"):
            preferred = "Alimentação" if self.kind_var.get() == TransactionType.EXPENSE.value else "Salário"
            self.category_var.set(preferred if preferred in self.category_box.cget("values") else categories[0].name)

    def _on_kind_changed(self, event=None):
        value = self.kind_display_var.get()
        self.kind_var.set(TransactionType.INCOME.value if value == "Receita" else TransactionType.EXPENSE.value)
        self._load_categories()

    def _on_return(self, event):
        if self.root.focus_get() is self.description_entry:
            self.add_transaction()
            return "break"

    def add_transaction(self):
        from tkinter import messagebox

        try:
            values = (self.kind_var.get(), self.description_var.get(), self.category_var.get(), self.amount_var.get(), self.date_var.get())
            if self.editing_id is None:
                self.service.add(*values)
                self.status_var.set("Movimentação adicionada.")
            else:
                self.service.update(self.editing_id, *values)
                self.status_var.set("Movimentação atualizada.")
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Não foi possível adicionar", str(error), parent=self.root)
            return
        self.description_var.set("")
        self.amount_var.set("")
        self.editing_id = None
        self.submit_button.configure(text="Adicionar movimentação")
        self.refresh()
        self.description_entry.focus_set()

    def begin_edit(self):
        from tkinter import messagebox

        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Selecione uma movimentação", "Selecione uma linha para editar.", parent=self.root)
            return
        transaction_id = int(selected[0])
        transaction = next((item for item in self.service.transactions() if item.id == transaction_id), None)
        if transaction is None:
            self.status_var.set("A movimentação selecionada não está mais disponível.")
            self.refresh()
            return
        self.editing_id = transaction_id
        self.kind_var.set(transaction.kind.value)
        self.kind_display_var.set("Receita" if transaction.kind is TransactionType.INCOME else "Despesa")
        self.description_var.set(transaction.description)
        self.category_var.set(transaction.category)
        self._load_categories()
        self.amount_var.set(f"{transaction.amount_cents // 100},{transaction.amount_cents % 100:02d}")
        self.date_var.set(transaction.occurred_on.strftime("%d/%m/%Y"))
        self.submit_button.configure(text="Salvar alterações")
        self.description_entry.focus_set()

    def clear_filters(self):
        self.search_var.set("")
        self.type_filter_var.set("Todos")
        self.category_filter_var.set("Todas")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.refresh()

    def open_categories(self):
        from cgp.ui.categories import CategoryManager

        CategoryManager(self.root, self.service, self._categories_changed)

    def _categories_changed(self):
        self._load_categories()
        self.refresh()

    def export_csv(self):
        from tkinter import filedialog, messagebox

        destination = filedialog.asksaveasfilename(
            parent=self.root,
            title="Exportar movimentações",
            defaultextension=".csv",
            filetypes=(("Arquivo CSV", "*.csv"),),
        )
        if not destination:
            return
        try:
            transactions = self._filtered_transactions()
            self.service.export_csv(transactions, destination)
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Falha na exportação", str(error), parent=self.root)
            return
        messagebox.showinfo("Exportação concluída", "As movimentações filtradas foram exportadas.", parent=self.root)

    def delete_transaction(self):
        from tkinter import messagebox

        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Selecione uma movimentação", "Selecione uma linha para excluir.", parent=self.root)
            return
        if not messagebox.askyesno("Confirmar exclusão", "Deseja excluir a movimentação selecionada?", parent=self.root):
            return
        try:
            self.service.delete(int(selected[0]))
        except RuntimeError as error:
            messagebox.showerror("Não foi possível excluir", str(error), parent=self.root)
            return
        self.status_var.set("Movimentação excluída.")
        self.refresh()

    def refresh(self):
        from tkinter import messagebox

        try:
            transactions = self._filtered_transactions()
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Filtros inválidos", str(error), parent=self.root)
            return
        summary = self.service.summary(transactions)
        self.income_value.configure(text=format_brl(summary.income_cents))
        self.expense_value.configure(text=format_brl(summary.expense_cents))
        self.balance_value.configure(text=format_brl(summary.balance_cents))
        start = self.start_date_var.get().strip()
        end = self.end_date_var.get().strip()
        self.period_label.configure(text=f"{start or 'Início'} a {end or 'Hoje'}" if start or end else "Todos os períodos")
        categories = self.service.categories()
        category_names = tuple(dict.fromkeys(category.name for category in categories))
        self.category_filter_box.configure(values=("Todas", *category_names))
        self.table.delete(*self.table.get_children())
        for transaction in transactions:
            label = "Receita" if transaction.kind is TransactionType.INCOME else "Despesa"
            self.table.insert("", "end", iid=str(transaction.id), values=(label, transaction.description, transaction.category, transaction.occurred_on.strftime("%d/%m/%Y"), format_brl(transaction.amount_cents)))
        if transactions:
            self.empty_label.pack_forget()
        else:
            self.empty_label.pack(fill="x", pady=9, before=self.table)

    def _filtered_transactions(self):
        type_mapping = {"Receitas": "income", "Despesas": "expense"}
        selected_category = self.category_filter_var.get()
        return self.service.transactions(
            self.search_var.get(),
            type_mapping.get(self.type_filter_var.get()),
            selected_category if selected_category and selected_category != "Todas" else None,
            self.start_date_var.get(),
            self.end_date_var.get(),
        )


def main():
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    try:
        repository = SQLiteRepository()
        CGPApplication(root, FinanceService(repository))
    except Exception as error:
        messagebox.showerror("CGP", f"Não foi possível iniciar o aplicativo: {error}", parent=root)
        root.destroy()
        return
    root.mainloop()
