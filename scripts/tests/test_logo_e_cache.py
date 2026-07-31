#!/usr/bin/env python3
"""Interpretação da logo e os caches que seguram o desempenho do editor.

Estes testes existem por causa de uma regressão real: o editor rodava rápido no
Mac e travava no Railway. A causa não era a rede — era trabalho repetido que o
Mac absorvia e o container não. Cada teste aqui trava uma dessas repetições.
"""
import io
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
VAULT = os.path.dirname(SCRIPTS)
sys.path.insert(0, SCRIPTS)

PIL = pytest.importorskip("PIL")
from PIL import Image, ImageDraw  # noqa: E402

import _logo  # noqa: E402


def _png_com_fundo_branco(w=800, h=300):
    """Logo como o cliente costuma mandar: marca escura em canvas branco."""
    im = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(im)
    # símbolo à esquerda + assinatura à direita, como a maioria dos wordmarks
    d.ellipse((20, int(h * .13), int(h * .8), int(h * .87)), fill=(20, 20, 30))
    d.rectangle((int(w * .38), int(h * .43), int(w * .88), int(h * .57)),
                fill=(20, 20, 30))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
       b'<circle cx="50" cy="50" r="40" fill="#8B3CF7"/>'
       b'<rect x="20" y="45" width="60" height="10" fill="#fff"/></svg>')


