"""Utilitários comuns aos scripts do experimento."""
import csv
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_FAKE = (RAIZ / "results" / "fake").resolve()


def pasta_saida(usa_llm=True):
    """Pasta de saída: 1º argumento da linha de comando (padrão: results/).

    Proteção: com LLM_PROVIDER=fake, só é permitido gravar dentro de results/fake/.
    """
    pasta = Path(sys.argv[1] if len(sys.argv) > 1 else RAIZ / "results").resolve()
    eh_fake = pasta == PASTA_FAKE or PASTA_FAKE in pasta.parents
    if usa_llm and os.environ.get("LLM_PROVIDER") == "fake" and not eh_fake:
        sys.exit(f"Com LLM_PROVIDER=fake a saída deve ficar em results/fake/, não em {pasta}.")
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def ler_csv(caminho):
    if not Path(caminho).exists():
        return []
    with open(caminho, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class GravadorCSV:
    """Acrescenta linhas a um CSV, gravando cada uma em disco na hora (permite retomar)."""

    def __init__(self, caminho, colunas):
        novo = not Path(caminho).exists() or Path(caminho).stat().st_size == 0
        self.arquivo = open(caminho, "a", encoding="utf-8", newline="")
        self.escritor = csv.DictWriter(self.arquivo, fieldnames=colunas)
        if novo:
            self.escritor.writeheader()

    def gravar(self, linha):
        self.escritor.writerow(linha)
        self.arquivo.flush()
        os.fsync(self.arquivo.fileno())

    def fechar(self):
        self.arquivo.close()
