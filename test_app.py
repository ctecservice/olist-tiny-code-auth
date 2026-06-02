import pytest
from app import app, build_auth_url


@pytest.fixture
def client():
    """Fixture que cria um cliente de teste Flask."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestIndexRoute:
    """Testes para a rota GET / (formulario de client_id)."""

    def test_index_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_index_contains_form(self, client):
        response = client.get("/")
        html = response.data.decode("utf-8")
        assert 'action="/authorize"' in html
        assert 'name="client_id"' in html


class TestAuthorizeRoute:
    """Testes para a rota POST /authorize."""

    def test_missing_client_id_returns_400(self, client):
        response = client.post("/authorize", data={})
        assert response.status_code == 400
        assert b"obrigatorio" in response.data

    def test_empty_client_id_returns_400(self, client):
        response = client.post("/authorize", data={"client_id": "   "})
        assert response.status_code == 400

    def test_valid_client_id_redirects(self, client):
        response = client.post("/authorize", data={"client_id": "meu-client-123"})
        assert response.status_code == 302
        location = response.headers["Location"]
        assert "accounts.tiny.com.br" in location
        assert "client_id=meu-client-123" in location
        assert "response_type=code" in location
        assert "scope=openid" in location
        assert "redirect_uri=" in location
        assert "state=" in location


class TestCallbackRoute:
    """Testes para a rota GET /callback."""

    def test_missing_code_returns_400(self, client):
        response = client.get("/callback")
        assert response.status_code == 400
        assert b"codigo de autorizacao" in response.data.lower()

    def test_error_param_returns_400(self, client):
        response = client.get("/callback?error=access_denied")
        assert response.status_code == 400
        assert b"access_denied" in response.data

    def test_error_with_description(self, client):
        response = client.get(
            "/callback?error=invalid_request&error_description=missing+client_id"
        )
        assert response.status_code == 400
        assert b"invalid_request" in response.data

    def test_valid_code_shows_code(self, client):
        response = client.get("/callback?code=abc123xyz")
        assert response.status_code == 200
        assert b"abc123xyz" in response.data

    def test_callback_error_has_text_plain_header(self, client):
        response = client.get("/callback?error=access_denied")
        assert response.content_type == "text/plain; charset=utf-8"


class TestBuildAuthUrl:
    """Testes para a funcao auxiliar build_auth_url."""

    def test_returns_valid_url(self):
        url = build_auth_url(
            client_id="test-client",
            redirect_uri="http://localhost/callback",
            state="random-state",
        )
        assert url.startswith("https://accounts.tiny.com.br/")
        assert "client_id=test-client" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%2Fcallback" in url
        assert "state=random-state" in url
        assert "scope=openid" in url
        assert "response_type=code" in url

    def test_all_params_are_encoded(self):
        url = build_auth_url(
            client_id="id with spaces",
            redirect_uri="http://host/path?x=1",
            state="st/+=?",
        )
        assert "client_id=id+with+spaces" in url
        assert "state=st%2F%2B%3D%3F" in url
