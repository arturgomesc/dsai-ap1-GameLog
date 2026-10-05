# Catálogo só com jogos reais (2026-10-05)

## O quê e por quê
O catálogo publicado deve mostrar apenas jogos reais, com capa oficial e alguns deles já avaliados pela comunidade, para a home ter destaques de verdade. Esta spec substitui os critérios de volume do seed fictício (CAT-03) e o IMP-09 (deploy importando da Steam ao subir).

## Critérios de aceitação
- CRE-01: `flask seed` cria usuários e atividade, mas nenhum jogo fictício: todo jogo do catálogo tem `source` preenchido
- CRE-02: os jogos do seed vêm de um arquivo versionado (`src/app/dados/jogos.json`) com no mínimo 100 jogos, cada um com título, data, desenvolvedora, ao menos um gênero e capa; o seed não depende de rede
- CRE-03: a fonte `arquivo` segue o contrato de fonte (`listar(limite, termo)`) e filtra por título quando recebe `termo`
- CRE-04: `flask export-games --termos "a;b;c" --saida caminho` gera esse arquivo a partir da Steam, um jogo por termo, e informa quantos termos não renderam jogo
- CRE-05: o seed é determinístico: mesma semente gera o mesmo catálogo, as mesmas avaliações e a mesma ordem
- CRE-06: cerca de 30 jogos recebem pelo menos 3 avaliações cada, a maioria com texto; os demais ficam sem avaliação
- CRE-07: a home mostra em "Em destaque" só jogos com 3 ou mais avaliações visíveis, cada um com nota média e número de avaliações; jogo sem avaliação ou com avaliações ocultas abaixo de 3 não aparece ali
- CRE-08: o deploy (`render.yaml`) e o `dev.sh` rodam só o seed, sem importar da Steam; `import-games` segue disponível para somar jogos depois
- CRE-09: o gerador de jogos fictícios fica restrito aos testes automatizados e não é usado por nenhum comando

## Fora do escopo
Resenhas escritas à mão para cada jogo, sincronização periódica com a Steam, importação pela interface admin.
