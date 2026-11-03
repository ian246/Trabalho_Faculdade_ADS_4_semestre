"""
Sistema de Controle de Empréstimo de Equipamentos
Projeto Integrado Interdisciplinar - ADS - Anhanguera
Autor: Ian Karel Ctvrtnik

Funcionalidade 1: Cadastro de Equipamento (grava no banco de dados)
Funcionalidade 2: Registrar Empréstimo (lê equipamentos/usuários e grava empréstimo)
"""
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "chave-secreta-projeto-integrado"
DB_PATH = os.path.join(os.path.dirname(__file__), "emprestimos.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS usuario (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        matricula TEXT NOT NULL UNIQUE,
        email TEXT,
        perfil TEXT NOT NULL DEFAULT 'solicitante'
    );

    CREATE TABLE IF NOT EXISTS equipamento (
        id_equipamento INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        cod_patrimonio TEXT NOT NULL UNIQUE,
        categoria TEXT NOT NULL,
        qtd_total INTEGER NOT NULL,
        qtd_disponivel INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS emprestimo (
        id_emprestimo INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER NOT NULL,
        id_equipamento INTEGER NOT NULL,
        data_retirada TEXT NOT NULL,
        data_prev_devolucao TEXT NOT NULL,
        data_devolucao TEXT,
        status TEXT NOT NULL DEFAULT 'em_andamento',
        FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
        FOREIGN KEY (id_equipamento) REFERENCES equipamento(id_equipamento)
    );
    """)
    # seed data for demonstration
    if conn.execute("SELECT COUNT(*) c FROM usuario").fetchone()["c"] == 0:
        conn.executescript("""
        INSERT INTO usuario (nome, matricula, email, perfil) VALUES
            ('Ian Karel Ctvrtnik', '2026ADS001', 'ian@exemplo.com', 'administrador'),
            ('Mariana Souza', '2026ADS014', 'mariana@exemplo.com', 'solicitante');

        INSERT INTO equipamento (nome, cod_patrimonio, categoria, qtd_total, qtd_disponivel) VALUES
            ('Furadeira de Impacto', 'EQ-001', 'Ferramentas Elétricas', 3, 3),
            ('Escada 5 degraus', 'EQ-002', 'Equipamentos de Acesso', 2, 2),
            ('Projetor Multimídia', 'EQ-003', 'Audiovisual', 1, 1);
        """)
    conn.commit()
    conn.close()


@app.route("/")
def login():
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    conn = get_db()
    equipamentos = conn.execute("SELECT * FROM equipamento ORDER BY nome").fetchall()
    conn.close()
    return render_template("dashboard.html", equipamentos=equipamentos)


# ---------- Funcionalidade 1: Cadastrar Equipamento ----------
@app.route("/equipamentos/novo", methods=["GET", "POST"])
def novo_equipamento():
    if request.method == "POST":
        nome = request.form["nome"].strip()
        cod = request.form["cod_patrimonio"].strip()
        categoria = request.form["categoria"].strip()
        qtd = int(request.form["qtd_total"])

        if not nome or not cod or qtd <= 0:
            flash("Preencha todos os campos corretamente.", "erro")
            return redirect(url_for("novo_equipamento"))

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO equipamento (nome, cod_patrimonio, categoria, qtd_total, qtd_disponivel) "
                "VALUES (?, ?, ?, ?, ?)",
                (nome, cod, categoria, qtd, qtd),
            )
            conn.commit()
            flash(f'Equipamento "{nome}" cadastrado com sucesso!', "sucesso")
        except sqlite3.IntegrityError:
            flash("Já existe um equipamento com esse código de patrimônio.", "erro")
        finally:
            conn.close()
        return redirect(url_for("dashboard"))

    return render_template("novo_equipamento.html")


# ---------- Funcionalidade 2: Registrar Empréstimo ----------
@app.route("/emprestimos/novo", methods=["GET", "POST"])
def novo_emprestimo():
    conn = get_db()
    usuarios = conn.execute("SELECT * FROM usuario ORDER BY nome").fetchall()
    equipamentos = conn.execute(
        "SELECT * FROM equipamento WHERE qtd_disponivel > 0 ORDER BY nome"
    ).fetchall()

    if request.method == "POST":
        id_usuario = int(request.form["id_usuario"])
        id_equipamento = int(request.form["id_equipamento"])
        dias = int(request.form.get("dias", 7))

        equip = conn.execute(
            "SELECT * FROM equipamento WHERE id_equipamento = ?", (id_equipamento,)
        ).fetchone()

        if not equip or equip["qtd_disponivel"] <= 0:
            flash("Equipamento indisponível para empréstimo.", "erro")
            conn.close()
            return redirect(url_for("novo_emprestimo"))

        hoje = date.today()
        previsao = hoje + timedelta(days=dias)
        conn.execute(
            "INSERT INTO emprestimo (id_usuario, id_equipamento, data_retirada, "
            "data_prev_devolucao, status) VALUES (?, ?, ?, ?, 'em_andamento')",
            (id_usuario, id_equipamento, hoje.isoformat(), previsao.isoformat()),
        )
        conn.execute(
            "UPDATE equipamento SET qtd_disponivel = qtd_disponivel - 1 WHERE id_equipamento = ?",
            (id_equipamento,),
        )
        conn.commit()
        conn.close()
        flash("Empréstimo registrado com sucesso!", "sucesso")
        return redirect(url_for("listar_emprestimos"))

    conn.close()
    return render_template("novo_emprestimo.html", usuarios=usuarios, equipamentos=equipamentos)


@app.route("/emprestimos")
def listar_emprestimos():
    conn = get_db()
    rows = conn.execute("""
        SELECT e.id_emprestimo, u.nome AS usuario, eq.nome AS equipamento,
               e.data_retirada, e.data_prev_devolucao, e.data_devolucao, e.status
        FROM emprestimo e
        JOIN usuario u ON u.id_usuario = e.id_usuario
        JOIN equipamento eq ON eq.id_equipamento = e.id_equipamento
        ORDER BY e.id_emprestimo DESC
    """).fetchall()
    conn.close()
    return render_template("listar_emprestimos.html", emprestimos=rows)


@app.route("/emprestimos/<int:id_emprestimo>/devolver", methods=["POST"])
def devolver(id_emprestimo):
    conn = get_db()
    emp = conn.execute("SELECT * FROM emprestimo WHERE id_emprestimo = ?", (id_emprestimo,)).fetchone()
    if emp and emp["status"] == "em_andamento":
        conn.execute(
            "UPDATE emprestimo SET status = 'devolvido', data_devolucao = ? WHERE id_emprestimo = ?",
            (date.today().isoformat(), id_emprestimo),
        )
        conn.execute(
            "UPDATE equipamento SET qtd_disponivel = qtd_disponivel + 1 WHERE id_equipamento = ?",
            (emp["id_equipamento"],),
        )
        conn.commit()
        flash("Devolução registrada com sucesso!", "sucesso")
    conn.close()
    return redirect(url_for("listar_emprestimos"))


if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    app.run(host="0.0.0.0", port=5050, debug=False)
