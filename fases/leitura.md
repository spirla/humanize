# Leitura integral

Abra o primeiro capítulo pendente. Leia o texto que a ferramenta devolve à conversa. Percorra toda a unidade em partes consecutivas que caibam na saída. Inclua notas, quadros, citações e exercícios. Se a saída vier truncada, repita com um bloco menor. Termine o capítulo antes de abrir o próximo.

No controle local rode `ler`. Leia o bloco exibido, depois chame `confirmar FIM "expressão literal do final"` com a posição que de fato alcançou e uma passagem dos últimos 180 caracteres. Para encurtar o bloco use `ler --limite N`. O mesmo início reaparece enquanto estiver sem confirmação. Peça as partes uma por vez. É vedado encadear essas chamadas num laço automático ou confirmar conteúdo que não entrou no contexto do revisor.

Ao terminar cada capítulo, escolha um trecho literal curto. Descreva, com o vocabulário da obra, a contribuição do capítulo e como uma passagem prepara outra. Verifique início, desenvolvimento e fecho. Numa unidade prática, explique o que o enunciado pede e o que a sequência de informações permite resolver. Guarde observações editoriais, sem expor raciocínio privado. A edição começa em fase posterior.

**Saída.** Para cada unidade, `registrar leitura NUMERO NOTA.json`, com os campos `trecho`, `contribuicao` e `encadeamento`. A nota deve poder ser conferida no texto. Hash, resumo anterior e contagem de palavras identificam o insumo. A leitura requer o conteúdo.
