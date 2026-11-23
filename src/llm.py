"""Camada do LLM: todo o projeto chama apenas gerar(prompt, temperatura, papel=...).

O provedor é escolhido pela variável de ambiente LLM_PROVIDER (pode estar no .env):
  - "fake": respostas falsas e variadas, para ensaiar o pipeline sem modelo nem chave.
  - "openrouter": modelos reais via OpenRouter (chave OPEN_ROUTER_API_KEY no .env).
O papel ("bot" ou "juiz") escolhe o modelo.
"""
import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from src.rubrica import FRASE_NAO_ENCONTREI

MODELOS = {
    "bot": os.environ.get("LLM_MODELO_BOT", "anthropic/claude-haiku-5.5"),
    "juiz": os.environ.get("LLM_MODELO_JUIZ", "anthropic/claude-sonnet-5.5"),
}
# Estes modelos não aceitam temperatura (o OpenRouter a descartaria em silêncio):
# o parâmetro não é enviado e vale o padrão do provedor, 1.0.
SEM_TEMPERATURA = {"anthropic/claude-haiku-5.5", "anthropic/claude-sonnet-5.5"}
TEMPERATURA_PADRAO = 1.0
URL_OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"


class ErroTransitorio(Exception):
    """Falha que vale a pena tentar de novo (limite de taxa, timeout, erro 5xx...)."""


def _carregar_env():
    """Lê o .env (formato CHAVE = valor) sem sobrescrever variáveis já definidas."""
    arquivo = Path(__file__).resolve().parent.parent / ".env"
    if arquivo.exists():
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            if "=" in linha and not linha.lstrip().startswith("#"):
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip().strip("'\""))


_carregar_env()


def provedor():
    nome = os.environ.get("LLM_PROVIDER")
    if not nome:
        raise RuntimeError("Defina LLM_PROVIDER (fake ou openrouter).")
    return nome


def modelo(papel="bot"):
    """Nome do modelo, para registrar junto de cada resposta."""
    return "fake" if provedor() == "fake" else MODELOS[papel]


def temperatura_efetiva(temperatura, papel="bot"):
    """A temperatura que de fato vale na chamada (para registro)."""
    if temperatura is None or (provedor() != "fake" and MODELOS[papel] in SEM_TEMPERATURA):
        return TEMPERATURA_PADRAO
    return temperatura


def gerar(prompt, temperatura, papel="bot", tentativas=6):
    """Gera texto para o prompt. temperatura=None usa o padrão do provedor.

    Tenta de novo, com espera crescente, em falhas transitórias.
    """
    funcao = {"fake": _gerar_fake, "openrouter": _gerar_openrouter}.get(provedor())
    if funcao is None:
        raise RuntimeError(f"Provedor desconhecido: {provedor()}")

    espera = 0.05 if provedor() == "fake" else 2.0
    for tentativa in range(1, tentativas + 1):
        try:
            return funcao(prompt, temperatura, papel)
        except ErroTransitorio as erro:
            if tentativa == tentativas:
                raise
            print(f"  falha transitória ({erro}); nova tentativa em {espera:.1f}s")
            time.sleep(espera)
            espera *= 2


# ----- Provedor OpenRouter --------------------------------------------------

# Custo de cada chamada real (informado pelo OpenRouter) e teto de gasto acumulado.
ARQ_CUSTOS = Path(__file__).resolve().parent.parent / "results" / "custos_openrouter.csv"
LIMITE_CUSTO_USD = float(os.environ.get("LIMITE_CUSTO_USD", "4.0"))


def custo_acumulado():
    if not ARQ_CUSTOS.exists():
        return 0.0
    linhas = ARQ_CUSTOS.read_text(encoding="utf-8").splitlines()[1:]
    return sum(float(l.split(",")[3]) for l in linhas if l)


