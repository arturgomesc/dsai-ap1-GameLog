# Importação de jogos reais (2026-10-05)

## O quê e por quê
O catálogo só tem jogos fictícios gerados pelo seed. Esta parte importa jogos reais de uma fonte externa (Steam, sem chave de API) e mostra a capa oficial. A fonte é plugável: trocar ou somar outra (RAWG, IGDB) não deve mexer no restante do sistema.

## Critérios de aceitação
- IMP-01: `flask import-games` importa jogos reais da fonte `steam` por padrão; opções `--fonte`, `--limite` (padrão 40) e `--termo` (busca por nome)
- IMP-02: uma fonte é um módulo em `src/app/fontes/` com a função `listar(limite, termo)`, que devolve dicionários com `external_id`, `title`, `synopsis`, `release_date`, `developer`, `genres`, `platforms` e `cover_url`; registrar uma nova fonte exige um arquivo e uma linha em `FONTES`
- IMP-03: o jogo importado fica no catálogo comum, com gêneros, plataformas e desenvolvedora criados quando ainda não existem (sem duplicar por nome)
- IMP-04: reexecutar o comando não duplica jogos (identidade: fonte + `external_id`); jogos já importados são ignorados
- IMP-05: erro de rede ou item com dados inválidos não aborta a importação: o item é pulado e o comando informa quantos foram importados, ignorados e com falha
- IMP-06: item sem título ou sem data de lançamento válida é ignorado
- IMP-07: jogo com `cover_url` mostra a imagem real na home, nas listagens e na página do jogo; jogo sem ela continua com a capa SVG gerada
- IMP-08: a importação usa só a rede da fonte e nenhuma chave, e os testes rodam sem rede (fonte falsa injetada)
- IMP-09: o deploy executa a importação depois do seed; se ela falhar, o app sobe do mesmo jeito

## Fora do escopo
Chave de API, sincronização periódica, preços, avaliações da Steam, importação pela interface do painel admin, remoção dos jogos fictícios.
