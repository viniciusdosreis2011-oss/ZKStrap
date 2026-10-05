# ZKStrap — Official Update Repository

Este repositório é a fonte oficial do sistema de atualização do ZKStrap.

## Canais

- `channels/stable.json` — versões públicas recomendadas
- `channels/beta.json` — builds de teste públicas/opcionais
- `channels/dev.json` — builds de desenvolvimento/Owner

Os pacotes binários devem ser publicados em **GitHub Releases**. O ZKStrap baixa somente pacotes declarados pelos manifests acima e valida o SHA-256 antes de instalar.

## Segurança

O updater preserva os dados do usuário fora da pasta do programa em `%LOCALAPPDATA%\ZKSTRAP` e cria backup da instalação anterior antes de substituir arquivos.

Consulte `docs/RELEASING.md` para o fluxo de publicação.
