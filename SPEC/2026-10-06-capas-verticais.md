# Capas verticais dos jogos (2026-10-06)

## O quê e por quê
Os cartões do site são verticais (3:4), mas a capa guardada para jogos da Steam é a imagem horizontal da loja (`header_image`), que sai cortada e sem o título legível. A Steam também publica a capa vertical de biblioteca (600×900). O catálogo passa a usar a vertical quando ela existe. Ajusta IMP-07 sem mudar o resto.

## Critérios de aceitação
- CAP-01: a fonte Steam tenta a capa vertical `https://cdn.cloudflare.steamstatic.com/steam/apps/<id>/library_600x900.jpg` (sem hash, estável) e a usa como `cover_url` quando a resposta é 200 e de tipo imagem
- CAP-02: se a vertical não existe ou a verificação falha (rede, erro), usa a `header_image` como antes, sem abortar a importação (IMP-05)
- CAP-03: o snapshot `src/app/dados/jogos.json` é regenerado com `flask export-games` e passa a trazer a vertical onde existir; as capas que ficam na horizontal continuam válidas
- CAP-04: todo `cover_url` de jogo da Steam no catálogo termina em `library_600x900.jpg` ou é uma `header_image`; nenhum `cover_url` fica vazio
- CAP-05: capa horizontal em cartão vertical continua preenchendo o cartão sem distorcer (recorte centralizado), e a página do jogo mostra a capa inteira, sem cortar (proporção natural)
- CAP-06: os testes rodam sem rede, com a verificação de existência substituída

## Fora do escopo
Hospedar ou copiar as imagens no nosso servidor, redimensionar imagens, capas de outras fontes além da Steam.
