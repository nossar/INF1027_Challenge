# Monitor virtual da INF1027 — experimento de medição

Chatbot RAG sobre os documentos da disciplina (`data/chunks.jsonl`), em duas versões de prompt (V1 e V2).
O objetivo é **medir** o bot: correção, fidelidade aos trechos, abstenção, consistência e concordância juiz × humanos.

## Preparação

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

O provedor do LLM é escolhido por `LLM_PROVIDER`:
- `openrouter`: bot = `anthropic/claude-haiku-5.5`, juiz = `anthropic/claude-sonnet-5.5`. A chave fica no `.env`
  (`OPEN_ROUTER_API_KEY = ...`, nunca versionado). Cada chamada tem o custo registrado em `results/custos_openrouter.csv`,
  e a execução para se o gasto acumulado passar de `LIMITE_CUSTO_USD` (padrão: US$ 4).
- `fake`: respostas aleatórias, para ensaiar o pipeline sem gastar.

Temperatura: o bot usa o padrão do provedor (1.0). O juiz pede 0, mas o Sonnet 5.5 não aceita o parâmetro,
então na prática também roda a 1.0 (fica registrado no `resultados.md`).

## Para os avaliadores (B e C)

1. Abra **só** o seu arquivo (`results/rotulos_B.csv` ou `results/rotulos_C.csv`) e `results/rubrica_humanos.md`.
2. **Não abra** `amostra_chave.csv`, `avaliacoes.csv` nem `respostas.csv`: eles revelam a versão e a nota do juiz e quebram a avaliação cega.
3. Preencha `correta`, `absteve` e `fiel` com `0` ou `1` em todas as 40 linhas, sozinho, sem conversar com o outro avaliador.
4. Pode ordenar e filtrar, mas não altere a coluna `id_amostra`. Salve em CSV (UTF-8, separado por vírgula) com o mesmo nome e faça commit.

## Pipeline

Todos os scripts recebem a pasta de saída como argumento (padrão: `results/`), gravam linha a linha e retomam de onde pararam.

| Passo | Comando | Saída |
|---|---|---|
| 0. Conferir a recuperação | `python -m src.recuperacao` | tabela no terminal |
| 1. Gerar 200 respostas | `LLM_PROVIDER=openrouter python -m src.executar results` | `respostas.csv` |
| 2. Juiz LLM (A e B) | `LLM_PROVIDER=openrouter python -m src.julgar results` | `avaliacoes.csv` |
| 3. Amostra cega (40) | `python -m src.amostrar results` | `rotulos_B.csv`, `rotulos_C.csv`, `amostra_chave.csv`, `rubrica_humanos.md` |
| 4. Rotulagem humana | B e C preenchem `correta`, `absteve`, `fiel` (0/1) seguindo `rubrica_humanos.md` | |
| 5. Métricas | `python -m src.metricas results` | `resultados.md`, `grafico.png` |

Os passos 1 e 2 precisam de `LLM_PROVIDER` definido. Para testar uma pergunta: `python -m src.bot V2 Em que data é a P1?`

## Ensaio com dados falsos

Com `LLM_PROVIDER=fake`, os scripts só aceitam gravar em `results/fake/` (ignorada pelo git).

```bash
export LLM_PROVIDER=fake
python -m src.executar results/fake
python -m src.julgar results/fake
python -m src.amostrar results/fake
python -m src.rotulos_fake results/fake   # preenche B e C com notas aleatórias
python -m src.metricas results/fake
```

## Arquivos

- `data/perguntas.csv` — gabarito: 20 perguntas (6 disciplina, 6 matéria, 4 multi-chunk, 4 armadilhas "NÃO CONSTA").
- `data/embeddings.npy` + `embeddings.hash` — embeddings dos chunks; regerados só se `chunks.jsonl` mudar.
- `src/rubrica.py` — critérios `correta`, `absteve`, `fiel`, usados pelo juiz e pelos humanos.
