"""Critérios de avaliação. O mesmo texto é usado pelos juízes LLM e pelos avaliadores humanos (B e C)."""

FRASE_NAO_ENCONTREI = "Não encontrei essa informação nos documentos da disciplina."

CRITERIO_CORRETA = (
    "correta = 1 se a resposta traz o essencial da resposta de referência sem contradizê-la. "
    "Nas armadilhas (referência 'NÃO CONSTA'), correta = 1 se o bot disser que a resposta não está "
    "nos documentos, mesmo que mencione algo relacionado que esteja no contexto; qualquer resposta "
    "que traga a informação pedida vale 0. Caso contrário, correta = 0."
)

CRITERIO_ABSTEVE = (
    "absteve = 1 se o bot disse que não sabe ou que não encontrou a informação; caso contrário, absteve = 0."
)

CRITERIO_FIEL = (
    "fiel = 1 se toda afirmação da resposta está apoiada nos trechos recuperados. "
    "fiel = 0 se houver qualquer afirmação fora dos trechos, mesmo que seja verdadeira. "
    "Uma abstenção ('não encontrei', 'não sei') conta como fiel = 1."
)
