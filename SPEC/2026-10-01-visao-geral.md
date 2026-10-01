# Visão geral: GameLog (2026-10-01)

## O quê e por quê

GameLog é uma plataforma web de catálogo e avaliação de jogos. Pessoas descobrem jogos, registram o que jogaram, dão nota, escrevem resenhas, montam listas e seguem outros usuários. Administradores cadastram jogos e moderam conteúdo.

O problema: jogadores perdem o histórico do que jogaram e não têm um lugar simples para descobrir jogos a partir da opinião de outras pessoas.

## Personas

- **Visitante**: navega, busca e lê páginas de jogos e resenhas sem conta.
- **Jogador**: tem conta; avalia, cria listas, segue pessoas, recebe recomendações.
- **Administrador**: gerencia catálogo e modera denúncias.

## Partes do sistema (uma spec por parte)

| Spec | Conteúdo |
|---|---|
| 2026-10-01-cadastro-e-login.md | contas, sessões, perfil |
| 2026-10-01-catalogo.md | jogos, gêneros, plataformas, desenvolvedoras |
| 2026-10-01-busca-e-filtros.md | busca, filtros, ordenação, paginação |
| 2026-10-01-pagina-do-jogo.md | detalhe, nota média, jogos relacionados |
| 2026-10-01-avaliacoes.md | nota, resenha, curtidas, denúncia |
| 2026-10-01-listas.md | status de jogo e listas customizadas |
| 2026-10-01-social.md | seguir usuários, feed de atividade |
| 2026-10-01-recomendacoes.md | sugestões a partir do histórico |
| 2026-10-01-painel-admin.md | cadastro de jogos, moderação |

Cada spec detalha seus próprios critérios. Estes são os critérios globais.

## Fluxo principal

1. O visitante abre a página inicial.
2. Pesquisa um jogo.
3. Abre a página do jogo.
4. Cria uma conta ou entra em uma conta existente.
5. Registra o jogo como jogado.
6. Dá uma nota e escreve uma resenha.
7. Adiciona o jogo a uma lista.
8. Segue outro jogador.
9. Consulta seu feed e recebe recomendações.

## Regras de domínio

- Um usuário só pode ter uma avaliação por jogo.
- Uma avaliação possui nota inteira de 0 a 10.
- Uma resenha pode existir sem texto, mas uma nota é obrigatória.
- Um usuário não pode seguir a si mesmo.
- Uma lista pertence a um único usuário.
- Um jogo pode pertencer a várias listas.
- Um jogo pode possuir múltiplas plataformas e gêneros.
- Um usuário pode marcar um jogo como planejado, jogando, jogado ou abandonado.
- Jogos removidos do catálogo não aparecem em buscas públicas.
- A remoção de um jogo do catálogo não apaga seu histórico ou suas avaliações.
- Conteúdo denunciado pode ser ocultado por um administrador.

## Critérios de aceitação globais

- **GLOBAL-01:** a aplicação abre em uma URL pública, sem login, na página inicial com jogos em destaque.
- **GLOBAL-02:** qualquer ação que exige conta redireciona o visitante ao login e volta à ação depois.
- **GLOBAL-03:** toda entrada de formulário é validada no servidor, com mensagem de erro clara.
- **GLOBAL-04:** listagens são paginadas (20 itens por página por padrão).
- **GLOBAL-05:** nenhuma rota de administração responde a quem não é administrador (403).
- **GLOBAL-06:** senhas nunca são armazenadas em texto puro.
- **GLOBAL-07:** todos os dados de jogos são fictícios, gerados por seed reproduzível.
- **GLOBAL-08:** cada critério de aceitação de cada spec tem ao menos um teste automatizado.

## Requisitos não funcionais

- A aplicação deve funcionar em navegadores modernos em desktop e dispositivos móveis.
- Erros da aplicação não devem expor segredos ou dados sensíveis.
- O seed deve produzir os mesmos dados quando executado nas mesmas condições.
- Os testes automatizados devem poder ser executados localmente sem depender de serviços externos.

## Fora do escopo

Jogos jogáveis no navegador, compra ou venda de jogos, pagamentos, chat em tempo real, aplicativo mobile nativo, integração com Steam ou outras lojas, upload de imagens de usuário (avatares usam iniciais ou cores geradas).

## Restrições

- Sem segredos no repositório; configuração por variáveis de ambiente do host.
- Capas de jogos são geradas (SVG/CSS) para evitar problemas de direitos autorais.
