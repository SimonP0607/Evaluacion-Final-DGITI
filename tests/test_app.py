import psycopg2
import pytest

import app as webapp


@pytest.fixture()
def client():
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


@pytest.fixture()
def calls(monkeypatch):
    registro = []

    def falso_run(sql, params=None, fetch=False):
        registro.append((sql, params))
        return [] if fetch else None

    monkeypatch.setattr(webapp, "run", falso_run)
    return registro


def run_con_error(*args, **kwargs):
    raise psycopg2.OperationalError("sin conexion")


def test_health_no_consulta_la_base(client, calls):
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["status"] == "ok"
    assert calls == []


def test_api_test_con_base_disponible(client, calls):
    respuesta = client.get("/api/test")
    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert cuerpo["database"] == "ok"
    assert cuerpo["instance"]
    assert calls == [("SELECT 1", None)]


def test_api_test_con_base_caida_responde_503(client, monkeypatch):
    monkeypatch.setattr(webapp, "run", run_con_error)
    respuesta = client.get("/api/test")
    assert respuesta.status_code == 503
    assert respuesta.get_json()["database"] == "error"


@pytest.mark.parametrize("n, esperado", [(0, 0), (2, 0), (3, 1), (10, 4), (100, 25)])
def test_compute_cuenta_primos(client, n, esperado):
    respuesta = client.get("/compute?n=%d" % n)
    assert respuesta.status_code == 200
    assert respuesta.get_json()["primes_found"] == esperado


def test_compute_limita_el_valor_pedido(client, monkeypatch):
    monkeypatch.setattr(webapp, "count_primes", lambda tope: tope)
    cuerpo = client.get("/compute?n=999999999").get_json()
    assert cuerpo["n"] == webapp.MAX_COMPUTE_N


def test_compute_valor_invalido_usa_el_predeterminado(client, monkeypatch):
    monkeypatch.setattr(webapp, "count_primes", lambda tope: 0)
    cuerpo = client.get("/compute?n=abc").get_json()
    assert cuerpo["n"] == webapp.DEFAULT_COMPUTE_N


def test_inicio_escapa_html(client, monkeypatch):
    filas = [(1, "<script>alert(1)</script>", "a@b.co", "300")]
    monkeypatch.setattr(webapp, "run", lambda sql, params=None, fetch=False: filas)
    pagina = client.get("/").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in pagina
    assert "&lt;script&gt;" in pagina


def test_inicio_con_error_de_base_responde_500(client, monkeypatch):
    monkeypatch.setattr(webapp, "run", run_con_error)
    assert client.get("/").status_code == 500


def test_agregar_contacto_inserta_con_parametros(client, calls):
    respuesta = client.post("/add", data={"name": " Ana ", "email": "ana@x.co", "phone": "1"})
    assert respuesta.status_code == 302
    sql, params = calls[0]
    assert sql.startswith("INSERT INTO contacts")
    assert params == ("Ana", "ana@x.co", "1")


def test_agregar_sin_nombre_no_inserta(client, calls):
    client.post("/add", data={"name": "   "})
    assert calls == []


def test_eliminar_contacto(client, calls):
    respuesta = client.post("/delete/7")
    assert respuesta.status_code == 302
    assert calls == [("DELETE FROM contacts WHERE id = %s", (7,))]
