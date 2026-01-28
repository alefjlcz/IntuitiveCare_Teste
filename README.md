# Teste Técnico - IntuitiveCare

## Visão Geral

Solução de automação completa para coleta, processamento, armazenamento e exposição de dados da ANS. O projeto consiste em um pipeline ETL que normaliza demonstrações financeiras históricas e disponibiliza consultas analíticas via API.

A solução foi desenvolvida focando em **resiliência** (tratamento de erros de layout da fonte) e **facilidade de execução** para o avaliador.

## Tecnologias Utilizadas

O projeto foi desenvolvido em **Python 3.13** visando performance e recursos modernos, utilizando as bibliotecas:

* **requests:** Comunicação HTTP e download dos arquivos.
* **beautifulsoup4:** Web scraping para navegação dinâmica na estrutura de pastas da ANS.
* **zipfile:** Manipulação e leitura de arquivos compactados.
* **pandas:** Motor de processamento, limpeza e agregação de dados (ETL).
* **fastapi / uvicorn:** Criação da API REST e servidor web assíncrono.
* **sqlite3:** Banco de dados relacional embarcado (garantindo portabilidade sem configuração extra).

## Estrutura do Projeto

* `main.py`: Orquestrador principal. Executa o pipeline completo sequencialmente.
* `src/`: Módulos da aplicação.
  * `coleta.py`: Crawler que identifica e baixa os arquivos mais recentes.
  * `processamento.py`: Leitura dos ZIPs, normalização de colunas e unificação.
  * `transformacao.py`: Limpeza de dados, cálculos estatísticos e regras de negócio.
  * `banco_dados.py`: Gerenciamento da persistência no SQLite.
  * `api.py`: Aplicação Web e rotas da API.
  * `scripts_mysql.sql`: Scripts SQL avançados (Queries analíticas e DDL para MySQL).
* `downloads_ans/`: Diretório local para cache dos arquivos brutos.

## Como Executar

1. **Instale as dependências:**
   ```bash
   pip install requests pandas beautifulsoup4 fastapi uvicorn