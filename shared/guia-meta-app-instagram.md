# Guia Meta: App Instagram multi-cliente (Business Login)

Guia prático para a **smark** (ou qualquer agência/tech provider) criar **um** aplicativo Meta, ligar à Business Manager, configurar **Instagram Login** e obter **Advanced Access** para que **cada cliente** conecte o próprio Instagram Business/Creator.

> Alinhado à documentação Meta (Instagram Platform, Business Login, App Review — 2025/2026) e ao que o studio já implementa em `scripts/_canais.py`.

**Links oficiais (abra e deixe abertos):**

| Tema | URL |
|------|-----|
| Criar app Instagram | https://developers.facebook.com/documentation/development/create-an-app/other-app-types/instagram-apis |
| Business Login (OAuth) | https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/business-login |
| App Review Instagram | https://developers.facebook.com/documentation/instagram-platform/app-review |
| App Dashboard | https://developers.facebook.com/apps |
| Business Manager | https://business.facebook.com |
| Verificação de empresa | https://developers.facebook.com/documentation/development/release/business-verification |

---

## 0. O que você está construindo (mapa mental)

```
┌─────────────────────────────────────────────────────────────┐
│  SUA Business Manager (smark)                                │
│    └── Meta App “smark Studio” (UM app)                      │
│          └── Produto Instagram + Instagram Login             │
│                └── Advanced Access (App Review)              │
└────────────────────────────┬────────────────────────────────┘
                             │ OAuth (cada cliente autoriza)
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   @cliente_a           @cliente_b           @cliente_c
   (Business/Creator)   (Business/Creator)   (Business/Creator)
```

- **1 app Meta** da smark — não cria um app por cliente.
- **Cada marca/cliente** clica em Conectar no studio → faz login no Instagram → autoriza permissões → token fica em `.secrets/canais/<marca>/`.
- Conta do cliente precisa ser **Instagram Professional** (Business ou Creator). Conta **pessoal não funciona**.

### Dois caminhos de API (escolha o certo)

| Caminho | Quando usar | Exige Facebook Page? |
|---------|-------------|----------------------|
| **Instagram Login** (recomendado pro studio) | Multi-cliente; login direto com @ do Instagram | **Não** |
| Facebook Login for Business | Conta IG já ligada a Page; features extras (shopping, etc.) | **Sim** |

O studio smark usa **Instagram Login** (`instagram_business_*`).

**Aviso Meta:** o app usa **Instagram Login OU Facebook Login** — não os dois no mesmo fluxo.

---

## 1. Pré-requisitos (antes de criar o app)

### 1.1 Conta Facebook pessoal de admin
- Você (ou o sócio) precisa de um Facebook **pessoal** com 2FA.
- Essa pessoa será admin do app e da BM.

### 1.2 Business Manager / Business Portfolio
1. Acesse https://business.facebook.com  
2. Crie ou entre na **Business Portfolio** da smark (ex.: “Smark Tech”).  
3. Confirme e-mail e telefone da empresa.

### 1.3 Verificação de empresa (Business Verification) — obrigatória para multi-cliente
Para publicar app e pedir **Advanced Access** (servir contas que **você não administra**), a BM precisa estar **verificada**.

