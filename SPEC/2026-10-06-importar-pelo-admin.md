# Importar jogos pelo painel admin (2026-10-06)

## O quê e por quê
Hoje só se traz jogos reais pela linha de comando. O administrador precisa buscar um jogo pelo nome na Steam, ver a capa e importá-lo com um clique, sem acesso ao servidor. Reaproveita a importação e as fontes plugáveis já existentes (IMP-01..09).

## Critérios de aceitação
- IAD-01: `/admin/importar` exige administrador, como o resto de `/admin/*`, e o painel tem um link para ela
- IAD-02: a busca por nome (mínimo 2 caracteres) lista até 10 resultados da fonte com capa e título, e um botão "Importar" em cada um; resultado que já está no catálogo aparece marcado, sem botão
- IAD-03: importar é um POST com token CSRF; busca os detalhes na fonte, cria o jogo no catálogo e redireciona para a página dele com uma mensagem de sucesso
- IAD-04: importar de novo o mesmo jogo não duplica e avisa que ele já estava no catálogo
- IAD-05: fonte fora do ar ou com erro mostra uma mensagem na tela, sem erro 500, e não cria nada
- IAD-06: resultado que não é jogo ou sem título ou data de lançamento válidos não é importado e informa o motivo
- IAD-07: cada importação bem-sucedida grava um registro de auditoria `jogo.importar` com título, fonte e id externo
- IAD-08: a fonte continua plugável: o módulo da fonte pode oferecer `buscar(termo, limite)` e `detalhe(external_id)`, e a tela só usa fontes que têm as duas funções (hoje, `steam`)
- IAD-09: os testes rodam sem rede, com a fonte substituída por uma falsa

## Fora do escopo
Importação em lote pela interface, edição dos dados antes de importar, busca por ID da Steam, escolha de fonte na tela.
