# Sistema de Controle de Empréstimo de Equipamentos

Projeto Integrado Interdisciplinar — Curso Superior de Tecnologia em Análise e
Desenvolvimento de Sistemas — Anhanguera Educacional.

Autor: Ian Karel Ctvrtnik

## Sobre
Protótipo funcional para controle de empréstimo e devolução de equipamentos
(ferramentas, equipamentos de acesso, audiovisual etc.), com cadastro de
equipamentos, registro de empréstimos/devoluções e consulta de disponibilidade.

## Tecnologias
- Python 3 / Flask
- SQLite3
- HTML5 / CSS3 (Jinja2 templates)

## Como executar
```bash
pip install flask
python app.py
```
Acesse http://localhost:5050

## Funcionalidades implementadas (Fase 4)
- RF01 — Cadastro de equipamento (grava no banco de dados)
- RF02 — Registro de empréstimo (consulta disponibilidade e grava no banco)
- RF03 — Registro de devolução
- RF05 — Consulta de disponibilidade (dashboard)

## Estrutura
```
app.py                  # rotas e regras de negócio
templates/               # telas (Jinja2)
emprestimos.db            # banco SQLite (gerado em tempo de execução)
```
