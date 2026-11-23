"""Execução: 20 perguntas × 5 execuções × 2 versões = 200 respostas em respostas.csv.

Uso:  LLM_PROVIDER=... python -m src.executar [pasta_saida]
Retoma de onde parou: respostas já gravadas não são refeitas.
"""
from src.bot import responder
from src.recuperacao import carregar_perguntas
from src.util import GravadorCSV, ler_csv, pasta_saida

EXECUCOES = 5
VERSOES = ["V1", "V2"]
COLUNAS = ["id_resposta", "id_pergunta", "tipo", "versao", "execucao", "pergunta",
           "resposta", "ids_trechos", "trechos", "modelo", "temperatura"]


def main():
    arquivo = pasta_saida() / "respostas.csv"
    feitas = {l["id_resposta"] for l in ler_csv(arquivo)}
    perguntas = carregar_perguntas()
    total = EXECUCOES * len(VERSOES) * len(perguntas)
    print(f"{len(feitas)}/{total} respostas já existem em {arquivo}")

    gravador = GravadorCSV(arquivo, COLUNAS)
    for execucao in range(1, EXECUCOES + 1):
        for versao in VERSOES:
            for p in perguntas:
                id_resposta = f"{p['id']}_{versao}_e{execucao}"
                if id_resposta in feitas:
                    continue
                r = responder(p["pergunta"], versao)
                gravador.gravar({"id_resposta": id_resposta, "id_pergunta": p["id"], "tipo": p["tipo"],
                                 "versao": versao, "execucao": execucao, "pergunta": p["pergunta"], **r})
                feitas.add(id_resposta)
                print(f"[{len(feitas)}/{total}] {id_resposta}")
    gravador.fechar()


if __name__ == "__main__":
    main()
