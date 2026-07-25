#!/usr/bin/env python3
"""Acervo de peças-referência por família de marca.

Cada arte aprovada e marcada entra aqui e passa a alimentar as gerações
seguintes via input_references. É o ativo que compõe juros: um concorrente
com o mesmo modelo e o mesmo prompt não tem as peças que esta marca aprovou.

Curadoria é obrigatória — só entra o que foi marcado à mão. Teto em max_refs.
Falha de leitura nunca derruba a geração: o arquivo ilegível é ignorado com
aviso em stderr e a lista segue com as peças legíveis."""
import base64
import datetime
import os
import shutil
import sys


def listar(acervo_dir, max_refs=20):
    """PNGs do acervo, mais recentes primeiro, limitados a `max_refs`."""
    if not acervo_dir or not os.path.isdir(acervo_dir):
        return []
    itens = [os.path.join(acervo_dir, n) for n in os.listdir(acervo_dir)
             if n.lower().endswith(".png")]
    itens.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return itens[:max_refs]


def adicionar(png_path, acervo_dir):
    """Copia a peça pro acervo com prefixo de data. Devolve o destino."""
    if not os.path.exists(png_path):
        raise FileNotFoundError(png_path)
    os.makedirs(acervo_dir, exist_ok=True)
    hoje = datetime.date.today().isoformat()
    destino = os.path.join(acervo_dir, f"{hoje}-{os.path.basename(png_path)}")
    shutil.copy2(png_path, destino)
    return destino


def remover(nome, acervo_dir):
    """Remove uma peça do acervo pelo nome do arquivo. True se removeu."""
    if not acervo_dir:
        return False
    alvo = os.path.join(acervo_dir, os.path.basename(nome))
    if os.path.exists(alvo):
        os.remove(alvo)
        return True
    return False


def como_data_urls(paths):
    """Converte caminhos de PNG em data-URLs pro input_references.

    Arquivo ilegível ou ausente é pulado com aviso em stderr — a geração
    continua com as refs que sobraram (ou sem refs)."""
    urls = []
    for p in paths or []:
        try:
            with open(p, "rb") as f:
                urls.append("data:image/png;base64," + base64.b64encode(f.read()).decode())
        except OSError as e:
            print(f"AVISO: acervo ignorou peça ilegível '{p}' ({e})", file=sys.stderr)
    return urls
