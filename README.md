# web-scraper

# 1. Visão Geral

## Objetivo

Desenvolver um serviço independente responsável por realizar a coleta de vagas de emprego em diferentes plataformas, normalizar os dados obtidos e armazená-los em um banco PostgreSQL.

O serviço será consumido por uma aplicação externa responsável por gerenciamento de usuários, buscas e candidaturas.

Este projeto **não possui interface gráfica**, autenticação ou gerenciamento de usuários.

Seu único objetivo é realizar scraping de vagas e persistir as informações.



## Instalação

```bash
git clone git@github.com:douglasaturnino/job-scraper
cd job-scraper
uv sync
```
## Configuração do Pre-commit

Após instalar as dependências, instale os hooks do pre-commit:

```bash
uv run pre-commit install
```

Para executar todos os hooks manualmente nos arquivos do projeto:

```bash
uv run pre-commit run --all-files
```

Para executar os hooks apenas nos arquivos alterados:

```bash
uv run pre-commit run
```

Caso seja necessário atualizar as versões dos hooks configurados:

```bash
uv run pre-commit autoupdate
```


## Executar

```bash
uv run src/main.py
```