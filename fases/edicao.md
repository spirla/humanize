# Edição do capítulo

Abra a entrada da edição identificada no mapa, os achados deste capítulo e as regras da Humanizer aplicáveis a cada passagem. Resolva os problemas concretos. Quando faltar ligação entre regra, condição, exemplo ou consequência, redija a ligação que os fatos sustentam. Ajuste a sequência inteira quando a simples troca da primeira palavra só deslocar a repetição.

Grave o candidato em pasta de trabalho. Conserve os títulos aprovados, fatos, fundamentos, transcrições, fórmulas fixas, referências, números, links e termos técnicos. Compare com o texto inicial e reverta mudanças sem função. Se a leitura justificar a preservação integral, indique a própria entrada como candidato. A fase admite correção de qualquer achado material da leitura, inclusive um que tenha escapado no diagnóstico.

Quando houver pendências em `atual`, reabra em uma chamada as unidades atingidas, por exemplo `reabrir edicao 2 5`. Trabalhe sobre a última versão do candidato e compare-a com o original. Na nota da unidade, inclua `resolucoes`, um objeto que associe cada número de pendência à passagem corrigida e à decisão concreta. Exemplo: `{"3":"Na seção 1.6, recuperei o termo técnico e mantive a explicação do ato."}`. Se o cotejo justificar preservar o texto, indique a passagem e a razão. Resolva os achados da unidade antes de registrar seu novo candidato. Cada unidade reaberta volta à conferência; a obra volta à remontagem uma vez após a rodada.

**Saída.** `registrar edicao NUMERO NOTA.json --candidato ARQUIVO` com `trecho` literal do candidato e `intervencao` indicando onde houve mudança e por quê, ou a razão concreta para preservar. O controle fixa a versão que seguirá para conferência.
