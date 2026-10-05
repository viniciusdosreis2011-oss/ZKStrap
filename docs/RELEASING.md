# Publicando uma atualização do ZKStrap

O updater trabalha com pacotes da pasta **buildada** (`dist/ZKStrap`), não com o ZIP do código-fonte.

## Fluxo recomendado

1. Gere o app com `BUILD_EXE.bat`.
2. Rode `MAKE_UPDATE_PACKAGE.bat`.
3. Ele cria um ZIP atualizável e mostra o SHA-256.
4. Publique esse ZIP em uma GitHub Release.
5. Copie a URL do asset da Release para o manifest do canal (`channels/stable.json`, `beta.json` ou `dev.json`).
6. Preencha `version`, `package_url`, `sha256`, `size_bytes`, `published_at` e `notes`.
7. Teste primeiro em `dev`, depois `beta`, e só então promova os mesmos dados para `stable`.

## Estrutura do pacote

O ZIP deve conter diretamente os arquivos da instalação:

```text
ZKStrap.exe
ZKUpdater.exe
_internal/...
```

Não coloque uma pasta extra envolvendo esses arquivos.

## Rollback

Antes de instalar uma atualização, o ZKUpdater salva a instalação anterior em `%LOCALAPPDATA%\ZKSTRAP\updates\backups`. Os dados pessoais do usuário ficam em `%LOCALAPPDATA%\ZKSTRAP` e não são substituídos pelo pacote.

## Manifest

Exemplo:

```json
{
  "channel": "stable",
  "version": "3.18.0",
  "published_at": "2026-10-05T18:00:00Z",
  "mandatory": false,
  "min_updater_version": "1.0.0",
  "package_url": "https://github.com/OWNER/ZKStrap/releases/download/v3.18.0/ZKStrap-v3.18.0-win64.zip",
  "sha256": "...",
  "size_bytes": 12345678,
  "notes": ["Update Center", "Backup e rollback"]
}
```
