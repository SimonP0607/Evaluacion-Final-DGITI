import html
import os
import socket
import time
from contextlib import closing

import psycopg2
from flask import Flask, jsonify, redirect, request

MAX_COMPUTE_N = 200000
DEFAULT_COMPUTE_N = 100000

app = Flask(__name__)


def db_settings():
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "dbname": os.environ.get("DB_NAME", "agenda"),
        "user": os.environ.get("DB_USER", "agenda_admin"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }


def connect():
    return psycopg2.connect(connect_timeout=5, **db_settings())


def run(sql, params=None, fetch=False):
    with closing(connect()) as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall() if fetch else None


def init_db(retries=30, wait=10):
    for attempt in range(1, retries + 1):
        try:
            run(
                "CREATE TABLE IF NOT EXISTS contacts ("
                "id SERIAL PRIMARY KEY, "
                "name TEXT NOT NULL, "
                "email TEXT, "
                "phone TEXT, "
                "created_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            print("Tabla contacts lista", flush=True)
            return
        except psycopg2.OperationalError as exc:
            print("Intento %d/%d: la base de datos aun no responde: %s" % (attempt, retries, exc), flush=True)
            time.sleep(wait)
    raise SystemExit("No fue posible conectar con la base de datos")


def instance_name():
    return socket.gethostname()


def is_prime(number):
    if number < 2:
        return False
    limit = int(number ** 0.5) + 1
    for divisor in range(2, limit):
        if number % divisor == 0:
            return False
    return True


def count_primes(upper_bound):
    return sum(1 for number in range(2, upper_bound) if is_prime(number))


STYLE = (
    "body{font-family:Arial,Helvetica,sans-serif;max-width:900px;margin:2rem auto;padding:0 1rem;color:#1f2933}"
    "h1{margin-bottom:.25rem}"
    ".host{background:#eef2f7;border:1px solid #cbd5e1;border-radius:6px;padding:.7rem .9rem;margin:1rem 0;font-size:.95rem}"
    ".host code{background:#fff;padding:.1rem .35rem;border-radius:4px}"
    "form.add{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}"
    "input{padding:.45rem;border:1px solid #94a3b8;border-radius:4px}"
    "button{padding:.45rem .9rem;border:0;border-radius:4px;background:#1d4ed8;color:#fff;cursor:pointer}"
    "button.del{background:#b91c1c}"
    "table{border-collapse:collapse;width:100%}"
    "th,td{border-bottom:1px solid #e2e8f0;padding:.5rem;text-align:left}"
    "th{background:#f1f5f9}"
)


def esc(value):
    return html.escape("" if value is None else str(value))


def render(rows):
    lines = []
    for contact_id, name, email, phone in rows:
        lines.append(
            "<tr><td>" + str(contact_id) + "</td><td>" + esc(name) + "</td><td>" + esc(email)
            + "</td><td>" + esc(phone) + "</td><td>"
            + '<form method="post" action="/delete/' + str(contact_id) + '">'
            + '<button class="del" type="submit">Eliminar</button></form></td></tr>'
        )
    if not lines:
        lines.append('<tr><td colspan="5">Todavía no hay contactos.</td></tr>')
    settings = db_settings()
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Agenda de contactos</title><style>" + STYLE + "</style></head><body>"
        "<h1>Agenda de contactos</h1>"
        '<div class="host">Atendido por el servidor <strong>' + esc(instance_name()) + "</strong><br>"
        "Conectada a <strong>RDS PostgreSQL</strong> (subred privada) &middot; Endpoint: <code>"
        + esc(settings["host"]) + ":" + esc(settings["port"]) + "</code> &middot; "
        "Base de datos: <code>" + esc(settings["dbname"]) + "</code></div>"
        '<form class="add" method="post" action="/add">'
        '<input name="name" placeholder="Nombre" required>'
        '<input name="email" placeholder="Correo">'
        '<input name="phone" placeholder="Teléfono">'
        '<button type="submit">Agregar contacto</button></form>'
        "<table><thead><tr><th>ID</th><th>Nombre</th><th>Correo</th><th>Teléfono</th><th></th></tr></thead>"
        "<tbody>" + "".join(lines) + "</tbody></table></body></html>"
    )


@app.route("/")
def index():
    try:
        rows = run("SELECT id, name, email, phone FROM contacts ORDER BY id", fetch=True)
    except psycopg2.Error as exc:
        return "<h1>Error de base de datos</h1><pre>" + esc(exc) + "</pre>", 500
    return render(rows)


@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    if name:
        run("INSERT INTO contacts (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
    return redirect("/")


@app.route("/delete/<int:contact_id>", methods=["POST"])
def delete(contact_id):
    run("DELETE FROM contacts WHERE id = %s", (contact_id,))
    return redirect("/")


@app.route("/health")
def health():
    return jsonify(status="ok", instance=instance_name())


@app.route("/api/test")
def api_test():
    try:
        run("SELECT 1")
        database = "ok"
        code = 200
    except psycopg2.Error:
        database = "error"
        code = 503
    return jsonify(status="ok" if code == 200 else "degraded", database=database, instance=instance_name()), code


@app.route("/compute")
def compute():
    n = request.args.get("n", default=DEFAULT_COMPUTE_N, type=int)
    n = max(0, min(n, MAX_COMPUTE_N))
    start = time.perf_counter()
    primes_found = count_primes(n)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    return jsonify(n=n, primes_found=primes_found, elapsed_ms=elapsed_ms, instance=instance_name())


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("APP_PORT", "80")))
