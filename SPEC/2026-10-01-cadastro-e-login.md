# Cadastro e login (2026-10-01)

## O quê e por quê
O visitante cria conta, entra e sai; o jogador edita seu perfil. Sem conta não há avaliação, lista nem feed.

## Critérios de aceitação
- CAD-01: cadastro exige nome de usuário (3 a 20 caracteres, único, sem diferenciar maiúsculas), e-mail válido e único, e senha com no mínimo 8 caracteres
- CAD-02: senha é armazenada somente como hash com salt (GLOBAL-06)
- CAD-03: login com credenciais corretas cria sessão; credenciais erradas mostram mensagem genérica, sem revelar se o e-mail existe
- CAD-04: após 5 tentativas de login falhas em 15 minutos para o mesmo e-mail, novas tentativas são bloqueadas por 15 minutos
- CAD-05: logout invalida a sessão no servidor
- CAD-06: ao ser redirecionado ao login por ação protegida, o usuário volta à ação após entrar (GLOBAL-02)
- CAD-07: perfil público mostra nome, data de entrada, bio (até 280 caracteres) e contadores de avaliações, listas e seguidores
- CAD-08: o jogador edita bio e nome de exibição; avatar é gerado a partir das iniciais e de uma cor derivada do nome de usuário
- CAD-09: usuário nunca altera dados de outro usuário (403)
- CAD-10: papéis possíveis: jogador e administrador; todo cadastro novo é jogador

## Fora do escopo
Login social, recuperação de senha por e-mail, autenticação em dois fatores, upload de avatar.