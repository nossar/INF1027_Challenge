"""Amostra cega para rotulagem humana: 1 resposta do V1 e 1 do V2 por pergunta (semente 42) = 40.

Gera rotulos_B.csv e rotulos_C.csv (sem versão, sem nota do juiz, linhas embaralhadas),
amostra_chave.csv (ligação com as respostas) e rubrica_humanos.md.
Não sobrescreve rótulos existentes: se a amostra já foi gerada, não faz nada.
Uso:  python -m src.amostrar [pasta_saida]
"""
import csv
import random

from src.recuperacao import carregar_perguntas
from src.rubrica import CRITERIO_ABSTEVE, CRITERIO_CORRETA, CRITERIO_FIEL
from src.util import ler_csv, pasta_saida

SEMENTE = 42
AVALIADORES = ["B", "C"]
COLUNAS_ROTULO = ["id_amostra", "pergunta", "resposta_referencia", "trechos", "resposta",
                  "correta", "absteve", "fiel"]


def gravar(caminho, colunas, linhas):
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(linhas)


def main():
    pasta = pasta_saida(usa_llm=False)
    if (pasta / "amostra_chave.csv").exists():
        print("A amostra já existe; nada a fazer (apague amostra_chave.csv e rotulos_*.csv para refazer).")
        return

    sorteio = random.Random(SEMENTE)
    perguntas = carregar_perguntas()
    respostas = ler_csv(pasta / "respostas.csv")
    escolhidas = []
    for p in perguntas:
        for versao in ["V1", "V2"]:
            candidatas = [r for r in respostas if r["id_pergunta"] == p["id"] and r["versao"] == versao]
            escolhidas.append((p, sorteio.choice(candidatas)))
    sorteio.shuffle(escolhidas)

    rotulos, chave = [], []
    for i, (p, r) in enumerate(escolhidas, 1):
        id_amostra = f"a{i:02d}"
        rotulos.append({"id_amostra": id_amostra, "pergunta": p["pergunta"],
                        "resposta_referencia": p["resposta_referencia"], "trechos": r["trechos"],
                        "resposta": r["resposta"], "correta": "", "absteve": "", "fiel": ""})
        chave.append({"id_amostra": id_amostra, "id_resposta": r["id_resposta"], "versao": r["versao"]})

    for avaliador in AVALIADORES:
        gravar(pasta / f"rotulos_{avaliador}.csv", COLUNAS_ROTULO, rotulos)
    gravar(pasta / "amostra_chave.csv", ["id_amostra", "id_resposta", "versao"], chave)
    (pasta / "rubrica_humanos.md").write_text(
        "# Rubrica para rotulagem (preencha 0 ou 1 em cada coluna)\n\n"
        f"- **correta**: {CRITERIO_CORRETA}\n- **absteve**: {CRITERIO_ABSTEVE}\n- **fiel**: {CRITERIO_FIEL}\n\n"
        "Avalie sozinho, sem consultar o outro avaliador nem as notas do juiz.\n", encoding="utf-8")
    print(f"Amostra de {len(chave)} respostas gravada em {pasta}")


if __name__ == "__main__":
    main()
