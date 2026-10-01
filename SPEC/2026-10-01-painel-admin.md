# Painel de administração (2026-10-01)

## O quê e por quê
O administrador mantém o catálogo e trata denúncias.

## Critérios de aceitação
- ADM-01: todas as rotas de administração respondem 403 a quem não é administrador e redirecionam visitantes ao login (GLOBAL-05)
- ADM-02: o administrador cria, edita e remove (soft delete) jogos, e restaura jogos removidos
- ADM-03: cadastro de jogo valida os campos de CAT-01 no servidor, com mensagens por campo
- ADM-04: o administrador gerencia gêneros, plataformas e desenvolvedoras; não é possível apagar um item em uso
- ADM-05: a fila de denúncias lista as pendentes, da mais antiga para a mais nova, com a avaliação, o autor, o motivo e quem denunciou
- ADM-06: o administrador oculta a avaliação, ou rejeita a denúncia; toda decisão registra quem decidiu e quando
- ADM-07: ocultar atualiza imediatamente notas médias, histogramas e feed (PAG-04, SOC-07)
- ADM-08: o administrador reverte uma ocultação
- ADM-09: existe registro de auditoria das ações administrativas, consultável e paginado
- ADM-10: o primeiro administrador é criado por comando de seed/CLI com credenciais vindas de variável de ambiente, nunca fixas no código

## Fora do escopo
Banimento de usuários, painel de métricas, múltiplos níveis de administrador.