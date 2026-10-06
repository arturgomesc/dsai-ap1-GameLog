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

## Registro de alterações
- 2026-10-06: o snapshot `src/app/dados/jogos.json` foi regenerado após a correção de datas da importação (IMP-10). Entraram jogos que tinham sido descartados por terem lançamento em novembro (como Half-Life 2, Left 4 Dead 2 e Apex Legends), as datas de março, junho e julho foram corrigidas, e "Among Us" (Steam 945360) passou a ser o jogo escolhido no lugar de "Among Us 3D" (Steam 3168600), que só entrou porque o original foi descartado. Os critérios não mudam.
- 2026-10-06 (curadoria do snapshot): a busca por nome da Steam trouxe a sequência ou a variante em vez do jogo pedido, e alguns jogos ficaram de fora. Trocados pelo id da Steam: Subnautica 2 → Subnautica (264710), Slay the Spire 2 → Slay the Spire (646570), Path of Exile 2 → Path of Exile (238960), Inside the Backrooms → INSIDE (304430), Planet Zoo 2 → Planet Zoo (703080), Planet Coaster 2 → Planet Coaster (493340), Frostpunk 2 → Frostpunk (323190), Kingdom Come: Deliverance II → Kingdom Come: Deliverance (379430), Slime Rancher 2 → Slime Rancher (433340), Wargroove 2 → Wargroove (607050), SUPERHOT VR → SUPERHOT (322500) e DEATH STRANDING 2 → DEATH STRANDING DIRECTOR'S CUT (1850570). Acrescentados: Hades (1145360), Rocket League (252950), Football Manager 2024 (2252570) e Fall Guys (1097150). O catálogo passa de 149 para 153 jogos. Counter-Strike: Global Offensive não entra, porque hoje é o mesmo aplicativo do Counter-Strike 2 (730), que já está no catálogo. Os critérios não mudam.
