# Humanizer em português brasileiro

O Humanizer corrige prosa em português brasileiro com a menor alteração que resolva o problema por completo. Preserva a redação que já funciona, a voz do autor e o sentido do texto. Os termos técnicos e jurídicos específicos do contexto permanecem na forma original.

Este fork adapta a [versão v4.0.0 do Humanizer de blader](https://github.com/blader/humanizer/releases/tag/v4.0.0). A skill usa 30 padrões de revisão. Eles ajudam a editar prosa e não servem para identificar a autoria de um texto.

**Antes**

> Vamos direto ao ponto. O formulário tem dois campos e fica aberto até sexta-feira, às 18h. Essa facilidade faz toda a diferença.

**Depois**

> O formulário tem dois campos e fica aberto até sexta-feira, às 18h.

## Instalação

### Claude Code

```text
/plugin marketplace add spirla/humanize
/plugin install humanizer@humanizer
```

O plugin requer Claude Code 2.1.142 ou posterior. Em versões anteriores, instale a skill com `npx skills add spirla/humanize --global --agent claude-code`.

### Codex

```sh
npx skills add spirla/humanize --global --agent codex
```

### pi

```sh
pi install git:github.com/spirla/humanize
```

Use `-l` para instalar somente no projeto atual. `pi update --extensions` atualiza a instalação.

### Claude.ai e Claude Desktop

Baixe o ZIP do repositório pelo menu **Code → Download ZIP** e importe-o como skill nas configurações.

### Outros agentes

```sh
npx skills add spirla/humanize --global --agent '*'
```

Remova `--global` para instalar apenas no projeto atual. Se o instalador não reconhecer o agente, copie o `SKILL.md` para o diretório de skills dele.

## Uso

No Claude Code, use `/humanizer:humanizer` se instalou o plugin ou `/humanizer` se instalou a skill diretamente. No Codex, use `$humanizer`. Também é possível pedir a revisão em linguagem natural.

```text
Revise este texto em português brasileiro com o Humanizer:

[cole o texto aqui]
```

- **Texto colado.** A skill devolve um rascunho, uma breve avaliação dos padrões que ainda aparecem e a versão final.
- **Arquivo indicado.** A skill lê a versão atual, grava só a prosa final no trecho pedido, preserva os elementos estruturados e informa quais seções revisou.
- **Etapa final de outra tarefa.** Todo texto entregue como produto de um projeto passa pela revisão antes da entrega. A skill devolve só o texto final.

Para calibrar a voz, forneça dois ou três parágrafos de sua autoria e indique qual trecho é a amostra. A skill acompanha escolhas de léxico, ritmo, aberturas, pontuação e transições.

## Como funciona

1. **Marcar.** Ler a unidade e seu contexto. Localizar os defeitos, as repetições em sequência e os termos técnicos e jurídicos que precisam ficar intactos.
2. **Corrigir.** Começar pela menor alteração que resolva o defeito. Ampliar a edição se a correção pontual for insuficiente. Reescrever o bloco inteiro quando o defeito estiver na estrutura.
3. **Conferir.** Aplicar os testes de conferência: apagar a frase, perguntar quem faz o quê, cortar o segundo termo do contraste, ler as bordas dos parágrafos em sequência, contar a pontuação retórica e ler em voz alta. Checar se o defeito foi resolvido, se os termos foram preservados e se alguma alteração pode ser revertida.
4. **Entregar.** Aplicar a mesma regra aos problemas que restaram e seguir o formato de saída pedido.

## Os 30 padrões

Os padrões da seção A justificam edição quando a ocorrência cumpre a função descrita. Um *sinal fraco isolado* pede outros indícios no mesmo trecho. A tabela resume o catálogo. A [skill](SKILL.md) explica as exceções e dá exemplos completos.

Três regras valem em toda revisão. “Crucial”, “em conclusão” e “em síntese” não entram na prosa própria. Mais de um travessão ou dois-pontos retórico a cada três parágrafos, ou os dois no mesmo parágrafo, pede a reescrita do trecho. O padrão que se repete pelo texto se corrige até desaparecer.

### A. Frases que anunciam em vez de dizer

| # | Padrão | O que fazer |
|---|---|---|
| 1 | **Contraste de correção vazio** | Afirmar o ponto e manter a oposição que muda o sentido. |
| 2 | **Fechos de efeito e frases fragmentadas** | Cortar o reforço que repete o parágrafo. |
| 3 | **Máximas com aparência de profundidade** | Enunciar o fato ou a proposição sustentada pelo trecho. |
| 4 | **Aberturas que preparam o efeito** | Começar pela afirmação. |
| 5 | **Resposta a objeção inexistente** | Retirar a defesa vazia e preservar as objeções pertinentes. |
| 6 | **Camada explicativa inócua** | Retirar a oração vaga e deixar a afirmação abrir o trecho. |
| 7 | **Frase que não diz o fato** | Escrever quem age, que ato pratica e que consequência decorre. |

### B. Ritmo aplicado em série

| # | Padrão | O que fazer |
|---|---|---|
| 8 | **Tríades forçadas** | Usar o número de itens que o conteúdo pede. |
| 9 | **Aberturas repetidas** | Reconstruir pela relação lógica as aberturas em que a repetição atrapalha a leitura. |
| 10 | **Travessões e dois-pontos retóricos** | Expressar a relação entre as ideias e preservar a pontuação funcional. |
| 11 | **Qualificadores empilhados** | Expressar uma vez o grau de certeza sustentado pela fonte. |
| 12 | **Hífens em pares artificiais** | Usar a locução natural em português e preservar a grafia dos termos. |
| 13 | **Voz passiva e sujeito oculto** | Nomear o agente quando ele for conhecido e relevante. |
| 14 | **Período travado** | Dividir até cada oração ter sujeito e verbo à vista. |

### C. Exagero e autoridade emprestada

| # | Padrão | O que fazer |
|---|---|---|
| 15 | **Vocabulário recorrente de IA** | Escolher palavras pelo sentido e pela função no trecho. |
| 16 | **Importância inflada** | Conservar o fato e descrever o impacto quando houver base. |
| 17 | **Relação vaga** | Nomear o vínculo que o texto sustenta. |
| 18 | **Gerúndio que acrescenta análise vazia** | Preservar o fato e a análise sustentada. |
| 19 | **Linguagem de propaganda** | Descrever o que o lugar, produto ou serviço oferece. |
| 20 | **Autoridade emprestada** | Atribuir à fonte identificada o que ela de fato afirma. |
| 21 | **Fórmulas longas e palavras rebuscadas** | Preferir o verbo simples e a palavra comum quando dizem o mesmo. |

### D. Formatação decorativa

| # | Padrão | O que fazer |
|---|---|---|
| 22 | **Negrito decorativo** | Retirar ênfase e rótulos que não ajudam a ler. |
| 23 | **Títulos decorativos** | Nomear o assunto e preservar a hierarquia. |
| 24 | **Aspas curvas fora da convenção do texto** | Seguir a convenção do formato ou da amostra de voz. |

### E. Restos da conversa e do rascunho

| # | Padrão | O que fazer |
|---|---|---|
| 25 | **Marcas de chatbot** | Retirar a moldura da conversa e preservar o conteúdo. |
| 26 | **Avisos de limitação e conjecturas** | Dizer que informação falta quando a lacuna afeta a conclusão. |
| 27 | **Primeira frase presa ao título** | Começar por uma afirmação que nomeie o assunto por extenso. |
| 28 | **Metadiscurso no lugar do assunto** | Dizer o que ocorre no assunto tratado e retirar o bastidor da produção. |

### F. Texto escrito para o leitor errado

| # | Padrão | O que fazer |
|---|---|---|
| 29 | **Reexplicação do que o leitor já sabe** | Em uma resposta, apresentar a decisão e conservar o contexto necessário. |
| 30 | **Referência sem objeto** | Nomear a coisa e dizer o conteúdo a que a remissão apontava. |

## Exemplo com termo jurídico

**Antes**

> Vale destacar que a exceção de pré-executividade foi juntada na terça-feira.
>
> A parte contrária se manifestou na sexta-feira.

**Depois**

> A exceção de pré-executividade foi juntada na terça-feira.
>
> A parte contrária se manifestou na sexta-feira.

## Fontes e licença

O catálogo original é de [blader/humanizer](https://github.com/blader/humanizer) e se baseia em [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), mantido pelo [WikiProject AI Cleanup](https://en.wikipedia.org/wiki/Wikipedia:WikiProject_AI_Cleanup). Os exemplos deste fork foram escritos em português brasileiro.

Consulte o [histórico de versões](CHANGELOG.md) e a [licença MIT](LICENSE).
