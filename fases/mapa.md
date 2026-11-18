# Mapa da obra

Antes de alterar o texto, identifique a edição, o leitor e o gênero. Monte um mapa de conteúdo (MOC) na ordem de leitura. Use o sumário aprovado e os arquivos reais. Inclua introduções, anexos, exercícios e aparatos. Registre o que exige preservação literal. Um mapa existente serve se corresponder à edição e à sequência de hoje.

Para cada unidade, indique arquivo, finalidade prevista e ligação esperada com outra unidade quando houver. A finalidade prevista será confirmada durante a leitura. Folhas de resposta e tabelas podem ter função própria. Duas ocorrências planejadas do mesmo conceito podem servir a leitores em momentos diferentes.

Com arquivos locais, grave o mapa em Markdown e uma lista JSON de caminhos absolutos das unidades na ordem editorial. Inicie o controle numa pasta de trabalho com `python3 scripts/fluxo.py ESTADO iniciar ENTRADAS.json MOC.md` a partir da instalação da skill, ou use o caminho absoluto do script. O controle identifica a edição de cada arquivo. Para retomar, use `atual`. Reserve uma conversa e um estado por obra quando o pedido exigir contextos separados.

**Saída.** O mapa e a lista correspondem entre si e ao sumário. A primeira fase liberada pelo controle é a leitura. Em ambientes sem arquivos, mantenha o mesmo mapa na conversa e use intervalos identificáveis do material recebido.
