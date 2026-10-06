# Recomendações colaborativas (2026-10-06)

## O quê e por quê
As recomendações usam só gênero e nota média. Passam a usar também quem tem gosto parecido: pessoas com alta afinidade com você (AFI-02) e que gostaram de um jogo que você ainda não conhece. Estende REC-02 e REC-03 sem mudar as demais regras de recomendação (REC-01, 04..09).

## Critérios de aceitação
- COL-01: vizinhos são as outras pessoas com no mínimo 3 jogos em comum avaliados e afinidade de 70% ou mais com a pessoa logada, pela mesma fórmula de AFI-02
- COL-02: um jogo recebe pontuação colaborativa pela soma da afinidade (0 a 1) dos vizinhos que lhe deram nota 8 ou mais, dividida pelo número de vizinhos; a pontuação colaborativa entra na pontuação final com peso 1, somada à de gênero e à nota média (REC-02)
- COL-03: jogos que a pessoa já avaliou, marcou, dispensou ou que foram removidos continuam fora, e avaliações ocultas dos vizinhos não contam (REC-01, 06, 07)
- COL-04: quando a pontuação colaborativa de um jogo é maior que zero, o motivo cita o vizinho de maior afinidade que o recomenda (desempate por nome de usuário): "@bia, com 89% de afinidade com você, deu nota 9"; sem ela, vale o motivo de gênero de REC-03
- COL-05: pessoa sem vizinhos recebe exatamente as recomendações de antes desta spec
- COL-06: pessoa sem avaliações continua com o aviso e os mais bem avaliados (REC-04), sem consulta a vizinhos
- COL-07: o resultado é determinístico (REC-05) e simétrico no sentido de que os vizinhos são os mesmos que a comparação de gosto mostra
- COL-08: a página `/recomendacoes` responde em até 800 ms com o seed padrão (REC-09) e faz um número fixo de consultas, sem crescer com o número de vizinhos (no máximo 14)

## Fora do escopo
Fatoração de matrizes, aprendizado de máquina, recomendar a partir de pessoas que não têm jogos em comum, explicação com mais de um vizinho, ajuste de pesos pela interface.
