# Comparar gosto entre jogadores (2026-10-06)

## O quê e por quê
Quem segue pessoas quer saber com quem tem gosto parecido. A comparação mostra o quanto duas pessoas concordam nas notas dos jogos que ambas avaliaram, onde divergem e o que uma pode indicar à outra. É sempre entre a pessoa logada e outra.

## Critérios de aceitação
- AFI-01: `/comparar` e `/u/<usuário>/comparar` exigem login; sem sessão redirecionam para a entrada e voltam depois (GLOBAL-02)
- AFI-02: a afinidade é `100 × (1 − média das diferenças absolutas de nota ÷ 10)`, arredondada para inteiro, sobre os jogos em comum avaliados por ambos; com menos de 3 jogos em comum não há percentual e a tela mostra "dados insuficientes"
- AFI-03: a comparação mostra a afinidade, o número de jogos em comum e a tabela deles com as duas notas, ordenada por diferença crescente e depois por título
- AFI-04: lista até 5 jogos em que concordam (diferença de 0 a 1) e até 5 em que divergem (diferença de 3 ou mais); sem nenhum, mostra uma mensagem
- AFI-05: mostra até 5 indicações da outra pessoa: jogos que ela avaliou com nota 8 ou mais e que eu não avaliei nem marquei com status, por nota decrescente e depois por título
- AFI-06: `/comparar` lista as pessoas que sigo com afinidade e jogos em comum, por afinidade decrescente (sem percentual por último) e depois por nome de usuário
- AFI-07: comparar consigo mesmo redireciona para o próprio perfil, e usuário inexistente responde 404
- AFI-08: o perfil de outra pessoa mostra a afinidade com um link para a comparação, apenas para quem está logado; visitante e o próprio perfil não mostram
- AFI-09: avaliações ocultas e jogos removidos não contam, e a afinidade é simétrica
- AFI-10: `/comparar` faz um número de consultas que não cresce com a quantidade de pessoas seguidas (no máximo 12)

## Fora do escopo
Pesos por gênero, comparar duas outras pessoas, notificações, histórico de afinidade, aprendizado de máquina.
