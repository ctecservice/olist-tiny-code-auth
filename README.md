# Olist Tiny Code Auth

> Aplicação web para geração do **Authorization Code** do fluxo OAuth2 do **Olist Tiny v3**.

[![Licença](https://img.shields.io/badge/licença-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Deploy](https://img.shields.io/badge/Vercel-online-000000.svg?logo=vercel&logoColor=white)](https://olist-tiny-teste2.vercel.app/)

---

## Sobre o projeto

Esta aplicação é uma **ponte OAuth2** que simplifica o primeiro passo do fluxo de autenticação do **Olist Tiny v3**: a obtenção do `authorization code`.

Em vez de construir manualmente a URL de autorização, abrir o navegador, autenticar e copiar o `code` da URL de retorno, você informa o `client_id` em um formulário, autentica-se no Tiny e recebe o código pronto para copiar e usar.

A URL completa do fluxo OIDC é montada automaticamente pela aplicação com os parâmetros exigidos pelo Tiny (`client_id`, `redirect_uri`, `scope=openid`, `response_type=code`, `state` anti-CSRF).

> **Aviso importante:** este portal serve **apenas** para gerar o código de autorização do Olist Tiny v3. A troca do código pelo `access_token`/`refresh_token` é feita diretamente pelo seu backend contra o endpoint de token do Tiny, conforme documentado em [api-docs.erp.olist.com](https://api-docs.erp.olist.com/documentacao/comecando/autenticacao).

---

## Demo

A aplicação está publicada em:

**https://olist-tiny-code-auth.vercel.app//**

Abra o link, informe o `client_id` registrado no seu app do Olist Tiny, autentique-se e o `authorization code` será exibido na tela.

---

## Privacidade e segurança

> **Nenhum dado é gravado.** A aplicação é **100% serverless** e não possui banco de dados, cache persistente ou armazenamento local.

- O `client_id` informado no formulário é usado **apenas** para montar a URL de redirecionamento e descartado em seguida.
- O `authorization code` retornado pelo Tiny é exibido na página e **não é armazenado**.
- O `state` anti-CSRF é gerado por request e descartado após o redirect.
- Toda a execução acontece em funções serverless do Vercel, sem estado entre requisições.

---

## Tecnologias

| Camada          | Tecnologia                                     |
|-----------------|------------------------------------------------|
| Linguagem       | Python 3.9+                                    |
| Framework web   | Flask 3.0.3                                    |
| Encoding URL    | `urllib.parse.urlencode` (stdlib)              |
| Tokens CSRF     | `secrets.token_urlsafe` (stdlib, CSPRNG)       |
| Testes          | pytest 8.2.0                                   |
| Deploy          | Vercel (`@vercel/python`)                      |
| Templates       | Jinja2 (nativo do Flask)                       |

Sem dependências externas em runtime além do Flask. Sem SDKs proprietários.

---

## Como usar

### Opção 1 — Usar a versão publicada (recomendado)

1. Acesse **[https://olist-tiny-code-auth.vercel.app//](https://olist-tiny-code-auth.vercel.app//)**.
2. No campo **Client ID**, cole o `client_id` do seu aplicativo registrado no Olist Tiny.
3. Clique em **Gerar Código de Autorização**.
4. Faça login no Tiny e autorize o acesso.
5. Copie o `authorization code` exibido na página de retorno.
6. Use o código em uma requisição `POST` para o endpoint de token do Tiny:

```bash
curl -X POST https://accounts.tiny.com.br/realms/tiny/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=authorization_code" \
  -d "client_id=SEU_CLIENT_ID" \
  -d "client_secret=SEU_CLIENT_SECRET" \
  -d "code=AUTHORIZATION_CODE_RECEBIDO" \
  -d "redirect_uri=https://olist-tiny-code-auth.vercel.app/callback"
```

### Opção 2 — Rodar localmente

Pré-requisitos: Python 3.9 ou superior.

```bash
git clone <repositorio>
cd olist-tiny-code-auth
pip install -r requirements.txt
python app.py
```

A aplicação iniciará em `http://localhost:5000`. Use `http://localhost:5000/callback` como `redirect_uri` ao testar localmente.

---

## Como configurar no Olist Tiny v3

Para que o Tiny aceite o redirect de volta para esta aplicação, você precisa registrar a **URL de Redirecionamento** no cadastro do seu aplicativo.

1. Acesse o painel do desenvolvedor do Olist Tiny.
2. Abra o cadastro do seu aplicativo (ou crie um novo).
3. No campo **URL de Redirecionamento** (Redirect URI), informe:

```
https://olist-tiny-code-auth.vercel.app//callback
```

> Em ambiente de desenvolvimento local, use `http://localhost:5000/callback`. A URL deve ser **exata** — incluindo o caminho `/callback` e o esquema (`http` vs `https`).

4. Salve o cadastro. O `client_id` e o `client_secret` serão gerados (ou exibidos) pelo painel.
5. Use o `client_id` no formulário desta aplicação para iniciar o fluxo.

Mais detalhes: **[Documentação oficial de autenticação Olist Tiny](https://api-docs.erp.olist.com/documentacao/comecando/autenticacao)**.

---

## Estrutura do projeto

```
olist-tiny-code-auth/
├── app.py                  # Objeto Flask, rotas e build_auth_url
├── index.py                # Entrypoint do Vercel (importa app)
├── requirements.txt        # Dependências de runtime e teste
├── vercel.json             # Build e roteamento do Vercel
├── test_app.py             # 12 testes pytest
├── LICENSE                 # MIT
├── README.md               # Este arquivo
├── static/
│   └── Logotipo.png        # Logotipo da CTEC
├── templates/
│   ├── index.html          # Landing page com formulário de client_id
│   └── callback.html       # Exibição do authorization code
└── docs/
    ├── README.md           # Índice da documentação
    ├── uso.md              # Passo a passo detalhado
    ├── api.md              # Referência das rotas HTTP
    ├── arquitetura.md      # Fluxo OAuth2 e decisões de design
    └── deploy.md           # Configuração de deploy
```

| Arquivo                 | Responsabilidade                                                    |
|-------------------------|---------------------------------------------------------------------|
| `app.py`                | Define o objeto `app` Flask, as 3 rotas e a função `build_auth_url` |
| `index.py`              | Entrypoint do Vercel — apenas importa `app` e chama `app.run()`     |
| `templates/index.html`  | Landing page com o formulário onde o usuário informa o `client_id`  |
| `templates/callback.html` | Página que exibe o `code` retornado pelo Tiny com botão de copiar  |
| `static/Logotipo.png`   | Logotipo da CTEC exibido no cabeçalho e no rodapé                   |
| `test_app.py`           | Suíte pytest cobrindo rotas, erros e encoding da URL                |
| `vercel.json`           | Configura o builder Python e o roteamento de qualquer URL para o app|

---

## Rotas

| Método | Rota         | Descrição                                                |
|--------|-------------|----------------------------------------------------------|
| GET    | `/`          | Formulário para informar o `client_id`                   |
| POST   | `/authorize` | Redireciona para a URL de autenticação do Tiny           |
| GET    | `/callback`  | Recebe e exibe o `authorization code` retornado pelo Tiny|

Referência completa (parâmetros, respostas, exemplos `curl`): **[docs/api.md](docs/api.md)**.

---

## Documentação

- **[docs/README.md](docs/README.md)** — índice da documentação
- **[docs/uso.md](docs/uso.md)** — passo a passo detalhado de uso
- **[docs/api.md](docs/api.md)** — referência das rotas e da função `build_auth_url`
- **[docs/arquitetura.md](docs/arquitetura.md)** — fluxo OAuth2 e decisões de design
- **[docs/deploy.md](docs/deploy.md)** — deploy no Vercel

---

## Variáveis de ambiente

| Variável           | Obrigatória | Descrição                                       | Padrão                 |
|--------------------|:-----------:|-------------------------------------------------|------------------------|
| `FLASK_SECRET_KEY` | Não         | Chave secreta para `app.secret_key` do Flask    | Gerada aleatoriamente  |

> Como o app não utiliza `flask.session`, a chave secreta é definida apenas por conformidade com o Flask. Em modo dev, o valor gerado por request é suficiente. Em produção, definir `FLASK_SECRET_KEY` no painel do Vercel (Settings → Environment Variables) garante comportamento consistente entre deploys.

---

## Testes

```bash
python -m pytest test_app.py -v
```

12 testes cobrindo:

- Renderização do formulário
- Validação de `client_id` ausente/vazio
- Redirecionamento correto com todos os parâmetros OAuth2
- Tratamento de erro no callback (`error`, `error_description`)
- Encoding correto de parâmetros com caracteres especiais em `build_auth_url`

---

## Licença

Este projeto está licenciado sob a **MIT License** — veja [LICENSE](LICENSE).

---

## Links úteis

- [Demo ao vivo](https://olist-tiny-code-auth.vercel.app/)
- [Documentação de autenticação Olist Tiny](https://api-docs.erp.olist.com/documentacao/comecando/autenticacao)
- [OAuth 2.0 Authorization Framework (RFC 6749)](https://datatracker.ietf.org/doc/html/rfc6749)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [Flask — Documentação oficial](https://flask.palletsprojects.com/)
- [Vercel Python Runtime](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
