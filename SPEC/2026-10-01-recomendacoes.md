# Recomendações (2026-10-01)

## O quê e por quê
Sugerir jogos que o jogador ainda não conhece, a partir do que ele já avaliou.

## Critérios de aceitação
- REC-01: recomendações só consideram jogos que o usuário ainda não avaliou nem marcou com status
- REC-02: a pontuação combina afinidade por gênero (peso pelas notas do usuário, notas altas pesam mais) e nota média do jogo
- REC-03: jogador com avaliações recebe até 20 recomendações, cada uma com o motivo ("porque você gostou de X")
- REC-04: jogador sem avaliações recebe os jogos mais bem avaliados, com aviso explicando isso
- REC-05: o resultado é determinístico: mesmos dados geram a mesma ordem (desempate por título)
- REC-06: jogos removidos e ocultos nunca são recomendados
- REC-07: o usuário dispensa uma recomendação, e o jogo deixa de ser sugerido a ele
- REC-08: recomendações são recalculadas quando o usuário avalia um jogo, sem exigir ação manual
- REC-09: a página responde em até 800 ms com o seed padrão em ambiente local

## Fora do escopo
Aprendizado de máquina, filtragem colaborativa entre usuários, e-mails de recomendação.