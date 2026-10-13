# CGP — Controle de Gastos Pessoais

Aplicativo desktop para Linux que organiza receitas e despesas em um banco SQLite local.

## Funcionalidades

- Cadastro, edição e exclusão de receitas e despesas.
- Categorias separadas por tipo de movimentação.
- Busca e filtros por período, tipo e categoria.
- Resumo de receitas, despesas e saldo conforme os filtros ativos.
- Exportação das movimentações filtradas para CSV.
- Persistência local entre execuções.

## Requisitos

- Linux, incluindo Zorin OS ou Ubuntu.
- Python 3.11 ou superior, com Tkinter e suporte a ambientes virtuais.
- SQLite, incluído na biblioteca padrão do Python.

No Zorin OS ou Ubuntu, instale os componentes do sistema com:

```sh
sudo apt install python3 python3-venv python3-tk
```

## Instalação e execução local

```sh
python3 -m venv .venv
source .venv/bin/activate
PYTHONPATH=src python -m cgp
```

O aplicativo usa apenas bibliotecas incluídas no Python e salva o banco em `~/.local/share/cgp/cgp.sqlite3`, respeitando `XDG_DATA_HOME` quando definido.

## Testes

Ative o ambiente virtual e execute:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```
