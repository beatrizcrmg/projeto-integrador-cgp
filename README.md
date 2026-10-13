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
make help
make setup
make run
```

O aplicativo usa apenas bibliotecas incluídas no Python e salva o banco em `~/.local/share/cgp/cgp.sqlite3`, respeitando `XDG_DATA_HOME` quando definido.

## Capturas de tela

As imagens mostram somente as janelas do aplicativo, sem a janela de terminal.

![Painel principal do CGP](docs/images/cgp-dashboard.png)

![Gerenciamento de categorias do CGP](docs/images/cgp-categories.png)

## Testes

Execute a suíte de testes com:

```sh
make test
```
