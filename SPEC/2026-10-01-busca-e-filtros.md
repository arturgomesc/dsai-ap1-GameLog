# Busca e filtros (2026-10-01)

## O quê e por quê
Encontrar jogos rapidamente por texto, gênero, plataforma, ano e nota.

## Critérios de aceitação
- BUS-01: busca por texto casa com título, desenvolvedora e gênero, sem diferenciar maiúsculas nem acentos
- BUS-02: filtros combináveis: gênero (um ou mais), plataforma (uma ou mais), faixa de ano de lançamento e nota média mínima
- BUS-03: ordenação por relevância, nota média, data de lançamento e título (A–Z)
- BUS-04: resultados paginados com 20 por página; página fora do intervalo retorna a última página válida ou lista vazia, nunca erro
- BUS-05: o estado de busca, filtros, ordenação e página fica na URL, e o link compartilhado reproduz o mesmo resultado
- BUS-06: busca sem resultados mostra mensagem e sugestão de limpar filtros
- BUS-07: jogos removidos nunca aparecem nos resultados
- BUS-08: parâmetros inválidos (ordenação desconhecida, ano não numérico) são ignorados com valor padrão, sem erro 500
- BUS-09: a busca responde em até 500 ms com o seed padrão em ambiente local

## Fora do escopo
Busca por voz, corretor ortográfico, histórico de buscas.