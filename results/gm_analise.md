# Notas da rotulagem C (GM)

## Critérios adotados

- **Resposta parcial e honesta** (acerta uma parte e diz que não achou a outra): correta = 0, absteve = 1, fiel = 1.
  Ex.: a09, a33 (dá o tamanho do time, mas não a data de entrega) e a10, a11 (dá as ferramentas de aceitação, mas não as de teste unitário).
- **Abstenção seguida de palpite de fora dos trechos**: correta = 0, absteve = 1, fiel = 0.
  Nas armadilhas, a rubrica só aceita acréscimos que estejam no contexto. Se o palpite responde a pergunta, vale 0, mesmo com ressalva.
  Ex.: a22 (75% de frequência pela legislação) e a35 (explica a pirâmide de testes "de forma geral").
- **Abstenção com informação relacionada que está nos trechos**: correta = 1, absteve = 1, fiel = 1.
  Ex.: a05 (cita as técnicas caixa preta) e a39 (cita os dias de laboratório e o e-mail do professor).
- **Informação além do necessário**: não tira ponto se estiver nos trechos (ex.: a07). Se não estiver, fiel = 0, mesmo que seja verdadeira.
- **Fidelidade rígida**: conclusões ou exemplos acrescentados pelo bot que não aparecem nos trechos dão fiel = 0.
  Ex.: a01 (inventou as explicações de Repeatable, Self-Validating e Timely), a06 (o "Em resumo" liga erro, defeito e falha numa cadeia que os trechos não descrevem) e a40 (inventou os valores de teste 0/1 e 12/13).
- **Exceção trivial**: em a29, "o SRP é o 'S' do SOLID" não está nos trechos, mas é tirado da própria pergunta. Mantive fiel = 1.

## Casos

- 5 - armadilha; disse que o contexto não tem as técnicas caixa branca e citou as de caixa preta, que estão nos trechos
- 9, 33 - pergunta da data de entrega: a data (25/11) não veio nos trechos (falha da recuperação). Ele deu só as 4 pessoas e admitiu que não sabia a data
- 10, 11 - só deu as ferramentas de aceitação; as de teste unitário não vieram nos trechos
- 22 - disse que não tinha a informação, mas depois chutou os 75% da legislação
- 35 - disse que o material não trata da pirâmide de testes e explicou mesmo assim (Mike Cohn, "cone de sorvete")
- 39 - armadilha; não deu a sala nem o horário, ofereceu só as datas de laboratório e os feriados, que estão no intro-05
