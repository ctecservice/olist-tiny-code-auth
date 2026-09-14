# Auditoria de Segurança — Relatório e Plano de Correção

**Projeto:** olist-tiny-code-auth
**Data da auditoria:** 14/09/2026
**Escopo:** `app.py`, `index.py`, `test_app.py`, `vercel.json`, `requirements.txt`, `templates/`, `docs/`, `robots.txt`, `.gitignore`
**Modalidade:** somente leitura — nenhum arquivo foi alterado

> **Uso deste documento:** este arquivo é a base de referência para futuras alterações de segurança. Ao implementar uma correção, marque o checkbox correspondente na seção "Plano de Correção" e registre a data na tabela de acompanhamento.

---

## 1. Resumo Executivo

Aplicação Flask minimalista (fluxo OAuth2 authorization-code): recebe `client_id` via formulário, redireciona ao IdP Tiny e exibe o `authorization code` no callback. **Sem banco, sem sessão, sem troca de token** — superfície de ataque pequena, mérito real do projeto.

### Pontos positivos confirmados

- Nenhum segredo hardcoded (apenas placeholders `SEU_CLIENT_SECRET` em docs)
- `state` gerado via CSPRNG (`secrets.token_urlsafe(16)`, ~128 bits)
- `urlencode` na montagem da URL (sem concatenação manual)
- Jinja2 autoescapa `{{ code }}` — sem XSS no callback
- `scope=openid` mínimo (princípio do menor privilégio)
- `.gitignore` cobre `.env*`, venv, chaves de IA
- LGPD: modelo stateless alinhado à minimização (art. 6º, III); code tratado como medida de segurança (art. 46)

---

## 2. Achados de Segurança

| # | Achado | Severidade | Evidência |
|---|--------|-----------|-----------|
| 1 | `state` OAuth2 gerado mas **nunca validado** no callback — proteção anti-CSRF da RFC 6749 §10.12 quebrada | 🔴 Alta/Crítica | `app.py:68` gera; callback `app.py:76-97` nunca compara |
| 2 | Ausência de `Cache-Control: no-store` na página que exibe o authorization code — risco de vazamento via cache CDN/proxy/navegador | 🔴 Alta | `app.py:97`, `templates/callback.html:338` |
| 3 | `POST /authorize` sem CSRF próprio nem allowlist de `client_id` — vetor de consent-phishing | 🟠 Média-Alta | `app.py:55-73`, `templates/index.html:736` |
| 4 | Flask 3.0.3 com **CVE-2026-27205** (fix em 3.1.3) — não explorável aqui, mas flagged por scanners | 🟠 Média | `requirements.txt:1` |
| 5 | `redirect_uri` derivado do header `Host` do request (host-header injection) — mitigado hoje pela validação do Tiny | 🟠 Média | `app.py:69` |
| 6 | Ausência total de headers de segurança (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy) | 🟠 Média | `app.py`, `vercel.json` |
| 7 | `FLASK_SECRET_KEY` opcional com fallback aleatório por instância (armadilha serverless) | 🟡 Média | `app.py:11` |
| 8 | `app.run(debug=True, host="0.0.0.0")` — Werkzeug debugger = RCE se exposto | 🟡 Baixa | `app.py:102` |
| 9 | `pytest` em requirements de produção — superfície de supply-chain desnecessária | 🟡 Baixa | `requirements.txt:2` |
| 10 | `vercel.json` usa `builds`/`routes` legados (deprecated) | 🟡 Baixa | `vercel.json:3-13` |
| 11 | Code em query string (histórico, logs, referrer) — inerente ao OAuth, mitigável via aviso na UI | 🟡 Baixa | `app.py:84` |
| 12 | Reflexão de `error_description` em `text/plain` — prática frágil | 🟡 Baixa | `app.py:90` |

### 2.1 Detalhe — Achado 1: `state` decorativo

A documentação admite abertamente que o state não é validado (`docs/arquitetura.md:67`), enquanto o site anuncia o contrário (`templates/index.html:650-653`: "State anti-CSRF... protegendo o fluxo contra CSRF"). **Anunciar proteção inexistente é em si um problema de segurança.**

Ataque possível: *authorization code injection* — atacante gera um code na própria conta e "empurra" para a vítima via link craftado (`/callback?code=CODIGO_DO_ATACANTE`), fazendo a vítima autenticar como o atacante.

### 2.2 Risco arquitetural (decisão de produto)

O `redirect_uri` público de terceiros (`https://olist-tiny-code-auth.vercel.app/callback`) centraliza authorization codes de múltiplos apps. Mitigantes hoje: code expira em ~300s e a troca exige `client_secret` que só o dono do app possui. **Se o app passar a trocar code→token no servidor, a urgência sobe para CRÍTICA imediata** — o domínio público se tornaria um honeypot de access_tokens de terceiros. Este risco deve ser documentado e comunicado aos usuários.

---

## 3. Divergências entre as análises (e resolução)

| Tema | Opiniões | Resolução |
|------|----------|-----------|
| **Urgência** | Modelo 1: CRÍTICA (bloqueante). Modelo 2: MÉDIA (sem vazamento imediato). Auditoria técnica: condicionalmente seguro | **ALTA / pré-produção** — bloqueante para promover uso amplo, não é emergência de incidente ativo |
| **Mecanismo do state** | Sessão Flask vs cookie assinado | **Cookie HttpOnly + SameSite=Lax assinado** — mais idiomático para serverless (cold starts, múltiplas instâncias) |
| **CSRF do formulário** | P1 vs impacto baixo | **P1** — hardening barato, previne escalonamento |
| **PKCE** | Recomendado vs desnecessário | **P3** — só faz sentido se o app evoluir para troca de token |

