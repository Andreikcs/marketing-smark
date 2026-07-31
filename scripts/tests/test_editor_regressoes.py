#!/usr/bin/env python3
"""Regressões da interface do Super Editor (`scripts/_editor2.html`).

O arquivo é servido verbatim (`editor_server.py:3055`), sem substituição de
template, então dá pra inspecionar CSS e JS direto como texto. Cada teste aqui
existe por causa de um defeito que chegou ao usuário — não são testes de estilo.

Rodar: python3 scripts/tests/test_editor_regressoes.py
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
UI = os.path.join(SCRIPTS, "_editor2.html")


def _html():
    with open(UI, encoding="utf-8") as f:
        return f.read()


def _regras_display(html, classe):
    """Toda regra CSS que declara `display` para um seletor citando `classe`.

    Devolve [(seletor, valor, importante)]. Aproximação de propósito generosa:
    inclui seletor que só *poderia* casar. Pra um guarda-corpo, incluir demais é
    o lado seguro do erro.
    """
    achados = []
    for sel, corpo in re.findall(r"([^{}]+)\{([^{}]*)\}", html):
        sel = sel.strip()
        if classe not in sel:
            continue
        m = re.search(r"(?:^|;)\s*display\s*:\s*([^;!]+?)\s*(!important)?\s*(?:;|$)", corpo)
        if not m:
            continue
        achados.append((sel, m.group(1).strip(), bool(m.group(2))))
    return achados


class TestEstudioMinimiza(unittest.TestCase):
    """Minimizar parou de funcionar e prendeu o usuário na tela.

    A causa foi disputa de especificidade: `#estudio.min .eslog{display:none}`
    vale (1,2,0) e `#estudio:has(.eslog .esmsg) .eslog{display:flex}` vale
    (1,3,0) — então bastava UMA mensagem no chat pra segunda vencer. Com o log
    visível e `#estudio.min{height:auto}`, o painel crescia até caber a conversa
    inteira; ancorado em `bottom:16px`, o cabeçalho com fechar/minimizar saía
    pela parte de cima da tela.

    Especificidade não é coisa que se confira de olho a cada mexida no CSS, e o
    `:has()` foi adicionado meses depois. Daí a trava ser mecânica.
    """

    @classmethod
    def setUpClass(cls):
        cls.html = _html()

    def test_min_esconde_e_ninguem_reverte(self):
        for classe in (".eslog", ".esfoot", ".eswelcome"):
            regras = _regras_display(self.html, classe)
            minimo = [r for r in regras if "#estudio.min" in r[0]]
            self.assertTrue(minimo, f"sumiu a regra de minimizar para {classe}")
            for sel, valor, importante in minimo:
                self.assertEqual(valor, "none", f"{sel} deveria esconder {classe}")
                self.assertTrue(
                    importante,
                    f"{sel} precisa de !important — sem ele, qualquer regra com "
                    f":has() vence e o painel volta a crescer sem parar",
                )
            # e ninguém mais pode usar !important pra reabrir o que o .min fechou
            for sel, valor, importante in regras:
                if "#estudio.min" in sel:
                    continue
                self.assertFalse(
                    importante and valor != "none",
                    f"{sel} usa !important e reabre {classe} por cima do minimizar",
                )

    def test_min_tem_teto_de_altura(self):
        """Segunda trava, independente de `display`.

        Mesmo que alguém volte a exibir o log no estado minimizado, o painel não
        pode crescer — senão o cabeçalho sai da tela de novo.
        """
        m = re.search(r"#estudio\.min\{([^}]*)\}", self.html)
        self.assertIsNotNone(m, "regra #estudio.min desapareceu")
        corpo = m.group(1)
        alt = re.search(r"max-height:\s*(\d+)px", corpo)
        self.assertIsNotNone(alt, "#estudio.min sem max-height — pode crescer sem limite")
        self.assertLessEqual(int(alt.group(1)), 140,
                             "max-height alto demais: já não é 'minimizado'")
        self.assertIn("overflow:hidden", corpo.replace(" ", ""),
                      "sem overflow:hidden o conteúdo vaza do teto de altura")

    def test_painel_cabe_na_janela(self):
        """O painel aberto nunca pode passar da altura do viewport."""
        m = re.search(r"#estudio\{([^}]*)\}", self.html)
        self.assertIsNotNone(m)
        corpo = m.group(1).replace(" ", "")
        self.assertIn("max-height:calc(100vh-32px)", corpo,
                      "#estudio precisa de teto relativo à janela")
        self.assertIn("bottom:16px", corpo)

    def test_cabecalho_e_composer_nao_encolhem(self):
        """Quem cede espaço quando a conversa cresce é o log, não os controles."""
        for classe in (".eshead", ".esfoot"):
            m = re.search(re.escape(classe) + r"\{([^}]*)\}", self.html)
            self.assertIsNotNone(m, f"regra {classe} não encontrada")
            self.assertIn("flex:0 0 auto", m.group(1),
                          f"{classe} sem flex:0 0 auto — pode ser espremido e "
                          f"levar os botões junto")
        m = re.search(r"\.eslog\{([^}]*)\}", self.html)
        corpo = m.group(1).replace(" ", "")
        self.assertIn("flex:1", corpo)
        self.assertIn("min-height:0", corpo, ".eslog sem min-height:0 não encolhe no flex")

    def test_botoes_de_fechar_e_minimizar_existem(self):
        self.assertIn("id=esmin", self.html)
        self.assertIn("id=esclose", self.html)
        # o clique no botão não pode borbulhar pro cabeçalho, que reabre o painel
        self.assertIn("stopPropagation", self.html)


if __name__ == "__main__":
    unittest.main()
