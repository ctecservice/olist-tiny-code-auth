# Referência da API

Todas as rotas são expostas pelo objeto `app` definido em `app.py`. Em produção (Vercel) o entrypoint é `index.py`, que apenas importa `app`.

Base URL local: `http://localhost:5000`

---

## `GET /`

Exibe o formulário HTML para que o usuário informe o `client_id`.

**Resposta**

| Código | Content-Type     | Descrição                          |
|-------:|------------------|------------------------------------|
| `200`  | `text/html`      | Página `templates/index.html`      |

**Exemplo**

```bash
curl -i http://localhost:5000/
```

---

## `POST /authorize`

Recebe o `client_id` via form-data, gera o `state` anti-CSRF e redireciona para a URL de autenticação OpenID Connect do Tiny.

**Parâmetros (form-urlencoded)**

| Campo        | Tipo   | Obrigatório | Descrição                                |
|--------------|--------|:-----------:|------------------------------------------|
| `client_id`  | string |    Sim      | Identificador do cliente no Tiny ERP     |

**Respostas**

| Código | Content-Type     | Descrição                                                            |
|-------:|------------------|----------------------------------------------------------------------|
| `302`  | —                | Redirect para `https://accounts.tiny.com.br/.../auth?...`            |
| `400`  | `text/html`      | `Client ID é obrigatório.` (campo ausente ou em branco)              |

**URL de redirect gerada**

```
https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth
  ?client_id=<client_id>
  &redirect_uri=<url_for('callback', _external=True)>
  &scope=openid
  &response_type=code
  &state=<secrets.token_urlsafe(16)>
```

**Exemplo**

```bash
curl -i -X POST http://localhost:5000/authorize \
  -d "client_id=meu-client-123"
```

Resposta:

```
HTTP/1.1 302 FOUND
Location: https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth?client_id=meu-client-123&redirect_uri=http%3A%2F%2Flocalhost%3A5000%2Fcallback&scope=openid&response_type=code&state=...
```

---

## `GET /callback`

Endpoint registrado no Tiny como `redirect_uri`. Recebe o `authorization code` ou um erro retornado pelo Tiny após o usuário autenticar.

**Query string**

| Parâmetro             | Tipo   | Descrição                                              |
|-----------------------|--------|--------------------------------------------------------|
| `code`                | string | Authorization code (caso de sucesso)                   |
| `error`               | string | Código de erro (caso de falha — ex.: `access_denied`)  |
| `error_description`   | string | Descrição legível do erro (opcional)                   |

**Respostas**

| Código | Content-Type                  | Descrição                                                            |
|-------:|-------------------------------|----------------------------------------------------------------------|
| `200`  | `text/html`                   | Página `templates/callback.html` exibindo o `code`                   |
| `400`  | `text/plain; charset=utf-8`   | `Erro na autorização: <error>` ou `Nenhum código de autorização recebido.` |

**Exemplos**

Sucesso:

```bash
curl -i "http://localhost:5000/callback?code=abc123xyz"
```

```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
```

Erro retornado pelo Tiny:

```bash
curl -i "http://localhost:5000/callback?error=access_denied&error_description=user+denied"
```

```
HTTP/1.1 400 BAD REQUEST
Content-Type: text/plain; charset=utf-8

Erro na autorização: access_denied
```

Sem parâmetros:

```bash
curl -i "http://localhost:5000/callback"
```

```
HTTP/1.1 400 BAD REQUEST
Content-Type: text/plain; charset=utf-8

Nenhum código de autorização recebido.
```

---

## Função auxiliar: `build_auth_url`

Definida em `app.py:16`.

```python
build_auth_url(client_id: str, redirect_uri: str, state: str) -> str
```

Monta a URL de autenticação OpenID Connect do Tiny. Utiliza `urllib.parse.urlencode` para encodar os parâmetros. **Não concatene query strings manualmente** — use esta função sempre que precisar montar a URL.

**Parâmetros**

| Nome           | Tipo   | Descrição                                          |
|----------------|--------|----------------------------------------------------|
| `client_id`    | string | Identificador do cliente no Tiny                   |
| `redirect_uri` | string | URL de callback (deve estar registrada no Tiny)    |
| `state`        | string | Token anti-CSRF (use `secrets.token_urlsafe`)      |

**Retorno**

URL completa apontando para `https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/auth` com os parâmetros do fluxo OAuth2 authorization-code.
