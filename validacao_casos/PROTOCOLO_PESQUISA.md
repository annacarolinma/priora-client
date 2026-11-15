# Protocolo de pesquisa e extração de casos (validação do Priora)

Você é um PESQUISADOR. Sua tarefa é só encontrar casos e extrair pistas. NÃO atribua pesos, NÃO calcule nada.
Pasta de trabalho: C:\Users\laisa\AppData\Local\Temp\claude\5bd65bae76e7bdfb\329ed4ed-d15d-408d-b2f1-c19f7521a7f8\scratchpad\val
(grave arquivos JSON em UTF-8 com a ferramenta Write; as subpastas casos/ e gabaritos/ já existem)

## O que é um caso utilizável
- Um caso criminal REAL já resolvido com de 3 a 10 suspeitos nomeados e de 8 a 40 pistas independentes.
- Solução oficial única e conhecida (autor definido pela justiça, confissão ou DNA, com fonte).
- Texto público e gratuito, sem login, sem pagar, sem contornar bloqueio. Use WebSearch e WebFetch. Se não achar casos suficientes, entregue menos e diga quantos faltaram. NÃO invente caso nem pistas.
- Direitos autorais: não copie trechos longos. Reescreva cada pista com suas palavras (fatos, não prosa). Registre fonte, URL e licença/condição de uso.

## Regras para as pistas (evidências)
- Cada pista é um FATO ou um TESTEMUNHO, escrito de forma neutra, em português, em 1 a 3 frases, sem concluir quem é o culpado.
- Inclua TODAS as pistas relevantes disponíveis na fase de investigação, também as que afastam suspeitos (álibis, contradições, pistas falsas, red herrings), não só as que incriminam o culpado. O número de pistas ligadas a cada suspeito NÃO deve entregar o culpado.
- Caso real: use só o que os investigadores sabiam ANTES da solução. Não inclua a sentença, a confissão final do autor nem a revelação do culpado. Evite viés de retrospectiva.
- Uma mesma informação não entra duas vezes (se um laudo derivar de outro registro, escreva como uma pista só ou deixe claro que depende do outro).
- "tipo" da pista: um destes: Digital, DNA, Depoimento, Documental, Física, Audiovisual, Biológica, Motivação, Antecedente, Pericial, Telefônica, Comportamento.
- "suspeitos": lista com TODOS os suspeitos a que a pista se refere (a favor ou contra). Se a pista não se refere a nenhum suspeito específico, use lista vazia.

## Arquivo CEGO (o que o avaliador de pesos vai ler): casos/<ID>.json
{
  "id": "J01",
  "tipo": "real",
  "resumo": "2 a 4 frases neutras sobre o crime (sem solução)",
  "suspeitos": [ {"id": "S1", "perfil": "descrição breve e neutra (relação com a vítima, ocupação, onde estava segundo ele)"} ],
  "evidencias": [ {"id": "E1", "tipo": "Depoimento", "texto": "...", "suspeitos": ["S1","S3"]} ]
}
- ANONIMIZE. Use só "S1", "S2"... com perfil neutro (ex.: "ex-companheiro da vítima"); troque nomes de pessoas, cidades, datas exatas e empresas por termos genéricos ("a vítima", "uma cidade do interior", "dois anos antes"). O arquivo cego não pode permitir reconhecer o caso. Não diga o país se isso identificar o caso.

## Arquivo de GABARITO (separado; o avaliador NÃO vai ver): gabaritos/<ID>.json
{
  "id": "J01",
  "titulo": "nome do caso real",
  "fonte": "nome da fonte", "url": "...", "licenca_ou_uso": "domínio público / uso livre / todos os direitos reservados (uso interno) / etc.",
  "culpado": ["S2"],
  "chave_nomes": {"S1": "nome real", "S2": "..."},
  "solucao": "como o desfecho oficial é explicado (2 a 5 frases) e, no caso real, o resultado judicial com a fonte",
  "pais_epoca": "país e ano",
  "tipo_crime": "homicídio / furto / envenenamento / incêndio / fraude / sequestro / ...",
  "observacoes": "limitações (poucos suspeitos, texto incompleto, pistas omitidas) e o que você deixou de fora"
}
("culpado" é uma lista de ids de suspeitos; pode ter mais de um autor.)

## Variedade
O conjunto total precisa ser MUITO variado (tipo de crime, época, país/ambientação, nº de suspeitos, nº de pistas, tipo de fonte, mix de tipos de pista). Siga a fatia que foi dada a você e escolha casos bem diferentes entre si.

## Entrega
Grave todos os arquivos e responda só com uma tabela curta: ID | título | nº suspeitos | nº pistas | fonte (URL) | licença/uso | problemas. Diga explicitamente se entregou menos casos que o pedido.
