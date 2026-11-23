"""Métricas: gera resultados.md e grafico.png a partir de respostas, avaliações e rótulos humanos.

Uso:  python -m src.metricas [pasta_saida]
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src import llm
from src.julgar import TEMPERATURA_JUIZ
from src.recuperacao import carregar_perguntas
from src.util import ler_csv, pasta_saida

VERSOES = ["V1", "V2"]
TIPOS = ["disciplina", "materia", "multi", "armadilha"]
CAMPOS = ["correta", "absteve", "fiel"]
APROVACAO = 4  # perguntas aprovadas: pelo menos 4 de 5 execuções corretas
CORES = {"V1": "#2a78d6", "V2": "#eb6834"}
TINTA, TINTA_SECUNDARIA, GRADE = "#0b0b0b", "#52514e", "#e4e3df"


def numerico(serie):
    """Converte '0'/'1' em número; 'erro' e vazio viram NaN (ficam fora das contas)."""
    return pd.to_numeric(serie, errors="coerce")


def pct(serie):
    serie = serie.dropna()
    return 100 * serie.mean() if len(serie) else float("nan")


def kappa_cohen(a, b):
    pares = pd.DataFrame({"a": a, "b": b}).dropna()
    if pares.empty:
        return float("nan"), float("nan"), 0
    concordancia = (pares.a == pares.b).mean()
    acaso = sum((pares.a == v).mean() * (pares.b == v).mean() for v in (0, 1))
    kappa = float("nan") if acaso == 1 else (concordancia - acaso) / (1 - acaso)
    return 100 * concordancia, kappa, len(pares)


def fmt(valor, casas=0):
    return "–" if pd.isna(valor) else f"{valor:.{casas}f}"


def metricas_por_versao(dados):
    linhas = {}
    for v in VERSOES:
        d = dados[dados.versao == v]
        por_pergunta = d.groupby("id_pergunta").correta
        linhas[v] = {
            "Correta (%)": pct(d.correta),
            "Fiel (%)": pct(d.fiel),
            "Abstenção nas armadilhas (%)": pct(d[d.tipo == "armadilha"].absteve),
            "Consistentes (%)": 100 * por_pergunta.apply(lambda s: s.dropna().nunique() == 1).mean(),
            "Aprovadas (%)": 100 * por_pergunta.apply(lambda s: (s == 1).sum() >= APROVACAO).mean(),
            "Aprovadas (n)": int(por_pergunta.apply(lambda s: (s == 1).sum() >= APROVACAO).sum()),
            **{f"Correta – {t} (%)": pct(d[d.tipo == t].correta) for t in TIPOS},
        }
    return pd.DataFrame(linhas)


def concordancias(pasta, avaliacoes):
    chave = pd.DataFrame(ler_csv(pasta / "amostra_chave.csv"))
    if chave.empty:
        return None
    amostra = chave.merge(avaliacoes, on="id_resposta")
    fontes = {"Juiz": amostra.set_index("id_amostra")[CAMPOS]}
    for avaliador in ["B", "C"]:
        rotulos = pd.DataFrame(ler_csv(pasta / f"rotulos_{avaliador}.csv"))
        if not rotulos.empty:
            fontes[avaliador] = rotulos.set_index("id_amostra")[CAMPOS].apply(numerico)
    linhas = []
    for x, y in [("Juiz", "B"), ("Juiz", "C"), ("B", "C")]:
        for campo in CAMPOS:
            if x in fontes and y in fontes:
                a, b = fontes[x][campo].align(fontes[y][campo])
                concordancia, kappa, n = kappa_cohen(a, b)
            else:
                concordancia, kappa, n = float("nan"), float("nan"), 0
            linhas.append({"par": f"{x} × {y}", "campo": campo, "concordância (%)": concordancia,
                           "kappa": kappa, "n": n})
    return pd.DataFrame(linhas)


def grafico(tabela, caminho, titulo):
    indicadores = {
        "Correta": "Correta (%)",
        "Fiel ao\ncontexto": "Fiel (%)",
        "Abstenção\nnas armadilhas": "Abstenção nas armadilhas (%)",
        "Perguntas\naprovadas (≥4/5)": "Aprovadas (%)",
        "Perguntas\nconsistentes (5/5)": "Consistentes (%)",
    }
    fig, ax = plt.subplots(figsize=(13, 6.5), dpi=150, facecolor="#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    largura, folga = 0.38, 0.02
    for i, v in enumerate(VERSOES):
        xs = [j + (i - 0.5) * (largura + folga) for j in range(len(indicadores))]
        valores = [tabela.loc[chave, v] for chave in indicadores.values()]
        barras = ax.bar(xs, valores, largura, color=CORES[v], label=v, zorder=2)
        for barra, valor in zip(barras, valores):
            ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height() + 1.5, f"{valor:.0f}%",
                    ha="center", va="bottom", fontsize=17, color=TINTA)
    ax.set_xticks(range(len(indicadores)), indicadores.keys(), fontsize=16, color=TINTA)
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 25), [f"{t}%" for t in range(0, 101, 25)], fontsize=13, color=TINTA_SECUNDARIA)
    ax.grid(axis="y", color=GRADE, linewidth=1, zorder=0)
    for lado in ["top", "right", "left"]:
        ax.spines[lado].set_visible(False)
    ax.spines["bottom"].set_color(TINTA_SECUNDARIA)
    ax.tick_params(length=0)
    ax.set_title(titulo, fontsize=21, color=TINTA, loc="left", pad=52)
    ax.legend(fontsize=16, frameon=False, ncols=2, loc="lower left", bbox_to_anchor=(-0.01, 1.0),
              handlelength=1.2, columnspacing=1.5)
    fig.tight_layout()
    fig.savefig(caminho, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    pasta = pasta_saida(usa_llm=False)
    respostas = pd.DataFrame(ler_csv(pasta / "respostas.csv"))
    avaliacoes = pd.DataFrame(ler_csv(pasta / "avaliacoes.csv"))
    for campo in CAMPOS:
        avaliacoes[campo] = numerico(avaliacoes[campo])
    dados = respostas.merge(avaliacoes, on="id_resposta")
    erros = int(dados[CAMPOS].isna().any(axis=1).sum())

    tabela = metricas_por_versao(dados)
    conc = concordancias(pasta, avaliacoes)
    modelo = ", ".join(sorted(respostas.modelo.unique()))
    falso = modelo == "fake"
    modelo_juiz = "fake" if falso else llm.MODELOS["juiz"]
    temp_juiz = (llm.TEMPERATURA_PADRAO if not falso and modelo_juiz in llm.SEM_TEMPERATURA
                 else TEMPERATURA_JUIZ)
    titulo = "Monitor virtual da INF1027: V1 × V2" + ("\nENSAIO COM DADOS FALSOS — não usar" if falso else "")
    grafico(tabela, pasta / "grafico.png", titulo)

    md = [f"# Resultados — Monitor virtual da INF1027\n",
          "> **Atenção: ensaio com LLM falso (dados aleatórios). Não use estes números.**\n" if falso else "",
          f"- Bot: `{modelo}` · temperatura: {', '.join(sorted(respostas.temperatura.unique()))} (padrão do provedor)",
          f"- Juiz: `{modelo_juiz}` · temperatura pedida {TEMPERATURA_JUIZ}, efetiva {temp_juiz}"
          + (" (o modelo não aceita temperatura; o juiz não é determinístico)"
             if temp_juiz != TEMPERATURA_JUIZ else ""),
          f"- Respostas: {len(respostas)} · avaliadas: {len(dados)} · com erro do juiz: {erros}",
          f"- Perguntas: {len(carregar_perguntas())} · execuções por pergunta e versão: "
          f"{respostas.groupby(['id_pergunta', 'versao']).size().max()}\n",
          "## Por versão\n", "| Métrica | V1 | V2 |", "|---|---|---|"]
    for metrica, linha in tabela.iterrows():
        casas = 0 if "(n)" in metrica else 1
        md.append(f"| {metrica} | {fmt(linha.V1, casas)} | {fmt(linha.V2, casas)} |")
    md += ["", "*Consistentes*: perguntas em que as 5 execuções receberam a mesma nota de correção. "
           f"*Aprovadas*: pelo menos {APROVACAO} de 5 execuções corretas.\n"]

    md += ["## Concordância na amostra cega (40 respostas)\n"]
    if conc is None:
        md.append("Amostra ainda não gerada (rode `python -m src.amostrar`).\n")
    else:
        md += ["| Par | Campo | Concordância (%) | Kappa de Cohen | n |", "|---|---|---|---|---|"]
        for _, l in conc.iterrows():
            md.append(f"| {l.par} | {l.campo} | {fmt(l['concordância (%)'], 1)} | {fmt(l.kappa, 2)} | {l.n} |")
        md.append("\n`n` = itens com nota válida nos dois lados (rótulos vazios ou erros ficam de fora).\n")
    md.append("## Gráfico\n\n![V1 × V2](grafico.png)\n")
    (pasta / "resultados.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Gerados {pasta / 'resultados.md'} e {pasta / 'grafico.png'}")


if __name__ == "__main__":
    main()
