PYTHON ?= python3
VENV ?= .venv
PYTHON_BIN := $(VENV)/bin/python

.PHONY: help setup run test package-deb

help:
	@printf '%s\n' 'make setup       Criar o ambiente virtual local' 'make run         Iniciar o aplicativo CGP' 'make test        Executar a suíte de testes' 'make package-deb Construir um pacote Debian em dist/'

setup:
	@if [ ! -x "$(PYTHON_BIN)" ]; then $(PYTHON) -m venv "$(VENV)"; fi

run: setup
	@PYTHONPATH=src "$(PYTHON_BIN)" -m cgp

test: setup
	@PYTHONPATH=src "$(PYTHON_BIN)" -m unittest discover -s tests -v

package-deb:
	@$(PYTHON) packaging/build_deb.py --output-dir dist
