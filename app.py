import logging
import os
import secrets
from urllib.parse import urlencode

from flask import Flask, request, render_template, redirect, url_for, send_from_directory

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

TINY_AUTH_URL = "https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth"


def build_auth_url(client_id: str, redirect_uri: str, state: str) -> str:
    """Monta a URL de autenticacao OpenID Connect do Tiny ERP.

    Args:
        client_id: O identificador do cliente registrado no Tiny.
        redirect_uri: A URL de callback para onde o Tiny redireciona apos autenticacao.
        state: Token anti-CSRF gerado aleatoriamente.

    Returns:
        A URL completa para iniciar o fluxo OAuth2 authorization-code.
    """
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid",
        "response_type": "code",
        "state": state,
    }
    return f"{TINY_AUTH_URL}?{urlencode(params)}"


@app.route("/llms.txt")
def llms_txt():
    """Serve o arquivo llms.txt para agentes de IA."""
    return send_from_directory(app.root_path, "llms.txt", mimetype="text/plain")


@app.route("/robots.txt")
def robots_txt():
    """Serve o arquivo robots.txt para crawlers."""
    return send_from_directory(app.root_path, "robots.txt", mimetype="text/plain")


@app.route("/")
def index():
    """Exibe o formulario para informar o client_id do Tiny ERP."""
    return render_template("index.html")


@app.route("/authorize", methods=["POST"])
def authorize():
    """Recebe o client_id e redireciona o usuario para a tela de login do Tiny.

    Returns:
        Redirecionamento HTTP 302 para a URL de autenticacao do Tiny,
        ou erro 400 se o client_id nao for informado.
    """
    client_id = request.form.get("client_id", "").strip()
    if not client_id:
        logger.warning("Tentativa de autorizacao sem client_id.")
        return "Client ID e obrigatorio.", 400

    state = secrets.token_urlsafe(16)
    redirect_uri = url_for("callback", _external=True)
    auth_url = build_auth_url(client_id, redirect_uri, state)

    logger.info("Redirecionando para autenticacao Tiny. client_id=%s", client_id)
    return redirect(auth_url)


@app.route("/callback")
def callback():
    """Recebe o codigo de autorizacao retornado pelo Tiny apos login do usuario.

    Returns:
        Pagina HTML exibindo o authorization code,
        ou erro 400 em caso de falha na autenticacao.
    """
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        error_desc = request.args.get("error_description", "")
        logger.error("Erro na autorizacao Tiny: %s — %s", error, error_desc)
        return f"Erro na autorizacao: {error}", 400, {"Content-Type": "text/plain; charset=utf-8"}

    if not code:
        logger.warning("Callback recebido sem authorization code.")
        return "Nenhum codigo de autorizacao recebido.", 400, {"Content-Type": "text/plain; charset=utf-8"}

    logger.info("Codigo de autorizacao recebido com sucesso.")
    return render_template("callback.html", code=code)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s [%(levelname)s] %(message)s")
    app.run(debug=True, host="0.0.0.0", port=5000)
