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


def test_roi_rotas_e_ui():
    srv = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "editor_server.py"),
               encoding="utf-8").read()
    assert '"/roi-start"' in srv
    assert '"/roi-resumo"' in srv
    assert "_roi.touch_image" in srv or "_roi.touch_copy" in srv
    ui = open(os.path.join(os.path.dirname(__file__), "..", "scripts", "_editor2.html"),
              encoding="utf-8").read()
    assert "roipanel" in ui
    assert "/roi-resumo" in ui
