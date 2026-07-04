# Brand Book — Grupo Smark

> Documento-mestre da identidade do grupo. Fonte de verdade técnica: `design-system/tokens/tokens.json`. Vitrine visual: projeto "Grupo Smark — Design System" no claude.ai/design.

## 1. A casa
A **smark.** é uma casa de tecnologia e IA operacional: implanta tecnologia e IA dentro da operação do cliente **e** constrói plataformas de IA próprias (Provider Max, Elever AI) como prova de capacidade. Um grupo de tecnologia — não consultoria solo, não SaaS solto.

## 2. Arquitetura de marca (endossada / branded house)
- **smark** (mãe) — implanta tecnologia e IA na operação de qualquer negócio.
- **Provider Max** — IA na operação comercial de ISPs.
- **Elever AI** — IA na pré-venda / inbound.
- **Fio condutor:** *“IA que deixa marcos na operação.”*
- **Endosso:** produtos assinam **“uma plataforma smark.”**; a mãe mostra os produtos. O loop fecha.

## 3. Voz
Próxima · direta · operacional · honesta · sem jargão vazio. Provoca via insight, nunca via insulto.
**Linha vermelha:** sem métrica de vaidade, sem promessa absoluta, sem tom de hype, sem imagem de IA cafona.
Voltagem: smark sóbria/premium · Provider Max comercial-direta · Elever veloz/moderna.

## 4. Mensagem
**As 4 dores (“O Padrão”):** (1) sistema faz quase tudo menos a parte que importa; (2) dependência de pessoa-chave; (3) time em trabalho manual; (4) “se desse pra automatizar”. Material de hook.

## 5. Sistema visual
- **Base:** `#0B0B0B` · superfície `#15151A` · texto `#FFFFFF` · apoio `#A1A1A1`.
- **Acentos:** smark roxo `#7C3AED` (lime `#C6F24E` como secundário) · Provider Max lime `#C6F24E` · Elever AI roxo `#7C3AED` / claro `#A472FF`.
- **Tipografia:** Display **Anton** (headline) · Texto/labels **Archivo**. *(Provisório — confirmar oficiais.)*
- **Logo:** quadrado + glyph (A / P / E) + wordmark. SVGs de trabalho em `design-system/assets/`.
- **Moldura (chassi):** etiqueta vertical + chip de conta (@handle + ✓) + rodapé (@handle · assinatura/endosso · ©ano). Cravada na imagem → a marca viaja no share/save.
- **Imagem:** fundo gerado por IA (cinematográfico, realista, acento da marca) + tipografia real por cima (compositor, render 2x).
- **Iconografia:** linha fina, geométrica, traço 2–2.5px.
- **Grid:** feed 4:5 (1080×1350) · quadrado 1:1 · story 9:16 · margem 64px · raio 16px.

## 6. Pipeline de produção
1. Texto: `/post-instagram`, `/post-linkedin`, `/pauta` (leem `arquitetura-marca` + branding).
2. Fundo: `scripts/openai_image.py` (cena sem texto).
3. Arte: `scripts/compositor.py` (tipografia real + moldura + selo).
4. Tokens (`tokens.json`) alimentam design system **e** compositor → consistência automática.

## 7. Pendências do usuário
🎨 hex oficiais · 🟣 confirmar smark roxo vs lime · 🔗 @handles + verificado real · 🔤 subir fontes (Upload fonts) · ✒️ aprovar/finalizar logo SVG.

---

## Prompt pronto — gerar no claude.ai/design (Doc ou Slides)
> Cole isto numa nova criação **Doc** (brand book PDF) ou **Slides** (deck institucional) dentro do projeto "Grupo Smark — Design System" — ele já usa este design system por padrão:

```
Crie um [documento de brand book / deck institucional] do Grupo Smark usando o design system deste projeto.
Estrutura: a casa smark; arquitetura de marca endossada (smark mãe + Provider Max + Elever AI, "uma plataforma smark"); fio condutor "IA que deixa marcos na operação"; voz e linha vermelha; sistema visual (cores, tipografia, logo, moldura, imagem, grid); uma página/slide por marca com cor, logo, @handle e exemplo de post.
Tom premium, escuro, confiante. Português do Brasil. Use os componentes e cores do design system.
```
