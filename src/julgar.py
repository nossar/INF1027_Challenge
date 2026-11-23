"""Juiz LLM: duas chamadas por resposta (temperatura 0), gravadas em avaliacoes.csv.

Juiz A (vê o gabarito): correta, absteve.   Juiz B (NÃO vê o gabarito): fiel.
Uso:  LLM_PROVIDER=... python -m src.julgar [pasta_saida]
"""
import json
import re

from src.llm import gerar
from src.recuperacao import carregar_perguntas
from src.rubrica import CRITERIO_ABSTEVE, CRITERIO_CORRETA, CRITERIO_FIEL
from src.util import GravadorCSV, ler_csv, pasta_saida

TENTATIVAS_JSON = 3
# Pedida: 0. O Sonnet 5.5 não aceita temperatura, então na prática vale o padrão (ver llm.temperatura_efetiva).
TEMPERATURA_JUIZ = 0
COLUNAS = ["id_resposta", "correta", "absteve", "justificativa_a", "fiel", "justificativa_b"]

PROMPT_JUIZ_A = """Você avalia respostas de um chatbot de monitoria da disciplina INF1027.

Pergunta do aluno: {pergunta}
Resposta de referência: {referencia}
Resposta do chatbot: {resposta}

Critérios:
- {criterio_correta}
- {criterio_absteve}

Responda apenas com um JSON, com a justificativa antes das notas:
{{"justificativa": "<uma ou duas frases>", "correta": 0 ou 1, "absteve": 0 ou 1}}"""

PROMPT_JUIZ_B = """Você verifica se a resposta de um chatbot está apoiada nos trechos que ele recebeu.

Pergunta do aluno: {pergunta}
Trechos recuperados:
{trechos}

Resposta do chatbot: {resposta}

Critério:
- {criterio_fiel}

Responda apenas com um JSON, com a justificativa antes da nota:
{{"justificativa": "<uma ou duas frases>", "fiel": 0 ou 1}}"""


def extrair_json(texto, campos):
    """Devolve o dict se o texto tiver um JSON com os campos pedidos valendo 0 ou 1; senão None."""
    achado = re.search(r"\{.*\}", texto, flags=re.DOTALL)
    if not achado:
        return None
    try:
        dados = json.loads(achado.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(dados, dict) or "justificativa" not in dados:
        return None
    if any(dados.get(c) not in (0, 1) for c in campos):
        return None
    return dados


def julgar(prompt, campos):
    for _ in range(TENTATIVAS_JSON):
        dados = extrair_json(gerar(prompt, TEMPERATURA_JUIZ, papel="juiz"), campos)
        if dados is not None:
            return dados
    return {"justificativa": f"JSON inválido após {TENTATIVAS_JSON} tentativas", **{c: "erro" for c in campos}}


def main():
    pasta = pasta_saida()
    referencias = {p["id"]: p["resposta_referencia"] for p in carregar_perguntas()}
    respostas = ler_csv(pasta / "respostas.csv")
    arquivo = pasta / "avaliacoes.csv"
    feitas = {l["id_resposta"] for l in ler_csv(arquivo)}
    print(f"{len(feitas)}/{len(respostas)} respostas já avaliadas")

    gravador = GravadorCSV(arquivo, COLUNAS)
    for r in respostas:
        if r["id_resposta"] in feitas:
            continue
        a = julgar(PROMPT_JUIZ_A.format(pergunta=r["pergunta"], referencia=referencias[r["id_pergunta"]],
                                        resposta=r["resposta"], criterio_correta=CRITERIO_CORRETA,
                                        criterio_absteve=CRITERIO_ABSTEVE), ["correta", "absteve"])
        b = julgar(PROMPT_JUIZ_B.format(pergunta=r["pergunta"], trechos=r["trechos"],
                                        resposta=r["resposta"], criterio_fiel=CRITERIO_FIEL), ["fiel"])
        gravador.gravar({"id_resposta": r["id_resposta"], "correta": a["correta"], "absteve": a["absteve"],
                         "justificativa_a": a["justificativa"], "fiel": b["fiel"],
                         "justificativa_b": b["justificativa"]})
        feitas.add(r["id_resposta"])
        print(f"[{len(feitas)}/{len(respostas)}] {r['id_resposta']}")
    gravador.fechar()


if __name__ == "__main__":
    main()
