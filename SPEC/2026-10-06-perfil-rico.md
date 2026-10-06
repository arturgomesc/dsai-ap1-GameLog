# Perfil mais rico (2026-10-06)

## O quê e por quê
O perfil público só mostra contadores e as cinco últimas avaliações. Ele passa a contar o gosto da pessoa: o que ela joga, como avalia, que gêneros prefere e quais jogos ama. Estende CAD-07 sem mudar o que já existe (contadores, bio, seguir, listas).

## Critérios de aceitação
- PRF-01: o perfil mostra quantos jogos a pessoa tem em cada status (planejado, jogando, jogado, abandonado), incluindo os zerados
- PRF-02: mostra a nota média dada, com uma casa decimal, e o histograma de notas de 0 a 10; sem avaliações, mostra "—" no lugar da média
- PRF-03: mostra até 5 gêneros favoritos, a partir dos jogos avaliados ou marcados como jogado, em ordem de quantidade e depois por nome, cada um com a contagem e um link para a página do gênero
- PRF-04: mostra até 5 jogos favoritos: os de nota 8 ou mais, ordenados por nota, depois pela avaliação mais recente e depois pelo título; sem nenhum, a seção não aparece
- PRF-05: a linha do tempo lista as avaliações da pessoa da mais recente para a mais antiga, 10 por página (`?page=`), com jogo, nota, data e trecho da resenha de até 140 caracteres; página fora do intervalo cai na última válida
- PRF-06: avaliações ocultas por moderação e jogos removidos do catálogo não entram em estatística, favoritos, gêneros nem linha do tempo
- PRF-07: perfil sem atividade mostra mensagens de vazio, sem erro
- PRF-08: listas privadas continuam invisíveis para outras pessoas e o contador de listas não muda
- PRF-09: o número de consultas ao banco do perfil não cresce com a quantidade de avaliações (no máximo 15)

## Fora do escopo
Gráficos interativos, comparação entre perfis, estatísticas por período, privacidade configurável dos status.
