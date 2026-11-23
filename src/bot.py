"""Monitor virtual da INF1027: duas versões que diferem só no prompt."""
from src.llm import gerar, modelo, temperatura_efetiva
from src.recuperacao import recuperar

INSTRUCOES = {
    "V1": "Você é o monitor virtual da INF1027. Responda à pergunta do aluno usando o contexto abaixo.",
    "V2": (
        "Você é o monitor virtual da INF1027. Responda à pergunta do aluno SOMENTE com base no contexto "
        "abaixo. Se a resposta não estiver nele, responda exatamente: 'Não encontrei essa informação nos "
        "documentos da disciplina.' Não use conhecimento próprio."
    ),
}

# O bot usa a temperatura padrão do provedor (None = não enviar o parâmetro).
TEMPERATURA_BOT = None


def formatar_trechos(chunks):
    return "\n".join(f"[{c['id']}] {c['texto']}" for c in chunks)


def montar_prompt(pergunta, trechos, versao):
    return f"{INSTRUCOES[versao]}\n\nContexto:\n{trechos}\n\nPergunta do aluno: {pergunta}\n\nResposta:"


def responder(pergunta, versao):
    chunks = recuperar(pergunta, k=4)
    trechos = formatar_trechos(chunks)
    resposta = gerar(montar_prompt(pergunta, trechos, versao), TEMPERATURA_BOT, papel="bot")
    return {
        "resposta": resposta.strip(),
        "ids_trechos": ";".join(c["id"] for c in chunks),
        "trechos": trechos,
        "modelo": modelo("bot"),
        "temperatura": temperatura_efetiva(TEMPERATURA_BOT, "bot"),
    }


if __name__ == "__main__":
    import sys
    pergunta = " ".join(sys.argv[2:]) or "Em que data é a P1?"
    versao = sys.argv[1] if len(sys.argv) > 1 else "V2"
    r = responder(pergunta, versao)
    print(f"[{versao}] {r['resposta']}\n(trechos: {r['ids_trechos']}; modelo: {r['modelo']}; T={r['temperatura']})")
