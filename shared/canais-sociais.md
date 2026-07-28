# Canais sociais por marca (Instagram → LinkedIn)

Cada **marca/cliente** conecta o próprio Instagram. A smark usa **um** Meta App; os clientes só autorizam o OAuth.

## Fluxo

1. Config → card da marca → **Conectar** (Instagram)
2. OAuth (fake hoje / Meta amanhã) → token em `.secrets/canais/<marca>/instagram.json`
3. Editor → exportar → **Publicar no Instagram**
   - fake: grava em `marcas/<marca>/publicacoes/social/instagram/_outbox/`
   - real: Content Publishing API (`/{ig-user-id}/media` + `media_publish`)

## App fake → real

No `.env` do vault:

```bash
# deixe vazio = modo fake (simula login)
INSTAGRAM_APP_ID=
INSTAGRAM_APP_SECRET=
INSTAGRAM_REDIRECT_URI=http://127.0.0.1:8765/oauth/instagram/callback
# auto | fake | real
CANAIS_MODE=auto
```

Quando o App Meta estiver pronto:

1. Meta for Developers → app Business + produto Instagram
2. OAuth redirect URI = `http://127.0.0.1:8765/oauth/instagram/callback` (e o domínio prod depois)
3. Permissões: `instagram_business_basic`, `instagram_business_content_publish`
4. Preencha `INSTAGRAM_APP_ID` e `INSTAGRAM_APP_SECRET`
5. Contas de teste no app (Standard Access) ou App Review (Advanced Access multi-cliente)

## Requisitos da conta do cliente

- Instagram **Business** ou **Creator** (não pessoal)
- Com Instagram Login: **não** exige Page do Facebook
- Com Facebook Login legado: exige Page vinculada

## Segurança

- Tokens **nunca** vão pro git (`.secrets/` no `.gitignore`)
- API `/canais` devolve só status público (username, conectado) — sem access_token
- Um vínculo por marca; desconectar apaga o JSON local

## LinkedIn

Estrutura pronta (`canal=linkedin`, status `em_breve`). OAuth na próxima etapa.
