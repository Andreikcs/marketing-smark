import base64
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import _acervo  # noqa: E402


def _png(p, conteudo=b"\x89PNG-fake"):
    open(p, "wb").write(conteudo)
    return p


def test_listar_devolve_mais_recentes_primeiro(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    a = _png(str(d / "2026-01-01-a.png"))
    time.sleep(0.01)
    b = _png(str(d / "2026-01-02-b.png"))
    assert _acervo.listar(str(d)) == [b, a]


def test_listar_respeita_o_teto(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    for i in range(5):
        _png(str(d / f"p{i}.png"))
        time.sleep(0.01)
    assert len(_acervo.listar(str(d), max_refs=3)) == 3


def test_listar_diretorio_inexistente_devolve_vazio(tmp_path):
    assert _acervo.listar(str(tmp_path / "nao-existe")) == []


def test_listar_ignora_nao_png(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    _png(str(d / "ok.png"))
    open(str(d / "leia.md"), "w").write("x")
    assert len(_acervo.listar(str(d))) == 1


def test_adicionar_copia_com_prefixo_de_data(tmp_path):
    origem = _png(str(tmp_path / "arte.png"))
    d = str(tmp_path / "acervo")
    destino = _acervo.adicionar(origem, d)
    assert os.path.exists(destino)
    assert os.path.basename(destino).endswith("-arte.png")
    assert len(_acervo.listar(d)) == 1


def test_remover(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    _png(str(d / "x.png"))
    assert _acervo.remover("x.png", str(d)) is True
    assert _acervo.remover("x.png", str(d)) is False


def test_como_data_urls(tmp_path):
    p = _png(str(tmp_path / "a.png"), b"abc")
    urls = _acervo.como_data_urls([p])
    assert urls[0] == "data:image/png;base64," + base64.b64encode(b"abc").decode()


# --- Robustez: falha ligada ao acervo nunca pode derrubar a geração. ---
# O brief não cobre estes casos; foram adicionados porque o requisito da
# task (lição acumulada) exige que dir ausente/vazio/ilegível/corrompido
# nunca aborte — só reduz para "sem referências" com aviso em stderr.

def test_como_data_urls_ignora_arquivo_ilegivel(tmp_path, capsys):
    boa = _png(str(tmp_path / "boa.png"), b"boa-conteudo")
    ilegivel = _png(str(tmp_path / "ilegivel.png"), b"conteudo-secreto")
    os.chmod(ilegivel, 0o000)
    try:
        if os.access(ilegivel, os.R_OK):
            # rodando como root ou FS que ignora chmod: não dá pra simular
            # o cenário nesta máquina — pula a asserção de skip.
            return
        urls = _acervo.como_data_urls([boa, ilegivel])
        assert len(urls) == 1
        assert urls[0] == "data:image/png;base64," + base64.b64encode(b"boa-conteudo").decode()
        assert "ilegível" in capsys.readouterr().err
    finally:
        os.chmod(ilegivel, 0o644)


def test_listar_diretorio_com_arquivo_corrompido_nao_quebra(tmp_path):
    d = tmp_path / "acervo"
    d.mkdir()
    # "corrompido" = qualquer coteúdo de bytes; listar só filtra por extensão,
    # nunca abre o arquivo — então isto sempre deve funcionar.
    _png(str(d / "corrompido.png"), b"\x00\x01lixo-binario-invalido")
    assert len(_acervo.listar(str(d))) == 1


def test_adicionar_com_diretorio_de_acervo_inexistente_cria(tmp_path):
    origem = _png(str(tmp_path / "arte.png"))
    d = str(tmp_path / "nao-existe-ainda" / "acervo")
    destino = _acervo.adicionar(origem, d)
    assert os.path.exists(destino)
