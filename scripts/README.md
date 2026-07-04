# scripts/

Ferramentas locais do vault. Rodam no seu PC.

## gemini_image.py — geração de imagem via Gemini

Gera UMA imagem PNG a partir de um prompt, usando a Gemini Image API.

```bash
cd /Users/andreik/smark
python3 scripts/gemini_image.py --out caminho/arte.png --prompt-file /tmp/prompt.txt --aspect 4:5
```

- **Chave:** lida de `.env` na raiz do vault (`GEMINI_API_KEY`). Nunca passada por linha de comando. `.env` é gitignored e `chmod 600`.
- **Modelo:** `gemini-2.5-flash-image` (default). Trocável via `GEMINI_IMAGE_MODEL` no `.env`.
- **Saída:** carrosséis vão para `marcas/<marca>/publicacoes/social/instagram/arte/<slug>/` (gitignored — regeneráveis pelo briefing).

### ⚠️ Requer billing ativo

O modelo de imagem **não** está no tier gratuito do Gemini. Sem billing, a API retorna `429 / limit: 0`.
Ative o tier pago em https://aistudio.google.com/ (Billing) no projeto da chave, e funciona sem mudar código.

### 🔐 Segurança

A chave atual foi compartilhada em texto aberto durante a configuração. **Recomendado gerar uma chave nova** e restringi-la depois de confirmar que tudo funciona. Atualize só o valor em `.env`.

### Custo

Cobrado por imagem gerada (centavos por imagem, conforme tabela do Gemini). Um carrossel de 7 frames = 7 chamadas.
