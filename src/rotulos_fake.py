"""Só para o ensaio: preenche rotulos_B.csv e rotulos_C.csv com notas aleatórias.

Uso:  python -m src.rotulos_fake results/fake      (recusa qualquer pasta fora de results/fake/)
"""
import csv
import random
import sys
from pathlib import Path

from src.util import PASTA_FAKE, ler_csv


def main():
    pasta = Path(sys.argv[1] if len(sys.argv) > 1 else PASTA_FAKE).resolve()
    if pasta != PASTA_FAKE and PASTA_FAKE not in pasta.parents:
        sys.exit("Rótulos falsos só podem ser gravados em results/fake/.")
    sorteio = random.Random(7)
    for avaliador in ["B", "C"]:
        caminho = pasta / f"rotulos_{avaliador}.csv"
        linhas = ler_csv(caminho)
        for linha in linhas:
            for campo in ["correta", "absteve", "fiel"]:
                linha[campo] = sorteio.randint(0, 1)
        with open(caminho, "w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=linhas[0].keys())
            escritor.writeheader()
            escritor.writerows(linhas)
        print(f"{caminho}: {len(linhas)} linhas preenchidas com notas aleatórias")


if __name__ == "__main__":
    main()