class TestInterpretacao:
    def test_fundo_branco_vira_transparente(self):
        png = _logo.normalizar(_png_com_fundo_branco(), ".png")
        im = Image.open(io.BytesIO(png))
        assert im.mode == "RGBA"
        # se o canvas branco não saiu, o alpha mínimo seria 255
        assert im.split()[-1].getextrema()[0] == 0

    def test_saida_e_png_dentro_do_limite(self):
        png = _logo.normalizar(_png_com_fundo_branco(), ".png")
        im = Image.open(io.BytesIO(png))
        assert im.format == "PNG"
        assert max(im.size) <= _logo.LADO_BRASAO

    def test_jpeg_tambem_e_aceito(self):
        im = Image.new("RGB", (600, 600), (255, 255, 255))
        ImageDraw.Draw(im).ellipse((100, 100, 500, 500), fill=(200, 30, 40))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=90)
        png = _logo.normalizar(buf.getvalue(), ".jpg")
        assert Image.open(io.BytesIO(png)).mode == "RGBA"

    def test_wordmark_continua_wordmark(self):
        """Regressão real: o recorte quadrado virava "smark." em "rk".

        A assinatura por extenso tem que sair inteira do normalizar(); quem
        recorta em quadrado é só o caminho da tab.
        """
        im = _logo.interpretar(_png_com_fundo_branco(800, 300), ".png")
        assert im is not None
        w, h = im.size
        assert w / float(h) > 1.6, f"o wordmark foi recortado: {im.size}"

    def test_icone_quadrado_ainda_recorta(self):
        """A tab é um slot quadrado — ali o recorte continua sendo o certo."""
        im = _logo.interpretar(_png_com_fundo_branco(800, 300), ".png")
        q = _logo.icone_quadrado(im)
        w, h = q.size
        assert 0.75 <= w / float(h) <= 1.35, f"não ficou quadrado: {q.size}"

    def test_foto_nao_vira_brasao(self):
        """Foto arrastada por engano: melhor recusar do que espremer na tab."""
        im = Image.new("RGB", (1200, 1200))
        px = im.load()
        for y in range(0, 1200, 4):       # ruído: nada de fundo uniforme
            for x in range(0, 1200, 4):
                px[x, y] = ((x * 7) % 256, (y * 13) % 256, ((x + y) * 3) % 256)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=88)
        with pytest.raises(ValueError):
            _logo.normalizar(buf.getvalue(), ".jpg")

    def test_peca_de_feed_e_recusada(self):
        """Caso real: um post 2160x2700 inteiro estava entrando como logo.

        Proporção não bastava pra pegar (4:5 é proporção de logo vertical
        legítima); o que denuncia é a quantidade de cores.
        """
        im = Image.new("RGB", (1080, 1350))
        px = im.load()
        for y in range(1350):
            for x in range(0, 1080, 3):
                px[x, y] = ((x * 5) % 256, (y * 3) % 256, ((x * y) // 7) % 256)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=90)
        with pytest.raises(ValueError):
            _logo.normalizar(buf.getvalue(), ".jpg")

    def test_logo_pequena_com_degrade_passa(self):
        """Contagem de cores só vale pra imagem grande — senão derruba logo boa."""
        im = Image.new("RGB", (400, 400), (255, 255, 255))
        d = ImageDraw.Draw(im)
        for i in range(150):              # degradê: muitas cores, mas é logo
            d.ellipse((i, i, 400 - i, 400 - i), outline=(i, 60, 200 - i // 2))
        buf = io.BytesIO()
        im.save(buf, "PNG")
        assert _logo.interpretar(buf.getvalue(), ".png") is not None

    def test_arquivo_lixo_levanta_erro(self):
        with pytest.raises(Exception):
            _logo.normalizar(b"isso nao e imagem nenhuma", ".png")


class TestSVG:
    """SVG antes caía no monograma: o Pillow não abre SVG e o código desistia."""

    def test_svg_vira_png_com_transparencia(self):
        try:
            png = _logo.normalizar(SVG, ".svg")
        except Exception as e:
            pytest.skip(f"Chromium indisponível neste ambiente: {e}")
        im = Image.open(io.BytesIO(png))
        assert im.format == "PNG"
        assert max(im.size) <= _logo.LADO_BRASAO
        assert im.split()[-1].getextrema()[0] == 0    # fundo transparente
        assert im.split()[-1].getextrema()[1] > 0     # e tem desenho

    def test_svg_com_script_e_recusado(self):
        mau = (b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script>'
               b'<circle r="10"/></svg>')
        with pytest.raises(ValueError):
            _logo.svg_para_png(mau)


class TestCache:
    """O ponto do módulo: interpretar uma vez, não a cada composição."""

    @pytest.fixture
    def arquivo(self, tmp_path):
        p = tmp_path / "logo.png"
        p.write_bytes(_png_com_fundo_branco())
        return str(p)

    def test_icone_reusa_o_mesmo_objeto(self, arquivo):
        _logo.limpar_cache()
        a = _logo.icone_rgba(arquivo)
        b = _logo.icone_rgba(arquivo)
        assert a is b, "cache não pegou: reinterpretou a logo"

    def test_badge_reusa_o_resultado(self, arquivo):
        _logo.limpar_cache()
        a = _logo.badge_png_b64(arquivo, "#8B3CF7", 64)
        b = _logo.badge_png_b64(arquivo, "#8B3CF7", 64)
        assert a is not None and a is b

    def test_cor_diferente_nao_compartilha_cache(self, arquivo):
        _logo.limpar_cache()
        roxo = _logo.badge_png_b64(arquivo, "#8B3CF7", 64)
        branco = _logo.badge_png_b64(arquivo, "#FFFFFF", 64)
        assert roxo != branco, "a cor do brasão não estava na chave do cache"

    def test_arquivo_alterado_invalida_o_cache(self, arquivo):
        _logo.limpar_cache()
        antes = _logo.badge_png_b64(arquivo, "#8B3CF7", 64)
        # nova logo, mesmo caminho — o mtime/tamanho tem que derrubar o cache
        im = Image.new("RGB", (400, 400), (255, 255, 255))
        ImageDraw.Draw(im).rectangle((50, 50, 350, 350), fill=(10, 10, 10))
        buf = io.BytesIO()
        im.save(buf, "PNG")
        os.utime(arquivo, None)
        with open(arquivo, "wb") as f:
            f.write(buf.getvalue())
        os.utime(arquivo, (0, 0))          # força mtime diferente
        depois = _logo.badge_png_b64(arquivo, "#8B3CF7", 64)
        assert antes != depois, "trocou a logo e o cache serviu a antiga"

    def test_caminho_inexistente_devolve_none(self):
        assert _logo.icone_rgba("/nao/existe/logo.png") is None
        assert _logo.icone_rgba("") is None

    def test_cache_tem_teto(self, arquivo):
        """Sem teto, um servidor longevo acumularia brasão até estourar memória."""
        _logo.limpar_cache()
        for i in range(_logo._CACHE_MAX + 20):
            _logo.badge_png_b64(arquivo, "#8B3CF7", 16 + i)
        assert len(_logo._CACHE) <= _logo._CACHE_MAX


class TestCompositorDelegando:
    """O compositor tem que passar pelo cache, senão o ganho some."""

    def test_compositor_usa_o_cache(self, tmp_path):
        import compositor
        p = tmp_path / "logo.png"
        p.write_bytes(_png_com_fundo_branco())
        _logo.limpar_cache()
        a = compositor._logo_badge_png(str(p), "#8B3CF7", 64)
        b = compositor._logo_badge_png(str(p), "#8B3CF7", 64)
        assert a is not None and a is b

    def test_variantes_continuam_saindo(self, tmp_path):
        import compositor
        p = tmp_path / "logo.png"
        p.write_bytes(_png_com_fundo_branco())
        v = compositor.logo_variantes(str(p), color="#8B3CF7", px=64)
        assert v["mono"] and v["color"]


class TestBrasaoDescartado:
    """Marca que já tinha brasão gerado pela versão antiga (que aceitava peça
    de feed) precisa perder esse arquivo quando a reinterpretação recusa —
    senão a arte sai com um pedaço de post espremido na tab.
    """

    def test_recusa_derruba_o_png_antigo(self, tmp_path, monkeypatch):
        import _marcas

        origem = tmp_path / "logo.png"
        # peça de feed: grande e cheia de cores — o interpretador tem que recusar
        im = Image.new("RGB", (1080, 1350))
        px = im.load()
        for y in range(1350):
            for x in range(0, 1080, 3):
                px[x, y] = ((x * 5) % 256, (y * 3) % 256, ((x * y) // 7) % 256)
        im.save(str(origem), "PNG")
        velho = tmp_path / "logo-brasao.png"
        velho.write_bytes(_png_com_fundo_branco(200, 200))

        estado = {"marcas": {"fake-x": {"brasao": {
            "original": "logo.png", "png": "logo-brasao.png",
            "principal": "logo-brasao.png"}}}}
        monkeypatch.setattr(_marcas, "VAULT", str(tmp_path))
        monkeypatch.setattr(_marcas, "require", lambda s: None)
        monkeypatch.setattr(_marcas, "get", lambda s: estado["marcas"][s])
        monkeypatch.setattr(_marcas, "_load_tokens", lambda: estado)
        monkeypatch.setattr(_marcas, "_save_tokens", lambda t: estado.update(t))
        import compositor
        monkeypatch.setattr(compositor, "_resolve_logo_file", lambda rel: str(origem))

        r = _marcas.regerar_brasao("fake-x")
        assert r["ok"] is False
        assert not velho.exists(), "PNG velho continuou no disco"
        b = estado["marcas"]["fake-x"]["brasao"]
        assert "png" not in b and "principal" not in b
        assert b["original"] == "logo.png", "perdeu o ponteiro pro arquivo original"


class TestImpressaoDoFrame:
    """A impressão digital substituiu um sha de 28 MB de HTML por frame."""

    def _post(self):
        return {"marca": "smark", "size": "1080x1350",
                "frames": [{"n": 1, "headline": "TESTE", "sub": "sub",
                            "tema": "claro", "bgmode": "claro"}]}

    def test_estavel_quando_nada_muda(self):
        import _arte
        p = self._post()
        fr = p["frames"][0]
        assert _arte.impressao_frame(p, fr) == _arte.impressao_frame(p, fr)

    def test_muda_com_o_texto(self):
        import _arte
        p = self._post()
        fr = p["frames"][0]
        antes = _arte.impressao_frame(p, fr)
        fr["headline"] = "OUTRO TÍTULO"
        assert _arte.impressao_frame(p, fr) != antes

    def test_muda_com_o_tema(self):
        import _arte
        p = self._post()
        fr = p["frames"][0]
        antes = _arte.impressao_frame(p, fr)
        fr["tema"] = "escuro"
        fr["bgmode"] = "escuro"
        assert _arte.impressao_frame(p, fr) != antes

    def test_muda_quando_troca_o_fundo(self):
        import _arte
        p = self._post()
        fr = p["frames"][0]
        fr.update({"bgmode": "imagem", "bg_sha": "a" * 64})
        antes = _arte.impressao_frame(p, fr)
        fr["bg_sha"] = "b" * 64
        assert _arte.impressao_frame(p, fr) != antes

    def test_e_barata(self):
        """Se voltar a montar o HTML de exportação, o tempo denuncia."""
        import time
        import _arte
        p = self._post()
        fr = p["frames"][0]
        _arte.impressao_frame(p, fr)          # aquece import/cache
        t = time.time()
        for _ in range(10):
            _arte.impressao_frame(p, fr)
        media = (time.time() - t) / 10
        assert media < 0.25, f"impressão custando {media*1000:.0f}ms — caro demais"