1. BM → **Configurações da empresa** → **Central de segurança** / **Verificação de empresa**  
   (ou: https://business.facebook.com/settings )  
2. Envie documentos típicos:
   - CNPJ / contrato social / fatura de utilidade / extrato bancário com razão social  
3. Aguarde aprovação (dias a semanas). **Não deixe para o final** — começa em paralelo.

### 1.4 Contas Instagram de teste
- Pelo menos **1 Instagram Business ou Creator** que você controla (para desenvolvimento).  
- Ideal: 2ª conta “cliente fake” para screencast do App Review.

Como virar Professional no app do Instagram:
**Configurações → Conta → Mudar para conta profissional → Empresa ou Criador.**

---

## 2. Criar o Meta App (passo a passo na web)

### 2.1 Entrar no Developers
1. Abra https://developers.facebook.com  
2. Login com o Facebook admin da BM.  
3. Se pedir, aceite os termos de desenvolvedor.  
4. Clique em **My Apps** → **Create App**.

### 2.2 Fluxo de criação (docs Meta atuais)

| Passo | O que escolher |
|-------|----------------|
| **Use case** | **Other** (Outro) |
| **App type** | **Business** (obrigatório para Instagram) |
| **App name** | Ex.: `smark Studio` (aparece pro usuário no OAuth) |
| **Contact email** | E-mail que a Meta usará (App Review, alertas) |
| **Business** | Conecte a **Business Portfolio smark** (agora ou em Settings → Basic) |

Limite: no máx. **15 apps** sem BM verificada onde você é admin/dev. Apps arquivados contam.

### 2.3 Adicionar o produto Instagram
No dashboard do app:
1. Encontre o card **Instagram** → **Set up**.  
2. Escolha **API setup with Instagram login**  
   (não “Facebook login”, a menos que queira o caminho com Page).

Isso adiciona o fluxo **Business Login for Instagram**.

### 2.4 Contas de teste (Standard Access)
Enquanto o app está em **Development** + **Standard Access**:
- Só funcionam contas com **papel no app** (Admin, Developer, Tester) **ou** Instagram adicionado no setup de teste.

1. **App Roles → Roles** → adicione Facebook de quem testa.  
2. Em **Instagram → API setup with Instagram login** → adicione Instagram de teste e faça login.

Assim você testa **sem** App Review (só contas internas).

---

## 3. Configurar Business Login (OAuth) — o que o studio precisa

Painel:
**App Dashboard → Instagram → API setup with Instagram login → Set up Instagram business login / Business login settings**

### 3.1 Dados que você vai copiar pro `.env`

| Campo no dashboard Meta | Variável no vault smark |
|-------------------------|-------------------------|
| **Instagram App ID** | `INSTAGRAM_APP_ID=` |
| **Instagram App Secret** | `INSTAGRAM_APP_SECRET=` |
| **OAuth redirect URIs** | `INSTAGRAM_REDIRECT_URI=` |

Exemplo local (já previsto no studio):

```bash
INSTAGRAM_APP_ID=123456789012345
INSTAGRAM_APP_SECRET=abcdef...
INSTAGRAM_REDIRECT_URI=http://127.0.0.1:8765/oauth/instagram/callback
CANAIS_MODE=auto
```

### 3.2 Redirect URIs (crítico)

Cadastre **exatamente** as URLs (a Meta é pedante com barra final `/`):

| Ambiente | URI |
|----------|-----|
| Local (hoje) | `http://127.0.0.1:8765/oauth/instagram/callback` |
| Produção (quando tiver domínio) | `https://seu-dominio.com/oauth/instagram/callback` |

No dashboard: **Business login settings → OAuth redirect URIs → Add URI**.

### 3.3 Permissões (scopes) para multi-cliente + postagem

Para o studio publicar arte:

| Permission | Para quê | App Review multi-cliente? |
|------------|----------|---------------------------|
| `instagram_business_basic` | Perfil, @, id | **Sim** (Advanced) |
| `instagram_business_content_publish` | Criar container + publicar feed/reels | **Sim** (Advanced) |

Opcionais depois:
- `instagram_business_manage_comments`
- `instagram_business_manage_messages` (puxa feature **Human Agent**)

No código smark (`_canais.py`) já pedimos:
`instagram_business_basic` + `instagram_business_content_publish`.

### 3.4 Deixar o app “testável”
**Settings → Basic:**
- **App icon** 1024×1024  
- **Privacy Policy URL** (página pública em pt ou en — **obrigatória** pro Review)  
- **App Category** (ex.: Business and Pages / Productivity)  
- **Business verification** ligada à BM  
- **App Domains** (quando for HTTPS real)

**Privacy Policy** precisa dizer, em linguagem clara:
- que o cliente conecta o Instagram;
- que usamos o token para **publicar conteúdo que o cliente autorizou no studio**;
- que não vendemos dados;
- como revogar (desconectar no studio + remover app em Configurações Instagram).

---

## 4. Standard Access vs Advanced Access (multi-cliente)

| Nível | Quem pode autorizar | App Review? |
|-------|---------------------|-------------|
| **Standard Access** | Só contas de quem tem papel no app / testes | Não |
| **Advanced Access** | **Qualquer** Instagram Business/Creator que autorizar OAuth | **Sim** |

Se a smark é **Tech Provider** e cada cliente conecta o próprio @ → você **precisa de Advanced Access** nas permissões acima.  
Isso está explícito na tabela da Meta (App Review for Instagram API).

Fluxo típico de vida do app:

```
Development + Standard  →  testa com seus IGs
        ↓
Business Verification OK
        ↓
App Review (Advanced Access) + screencasts
        ↓
Live + clientes reais conectam
```

---

## 5. App Review — como aprovar para multi-cliente

### 5.1 Onde submeter
**Instagram → API setup with Instagram login → Complete app review → Continue to app review**  
ou **App Review → Requests**.

### 5.2 Checklist Meta (não pule)

1. **App Settings completos** (ícone, privacy policy, categoria, e-mail).  
2. **App verificável externamente** (URL web que o revisor abre — localhost **não** basta para Review final; use staging HTTPS).  
3. **Instruções de login** passo a passo (Web) + credenciais de teste se a área for fechada.  
4. **≥ 1 chamada de API bem-sucedida** com cada permission em Development (antes de pedir Advanced).  
5. **Descrição + screencast por permission**.

### 5.3 O que gravar no screencast (o revisor é rigoroso)

Grave **em inglês** na UI se possível (recomendação Meta). Caso contrário, legendas em inglês.

**Roteiro sugerido (um vídeo por permission, ou um longo bem narrado):**

1. Abrir o **smark Studio** (staging).  
2. Ir em **Config → card da marca do cliente**.  
3. Clicar no **ícone Instagram** → tela de OAuth Instagram.  
4. Login com conta **Business/Creator de teste**.  
5. Aceitar permissões (`basic` + `content_publish`).  
6. Voltar ao studio mostrando **IG conectado** (@ visível).  
7. No Editor: exportar peça → **Publicar no Instagram**.  
8. Abrir o app Instagram / perfil e mostrar o post publicado.  
9. Mostrar **Desconectar** (revogação).

**Textos de use case (modelo):**

> **instagram_business_basic**  
> “Our agency tool lets each client brand connect their own Instagram professional account. We use this permission to identify the account (username, id) and store the connection so the correct brand publishes to the correct profile.”

> **instagram_business_content_publish**  
> “After the client designs a post in our studio, they click Publish. We create a media container and call media_publish so the image and caption go live on the client’s Instagram feed. We only publish content the client explicitly approved in the tool.”

### 5.4 Erros comuns (rejeição)

- Screencast sem mostrar o **botão de login** e o fluxo completo.  
- Pedir permission que o app **não usa**.  
- Privacy Policy genérica / 404.  
- Só localhost, sem staging público.  
- Conta de teste **pessoal** (não Business/Creator).  
- Não explicar o benefício **para o dono do Instagram** (o cliente), só “pra gente gerenciar”.

---

## 6. Depois da aprovação — operação multi-cliente

1. App em **Live** (modo produção).  
2. `.env` de produção com App ID/Secret e redirect HTTPS.  
3. Cada cliente no studio: **Config → ícone IG → autorizar**.  
4. Tokens long-lived (~60 dias) — o studio já tem refresh em `_canais.refresh_token_se_preciso`.  
5. Cliente precisa manter conta Professional; se voltar a pessoal, a API quebra.

### Publicação real (Content Publishing)
- Imagem precisa ser **URL pública HTTPS** (Meta baixa a arte).  
- Local: hoje o modo fake grava `_outbox/`; em produção será preciso hospedar PNG (S3, CDN, etc.) antes do `media_publish`.

---

## 7. Checklist único (imprima)

### BM / empresa
- [ ] Business Portfolio smark criada  
- [ ] Business Verification enviada / aprovada  
- [ ] Admin com 2FA  

### App
- [ ] Create App → Other → **Business**  
- [ ] App ligado à BM  
- [ ] Produto **Instagram** → **API setup with Instagram login**  
- [ ] Business login: App ID, Secret, Redirect URIs  
- [ ] Privacy Policy + ícone 1024 + categoria  
- [ ] Contas de teste Instagram Professional adicionadas  

### Desenvolvimento smark
- [ ] `.env` com `INSTAGRAM_APP_ID` / `SECRET` / `REDIRECT_URI`  
- [ ] `CANAIS_MODE=auto`  
- [ ] Teste OAuth com conta de teste (Standard)  
- [ ] Teste publish com URL HTTPS pública  

### Multi-cliente (Advanced)
- [ ] Staging HTTPS acessível ao revisor  
- [ ] Screencasts basic + content_publish  
- [ ] ≥1 API call bem-sucedida por permission  
- [ ] Submissão App Review aprovada  
- [ ] App Live  

---

## 8. Ordem do dia recomendada (cronograma realista)

| Dia | Ação |
|-----|------|
| **D0** | BM + iniciar Business Verification + criar app Business + Instagram Login |
| **D0–D1** | Redirect local, `.env`, conectar 1 marca de teste no studio (Standard) |
| **D1–D7** | Privacy policy, ícone, staging HTTPS, 1 post real de teste |
| **Paralelo** | Aguardar Business Verification |
| **Após BV** | Screencasts + App Review |
| **+1–4 sem.** | Aprovação Meta (varia) → Live multi-cliente |

---

## 9. Onde fica cada coisa no studio smark

| Conceito Meta | No código / vault |
|---------------|-------------------|
| OAuth start | `POST /canais/conectar` → `_canais.iniciar_oauth` |
| Callback real | `GET /oauth/instagram/callback` → `trocar_code_real` |
| Token por cliente | `.secrets/canais/<marca>/instagram.json` |
| Fake enquanto não tem app | `CANAIS_MODE=fake` ou App ID vazio |
| Doc operacional | `shared/canais-sociais.md` |
| Este guia | `shared/guia-meta-app-instagram.md` |

---

## 10. Resumo em 5 frases

1. Crie **um** app **Business** na BM smark e adicione **Instagram Login** (não um app por cliente).  
2. Configure **App ID, Secret e redirect** iguais ao `.env` do studio.  
3. Em Development, teste só com contas em **Roles** (Standard Access).  
4. Para clientes reais: **Business Verification** + **App Review (Advanced Access)** com screencast de conectar + publicar.  
5. Cada cliente autoriza o **próprio** Instagram Professional; o studio guarda o token e publica no perfil certo.

---

*Última atualização: alinhado à Meta Instagram Platform / Business Login / App Review (docs 2025–2026). A UI do dashboard muda com frequência — se um rótulo diferir, busque no menu lateral “Instagram → API setup with Instagram login”.*