def _registrar_custo(papel, uso):
    novo = not ARQ_CUSTOS.exists()
    with open(ARQ_CUSTOS, "a", encoding="utf-8") as f:
        if novo:
            f.write("papel,tokens_entrada,tokens_saida,custo_usd\n")
        f.write(f"{papel},{uso.get('prompt_tokens', 0)},{uso.get('completion_tokens', 0)},{uso.get('cost', 0)}\n")


def _gerar_openrouter(prompt, temperatura, papel):
    chave = os.environ.get("OPEN_ROUTER_API_KEY")
    if not chave:
        raise RuntimeError("OPEN_ROUTER_API_KEY não encontrada no .env.")
    if custo_acumulado() >= LIMITE_CUSTO_USD:
        raise RuntimeError(f"Teto de custo atingido: US$ {custo_acumulado():.4f} >= {LIMITE_CUSTO_USD} "
                           "(ajuste LIMITE_CUSTO_USD para continuar).")
    corpo = {"model": MODELOS[papel], "max_tokens": 4000,
             "messages": [{"role": "user", "content": prompt}]}
    if temperatura is not None and MODELOS[papel] not in SEM_TEMPERATURA:
        corpo["temperature"] = temperatura
    requisicao = urllib.request.Request(
        URL_OPENROUTER, data=json.dumps(corpo).encode(),
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(requisicao, timeout=120) as r:
            dados = json.load(r)
    except urllib.error.HTTPError as erro:
        if erro.code in (408, 429) or erro.code >= 500:
            raise ErroTransitorio(f"HTTP {erro.code}")
        raise RuntimeError(f"OpenRouter HTTP {erro.code}: {erro.read().decode()[:300]}")
    except (urllib.error.URLError, TimeoutError) as erro:
        raise ErroTransitorio(f"rede: {erro}")

    if "error" in dados:
        raise ErroTransitorio(f"erro do provedor: {str(dados['error'])[:120]}")
    _registrar_custo(papel, dados.get("usage", {}))
    texto = (dados["choices"][0]["message"].get("content") or "").strip()
    if not texto:
        raise ErroTransitorio(f"resposta vazia (finish_reason={dados['choices'][0].get('finish_reason')})")
    return texto


# ----- Provedor fake --------------------------------------------------------

_INVENCOES = [
    "Segundo a disciplina, isso é coberto pelo critério MC/DC, que exige 100% de cobertura de ramos.",
    "A resposta é 75%, conforme definido no regulamento da disciplina.",
    "Isso é explicado pela pirâmide de testes: muitos testes de unidade e poucos testes de interface.",
    "As aulas acontecem às terças e quintas, das 9h às 11h, na sala L520.",
    "O teste de mutação gera mutantes do programa e o escore é mutantes mortos / mutantes não equivalentes.",
]


def _gerar_fake(prompt, temperatura, papel):
    if random.random() < 0.02:
        raise ErroTransitorio("fake: limite de taxa simulado")
    if '"correta"' in prompt or '"fiel"' in prompt:
        return _juiz_fake(prompt)
    return _bot_fake(prompt)


def _bot_fake(prompt):
    sorteio = random.random()
    trechos = re.findall(r"^\[[^\]]+\] (.+)$", prompt, flags=re.MULTILINE)
    if sorteio < 0.45 and trechos:
        frases = [f for f in re.split(r"(?<=[.:])\s+", random.choice(trechos)) if len(f) > 20]
        return random.choice(frases or trechos)
    if sorteio < 0.75:
        return FRASE_NAO_ENCONTREI
    return random.choice(_INVENCOES)


def _juiz_fake(prompt):
    if '"fiel"' in prompt:
        nota = {"justificativa": "fake: avaliação aleatória de fidelidade.", "fiel": random.randint(0, 1)}
    else:
        nota = {
            "justificativa": "fake: avaliação aleatória de correção.",
            "correta": random.randint(0, 1),
            "absteve": random.randint(0, 1),
        }
    return json.dumps(nota, ensure_ascii=False)
