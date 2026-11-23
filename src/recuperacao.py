"""Recuperação: embeddings locais + similaridade de cosseno.

Uso:  python -m src.recuperacao      (verifica se o chunk_fonte está entre os 4 recuperados)
"""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

PASTA_DADOS = Path(__file__).resolve().parent.parent / "data"
ARQ_CHUNKS = PASTA_DADOS / "chunks.jsonl"
ARQ_PERGUNTAS = PASTA_DADOS / "perguntas.csv"
ARQ_EMBEDDINGS = PASTA_DADOS / "embeddings.npy"
ARQ_HASH = PASTA_DADOS / "embeddings.hash"  # assinatura dos chunks usados no .npy
MODELO_EMBEDDING = "paraphrase-multilingual-MiniLM-L12-v2"

_modelo = None
_chunks = None
_matriz = None


def carregar_chunks():
    with open(ARQ_CHUNKS, encoding="utf-8") as f:
        return [json.loads(linha) for linha in f if linha.strip()]


def carregar_perguntas():
    with open(ARQ_PERGUNTAS, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _modelo_embedding():
    global _modelo
    if _modelo is None:
        from sentence_transformers import SentenceTransformer
        _modelo = SentenceTransformer(MODELO_EMBEDDING)
    return _modelo


def _embutir(textos):
    # normalize_embeddings=True -> produto interno = similaridade de cosseno
    return _modelo_embedding().encode(textos, normalize_embeddings=True)


def _assinatura():
    conteudo = ARQ_CHUNKS.read_bytes() + MODELO_EMBEDDING.encode()
    return hashlib.sha256(conteudo).hexdigest()


def _indice():
    """Devolve (chunks, matriz de embeddings), reaproveitando o .npy se os chunks não mudaram."""
    global _chunks, _matriz
    if _matriz is None:
        _chunks = carregar_chunks()
        assinatura = _assinatura()
        if ARQ_EMBEDDINGS.exists() and ARQ_HASH.exists() and ARQ_HASH.read_text().strip() == assinatura:
            _matriz = np.load(ARQ_EMBEDDINGS)
        else:
            print("Gerando embeddings dos chunks...")
            _matriz = _embutir([c["texto"] for c in _chunks])
            np.save(ARQ_EMBEDDINGS, _matriz)
            ARQ_HASH.write_text(assinatura)
    return _chunks, _matriz


def recuperar(pergunta, k=4):
    """Devolve os k chunks mais similares à pergunta, cada um com a chave 'score'."""
    chunks, matriz = _indice()
    similaridades = matriz @ _embutir([pergunta])[0]
    melhores = np.argsort(-similaridades)[:k]
    return [{**chunks[i], "score": float(similaridades[i])} for i in melhores]


def verificar(k=4):
    """Para cada pergunta que não é armadilha, o chunk_fonte está entre os k recuperados?"""
    linhas = []
    for p in carregar_perguntas():
        if p["tipo"] == "armadilha":
            continue
        fontes = p["chunk_fonte"].split(";")
        ids = [c["id"] for c in recuperar(p["pergunta"], k)]
        achados = [f for f in fontes if f in ids]
        linhas.append({
            "id": p["id"], "tipo": p["tipo"], "fonte": p["chunk_fonte"],
            "recuperados": ", ".join(ids),
            "resultado": f"{len(achados)}/{len(fontes)}",
            "posicoes": ", ".join(str(ids.index(f) + 1) if f in ids else "-" for f in fontes),
        })
    return linhas


if __name__ == "__main__":
    linhas = verificar()
    cab = f"| id | tipo | chunk_fonte | achou | posição | top-4 recuperados |\n|---|---|---|---|---|---|"
    corpo = "\n".join(
        f"| {l['id']} | {l['tipo']} | {l['fonte']} | {l['resultado']} | {l['posicoes']} | {l['recuperados']} |"
        for l in linhas
    )
    completas = sum(l["resultado"].split("/")[0] == l["resultado"].split("/")[1] for l in linhas)
    resumo = f"\nFonte completa no top-4: {completas}/{len(linhas)} perguntas."
    print(cab + "\n" + corpo + resumo)
