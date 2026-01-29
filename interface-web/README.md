# Teste Técnico - Engenharia de Dados e Fullstack
**Candidato:** Alessandro Barbosa

## Visão Geral do Projeto

Este projeto apresenta uma solução completa de automação e visualização de dados para o desafio proposto pela IntuitiveCare. O sistema consiste em um pipeline de dados (ETL) que coleta demonstrações financeiras de operadoras de saúde diretamente do portal da ANS, normaliza essas informações em um banco de dados relacional e as expõe através de uma API REST consumida por uma interface web.

O desenvolvimento foi norteado pelos princípios de arquitetura limpa e simplicidade (KISS), visando garantir a facilidade de execução em diferentes ambientes e a manutenibilidade do código.

---

## Stack Tecnológico e Decisões de Arquitetura

### Backend (Python 3.13)
* **FastAPI:** Framework selecionado pela alta performance (ASGI) e pela geração automática de documentação técnica (OpenAPI/Swagger), otimizando o tempo de desenvolvimento em comparação ao Flask.
* **SQLite:** Banco de dados relacional embarcado. A escolha elimina a necessidade de configuração de servidores de banco de dados locais (como MySQL ou PostgreSQL) por parte do avaliador, garantindo execução imediata.
    * *Nota:* Scripts DDL e DML compatíveis com MySQL Enterprise foram fornecidos separadamente no arquivo `src/scripts_mysql.sql`.
* **Pandas & BeautifulSoup4:** Motor de ETL. Implementação de um crawler dinâmico que mapeia a estrutura de diretórios da ANS para identificar arquivos recentes, mitigando a quebra de links estáticos ("hardcoded").

### Frontend (Vue.js 3 + Vite)
* **Vue 3 (Composition API):** Utilizado para construção de uma interface reativa e modular.
* **Fetch API:** A camada de comunicação HTTP utiliza recursos nativos do navegador, dispensando bibliotecas externas como Axios para reduzir o tamanho do bundle final.
* **Gestão de Estado:** O estado da aplicação é gerenciado localmente via `Ref` e `Reactive`, evitando a complexidade desnecessária de stores globais (Pinia/Redux) para o escopo deste teste.

---

## Diferenciais Técnicos e Resiliência

1.  **Resiliência a Estrutura de Dados:**
    A camada de apresentação (Frontend) implementa lógica defensiva para lidar com variações na nomenclatura das chaves JSON (ex: `Razao_Social` vs `razao_social`) e na estrutura de resposta da API (listas planas vs objetos paginados), garantindo estabilidade mesmo diante de alterações no Backend.

2.  **Tratamento de Encoding:**
    O pipeline de dados aplica codificação `utf-8-sig` nos arquivos gerados, assegurando a correta renderização de caracteres especiais da língua portuguesa em softwares de planilha (Excel).

3.  **Sanitização e Consistência:**
    Registros com inconsistências financeiras ou dados cadastrais nulos são tratados durante o processamento para assegurar a integridade das métricas estatísticas apresentadas.

---

## Instruções de Instalação e Execução

O projeto opera em arquitetura cliente-servidor. É necessário executar os serviços simultaneamente em terminais distintos.

### 1. Backend (API e Processamento)
Instale as dependências e inicie o serviço:

```bash
pip install fastapi uvicorn pandas requests beautifulsoup4
python main.py  # Executa o ETL inicial
python -m uvicorn src.api:app --reload
npm install chart.js vue-chartjs

2. Frontend (Interface Web)
Navegue até o diretório da interface e inicie o servidor de desenvolvimento:

Bash
cd interface-web
npm install
npm run dev
Acesse a aplicação em: http://localhost:5173