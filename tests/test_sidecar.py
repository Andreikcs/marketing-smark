import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _sidecar  # noqa: E402


def test_bloco_do_chamador_antigo_e_exatamente_este():
    """Trava o bloco inteiro para quem chama só com as 4 chaves antigas.

    gemini_image.py continua chamando assim, e a decisão de produto é que os
    campos novos apareçam mesmo vazios. Asserção de igualdade, não de substring:
    um teste de substring passaria mesmo se a ordem ou os campos mudassem.
    """
    import datetime
    hoje = datetime.date.today().isoformat()
    bloco = _sidecar.meta_block("/x/arte/01.png", {"modelo": "gpt-image-1.5",
                                                   "qualidade": "high",
                                                   "tamanho": "1024x1536",
                                                   "paleta": "roxo"})
    esperado = "\n".join([
        "----- METADADOS DA ARTE (cole no frontmatter + corpo da nota do post) -----",
        "arte: arte/01.png",
        "arte-modelo: gpt-image-1.5",
        "arte-provider: ",
        "arte-qualidade: high",
        "arte-tamanho: 1024x1536",
        "arte-proporcao: 2:3",
        "arte-seed: ",
        "arte-paleta: roxo",
        "arte-custo-usd: ",
        "arte-suplente: ",
        f"arte-gerada-em: {hoje}",
        "embed-no-corpo: ![[arte/01.png]]",
    ])
    assert bloco == esperado


def test_inclui_campos_novos():
    bloco = _sidecar.meta_block("/x/arte/01.png", {
        "modelo": "google/gemini-3-pro-image", "tamanho": "1024x1536",
        "seed": 12345, "custo_usd": 0.135,
        "provider": "openrouter", "suplente_usado": False})
    assert "arte-seed: 12345" in bloco
    assert "arte-custo-usd: 0.135" in bloco
    assert "arte-provider: openrouter" in bloco
    assert "arte-suplente: false" in bloco


def test_suplente_true_sai_como_true():
    bloco = _sidecar.meta_block("/x/a.png", {"suplente_usado": True})
    assert "arte-suplente: true" in bloco
