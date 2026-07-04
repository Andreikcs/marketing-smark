"""Imprime um bloco de metadados da arte para ser EMBUTIDO na nota única do post.
NÃO cria arquivo separado — a filosofia do vault é 1 arquivo por post (imagem + metadados
+ legenda + prompt na mesma nota). Importado por openai_image.py e gemini_image.py."""
import datetime
import os
from math import gcd


def _aspect(size):
    try:
        w, h = size.lower().split("x")
        w, h = int(w), int(h)
        g = gcd(w, h)
        return f"{w // g}:{h // g}"
    except Exception:
        return ""


def meta_block(out_png, meta):
    """Retorna um bloco YAML (campos arte-*) + a linha de embed, pra colar na nota do post."""
    today = datetime.date.today().isoformat()
    size = meta.get("tamanho", "")
    fn = os.path.basename(out_png)
    return "\n".join([
        "----- METADADOS DA ARTE (cole no frontmatter + corpo da nota do post) -----",
        f"arte: arte/{fn}",
        f"arte-modelo: {meta.get('modelo', '')}",
        f"arte-qualidade: {meta.get('qualidade', '')}",
        f"arte-tamanho: {size}",
        f"arte-proporcao: {_aspect(size)}",
        f"arte-paleta: {meta.get('paleta', '')}",
        f"arte-gerada-em: {today}",
        f"embed-no-corpo: ![[arte/{fn}]]",
    ])
