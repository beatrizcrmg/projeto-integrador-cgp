class CategoryManager:
    def __init__(self, parent, service, on_changed):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.service = service
        self.on_changed = on_changed
        self.window = tk.Toplevel(parent)
        self.window.title("Gerenciar categorias")
        self.window.transient(parent)
        self.window.geometry("430x440")
        self.window.minsize(380, 380)
        self.kind_var = tk.StringVar(value="Despesa")
        self.name_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.category_ids = []
        self._build()
        self._load()
        self.window.grab_set()

    def _build(self):
        frame = self.ttk.Frame(self.window, padding=16)
        frame.pack(fill="both", expand=True)
        self.ttk.Label(frame, text="Tipo de categoria").pack(anchor="w")
        kind_box = self.ttk.Combobox(frame, textvariable=self.kind_var, values=("Despesa", "Receita"), state="readonly")
        kind_box.pack(fill="x", pady=(4, 10))
        kind_box.bind("<<ComboboxSelected>>", lambda event: self._load())
        self.listbox = self.tk.Listbox(frame, exportselection=False, activestyle="dotbox")
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._select)
        self.ttk.Label(frame, text="Nome da categoria").pack(anchor="w", pady=(10, 0))
        self.name_entry = self.ttk.Entry(frame, textvariable=self.name_var)
        self.name_entry.pack(fill="x", pady=(4, 8))
        buttons = self.ttk.Frame(frame)
        buttons.pack(fill="x")
        self.ttk.Button(buttons, text="Adicionar", command=self._create).pack(side="left")
        self.ttk.Button(buttons, text="Renomear", command=self._rename).pack(side="left", padx=6)
        self.ttk.Button(buttons, text="Excluir", command=self._delete).pack(side="left")
        self.ttk.Button(buttons, text="Fechar", command=self.window.destroy).pack(side="right")
        self.ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=(8, 0))

    def _kind(self):
        return "income" if self.kind_var.get() == "Receita" else "expense"

    def _load(self):
        categories = self.service.categories(self._kind())
        self.category_ids = [category.id for category in categories]
        self.listbox.delete(0, "end")
        for category in categories:
            self.listbox.insert("end", category.name)
        self.name_var.set("")

    def _selected_id(self):
        selection = self.listbox.curselection()
        return self.category_ids[selection[0]] if selection else None

    def _select(self, event=None):
        selection = self.listbox.curselection()
        if selection:
            self.name_var.set(self.listbox.get(selection[0]))

    def _create(self):
        from tkinter import messagebox

        try:
            self.service.create_category(self.name_var.get(), self._kind())
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Não foi possível criar", str(error), parent=self.window)
            return
        self.status_var.set("Categoria adicionada.")
        self._load()
        self.on_changed()
        self.name_entry.focus_set()

    def _rename(self):
        from tkinter import messagebox

        category_id = self._selected_id()
        if category_id is None:
            messagebox.showwarning("Selecione uma categoria", "Selecione uma categoria para renomear.", parent=self.window)
            return
        try:
            self.service.rename_category(category_id, self.name_var.get())
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Não foi possível renomear", str(error), parent=self.window)
            return
        self.status_var.set("Categoria renomeada.")
        self._load()
        self.on_changed()

    def _delete(self):
        from tkinter import messagebox

        category_id = self._selected_id()
        if category_id is None:
            messagebox.showwarning("Selecione uma categoria", "Selecione uma categoria para excluir.", parent=self.window)
            return
        if not messagebox.askyesno("Confirmar exclusão", "Deseja excluir a categoria selecionada?", parent=self.window):
            return
        try:
            self.service.delete_category(category_id)
        except (ValueError, RuntimeError) as error:
            messagebox.showerror("Não foi possível excluir", str(error), parent=self.window)
            return
        self.status_var.set("Categoria excluída.")
        self._load()
        self.on_changed()
