# Deploy no Vercel

O projeto já vem pronto para deploy no Vercel via `vercel.json`.

---

## Configuração

`vercel.json`:

```json
{
  "version": 2,
  "builds": [
    { "src": "index.py", "use": "@vercel/python" }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "index.py" }
  ]
}
```

- **Build**: usa o builder `@vercel/python` apontando para `index.py`.
- **Roteamento**: qualquer URL (`/(.*)`) é encaminhada para `index.py`, que importa o `app` Flask de `app.py`.

---

## Passo a passo

1. Suba o repositório para o GitHub.
2. Em [vercel.com/new](https://vercel.com/new), importe o repositório.
3. O Vercel detecta automaticamente o `vercel.json` — não há comando de build nem diretório de output a configurar.
4. (Opcional) Em **Settings → Environment Variables**, adicione:
   - `FLASK_SECRET_KEY` — chave secreta para sessões Flask. Recomendado em produção para manter sessões entre deploys.
5. Clique em **Deploy**.

Após o deploy, o Vercel fornece uma URL pública do tipo `https://olist-tiny-code-auth.vercel.app`.

---

## Configurando o `redirect_uri` no Tiny

Após o deploy, registre a URL de callback no painel do Tiny ERP. O formato exato depende do cadastro de aplicativo, mas será algo como:

```
https://olist-tiny-code-auth.vercel.app/callback
```

> O `redirect_uri` usado pela aplicação é gerado dinamicamente via `url_for('callback', _external=True)`, que usa o host do request. Em produção no Vercel isso resulta automaticamente na URL pública acima.

---

## Limites e observações

- O Vercel executa funções serverless — o `app.run()` de `app.py` não é usado em produção (só em dev local).
- Cada requisição pode iniciar uma nova instância fria. A aplicação é leve, sem dependências externas em runtime (apenas Flask), então o cold start é rápido.
- Logs ficam disponíveis em **Vercel Dashboard → Project → Logs**.

---

## Troubleshooting

| Problema                           | Solução                                                          |
|------------------------------------|------------------------------------------------------------------|
| Build falha no Vercel              | Verifique se `requirements.txt` está commitado e tem `Flask`     |
| `404 Not Found` em todas as rotas  | Confira `vercel.json` — `dest` deve apontar para `index.py`      |
| Callback retorna URL errada        | Em dev local, use `http://localhost:5000/callback`. No Vercel, use a URL pública + `/callback` |