---

## 4. Plano de Correção Priorizado

### P0 — Imediato (bloqueante para produção)

- [ ] **Validar `state` no callback** — gravar em cookie HttpOnly + SameSite=Lax assinado em `/authorize`, comparar no `/callback` com `secrets.compare_digest`, rejeitar divergência com 400
  ```python
  # em /authorize:
  state = secrets.token_urlsafe(24)
  resp = redirect(auth_url)
  resp.set_cookie("oauth_state", state, httponly=True, samesite="Lax",
                  secure=True, max_age=600, path="/callback")
  return resp

  # em /callback:
  expected = request.cookies.get("oauth_state")
  returned = request.args.get("state")
  if not expected or not returned or not secrets.compare_digest(expected, returned):
      return "State invalido ou ausente.", 400
  ```
- [ ] **Tornar `FLASK_SECRET_KEY` obrigatória** no Vercel (variável de ambiente fixa; falhar o build se ausente)
- [ ] **Adicionar `Cache-Control: no-store`** na resposta do callback
  ```python
  return render_template("callback.html", code=code), 200, {
      "Cache-Control": "no-store, no-cache, must-revalidate"
  }
  ```
- [ ] **Remover/reescrever** o texto de `templates/index.html:650-653` que anuncia "State anti-CSRF" até que a validação esteja ativa

### P1 — Curto prazo (esta semana)

- [ ] **Headers de segurança** no `vercel.json`: CSP, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, HSTS, `Referrer-Policy: no-referrer`
- [ ] **Atualizar `Flask==3.1.3`** (corrige CVE-2026-27205)
- [ ] **Fixar `redirect_uri`** via variável de ambiente (`CALLBACK_URL`) — não derivar do header `Host`
- [ ] **CSRF token** no form `/authorize` (Flask-WTF ou manual) + **allowlist/rate limit de `client_id`** (mitiga consent-phishing)
- [ ] **Migrar `vercel.json`** de `builds`/`routes` (v2 legado) para `functions` + `rewrites` + `headers`

### P2 — Curto prazo

- [ ] `debug` condicional: `debug=os.environ.get("FLASK_DEBUG") == "1"` + proteger `app.run` com `if __name__ == "__main__"`
- [ ] Separar `pytest` → `requirements-dev.txt`
- [ ] Log level WARNING em produção; evitar logar `client_id` em INFO
- [ ] Adicionar `.env.example` documentando as variáveis esperadas

### P3 — Opcional / futuro

- [ ] Aviso explícito na tela de callback sobre o code aparecer em URL/histórico/logs
- [ ] Considerar **PKCE** (RFC 7636) se o app evoluir para troca de token
- [ ] `Disallow: /callback` no `robots.txt`

---

## 5. Acompanhamento das Correções

| Item | Prioridade | Status | Data | Observações |
|------|-----------|--------|------|-------------|
| Validar state no callback | P0 | Pendente | — | — |
| FLASK_SECRET_KEY obrigatória | P0 | Pendente | — | — |
| Cache-Control: no-store | P0 | Pendente | — | — |
| Remover texto enganoso do template | P0 | Pendente | — | — |
| Headers de segurança | P1 | Pendente | — | — |
| Flask 3.1.3 | P1 | Pendente | — | — |
| Redirect_uri fixo via env | P1 | Pendente | — | — |
| CSRF + allowlist client_id | P1 | Pendente | — | — |
| Migrar vercel.json | P1 | Pendente | — | — |
| debug condicional | P2 | Pendente | — | — |
| pytest → requirements-dev | P2 | Pendente | — | — |
| Log level produção | P2 | Pendente | — | — |
| .env.example | P2 | Pendente | — | — |
| Aviso na tela de callback | P3 | Pendente | — | — |
| PKCE | P3 | Pendente | — | — |
| robots.txt /callback | P3 | Pendente | — | — |

---

## 6. Verificação Pós-Correção

1. `curl -I "https://olist-tiny-code-auth.vercel.app/callback?code=teste"` → confirmar `Cache-Control: no-store`, `Referrer-Policy`, `X-Content-Type-Options`, CSP e HSTS presentes
2. Fluxo real com client_id de teste → confirmar cookie `oauth_state` (HttpOnly; Secure; SameSite=Lax) → callback sem state ou com state divergente → esperar **400**
3. `POST /authorize` com `Host: evil.example` → confirmar redirect com `redirect_uri` do domínio fixo
4. `pip-audit -r requirements.txt` → zero CVEs após upgrade
5. `python -m pytest test_app.py -v` → 18 testes passando (adicionar testes para state e headers)
6. Na página de callback, clicar em link externo e verificar que o code não aparece no header `Referer` do destino

---

## 7. Referências

- RFC 6749 §10.12 (CSRF em OAuth2)
- OAuth 2.0 Security BCP — RFC 9700 §4.7
- OIDC Core §15.5.2
- CVE-2026-27205 / GHSA-68rp-wp8r-4726 (Flask < 3.1.3)
- CWE-352, CWE-524, CWE-444, CWE-693
- OWASP Secure Headers Project
- LGPD art. 6º (minimização) e art. 46 (medidas de segurança)
