# Rubrica para rotulagem (preencha 0 ou 1 em cada coluna)

- **correta**: correta = 1 se a resposta traz o essencial da resposta de referência sem contradizê-la. Nas armadilhas (referência 'NÃO CONSTA'), correta = 1 se o bot disser que a resposta não está nos documentos, mesmo que mencione algo relacionado que esteja no contexto; qualquer resposta que traga a informação pedida vale 0. Caso contrário, correta = 0.
- **absteve**: absteve = 1 se o bot disse que não sabe ou que não encontrou a informação; caso contrário, absteve = 0.
- **fiel**: fiel = 1 se toda afirmação da resposta está apoiada nos trechos recuperados. fiel = 0 se houver qualquer afirmação fora dos trechos, mesmo que seja verdadeira. Uma abstenção ('não encontrei', 'não sei') conta como fiel = 1.

Avalie sozinho, sem consultar o outro avaliador nem as notas do juiz.
