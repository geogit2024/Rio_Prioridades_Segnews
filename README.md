# Rio Prioridades Segnews

Feed público de notícias de segurança e prioridades do Rio de Janeiro, atualizado automaticamente pelo scraper Nova Terra.

O GitHub Actions executa a coleta a cada 15 minutos e publica alterações automaticamente. Também é possível executar manualmente em **Actions > Atualizar feed de notícias > Run workflow**.

Arquivos disponíveis:

- [`noticias.json`](noticias.json): formato estruturado para consumo por aplicações.
- [`noticias.txt`](noticias.txt): uma notícia por linha, com data e link.
- [`index.html`](index.html): ticker/letreiro de notícias em HTML, publicado via GitHub Pages em https://geogit2024.github.io/Rio_Prioridades_Segnews/.

O workflow usa somente fontes públicas de notícias e não precisa de credenciais. O token padrão do GitHub Actions tem permissão restrita de escrita neste repositório.
