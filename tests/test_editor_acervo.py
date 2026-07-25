import os


def test_rota_acervo_add_existe():
    fonte = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "editor_server.py"),
                 encoding="utf-8").read()
    assert '"/acervo-add"' in fonte
    assert "_acervo.adicionar" in fonte


def test_botao_no_editor():
    fonte = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "_editor2.html"),
                 encoding="utf-8").read()
    assert "/acervo-add" in fonte
