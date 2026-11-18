# Conferência de fidelidade e progressão local

Releia o candidato gravado por inteiro, em ordem, usando `ler` e `confirmar`. Abra o original e o diff. Confira o alcance das afirmações, exceções, negações, citações, autoridades, números, comandos e termos protegidos. Confira exercícios e aparatos pelas regras do gênero. Compare também os trechos mantidos: uma boa alteração pode introduzir uma repetição com o parágrafo vizinho.

Aplique os testes de conferência do SKILL.md. Releia as aberturas e depois os fechos em sequência. Nos pontos editados, julgue a naturalidade da passagem inteira. Numa série de categorias jurídicas, o paralelismo pode orientar a comparação. Quando a editora alegar que a série foi resolvida, procure a construção substituta em vez de conferir apenas a contagem de artigos.

Quando houver uma série, leia os parágrafos inteiros. Verifique se uma ideia retorna depois de outro assunto ou se a paráfrase repete a transcrição sem aplicá-la. Preserve a sequência que distingue hipóteses úteis ao leitor.

Execute `aberturas NUMERO` sobre o candidato gravado. Leia as sequências que restaram e as novas, incluindo a passagem entre subtítulos. Registre em `bordas` a correção ou a distinção que justifica o paralelismo. No cotejo de sentido, identifique quem pratica o ato, qual evento produz o efeito e a que hipótese se ligam o prazo e a exceção. Um termo técnico que nomeia o conceito ensinado continua necessário mesmo quando a paráfrase soa natural.

**Saída.** `registrar conferencia NUMERO NOTA.json` com `trecho`, `fidelidade` e `bordas`. Identifique ao menos uma decisão verificável no capítulo e a situação dos achados anteriores. Acrescente `pendencias`. Use `[]` quando a unidade estiver apta. Para cada correção, informe a unidade de destino (posição no mapa, a partir de 1) e o problema com a seção e o efeito sobre o leitor. Exemplo: `[{"unidade":2,"problema":"Em 1.6, a paráfrase omite o nome técnico da atividade que o candidato precisa identificar."}]`. Continue a fase para reunir achados da mesma unidade. Ao terminar, consulte `atual`, reabra os capítulos atingidos em lote e siga a ficha de edição.
