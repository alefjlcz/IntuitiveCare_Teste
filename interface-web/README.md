# Teste Técnico - IntuitiveCare

## Visão Geral do Projeto

Este projeto apresenta uma solução completa de automação e visualização de dados para o desafio proposto pela IntuitiveCare. O sistema consiste em um pipeline de dados que coleta demonstrações financeiras de operadoras de saúde diretamente do portal da ANS, normaliza essas informações em um banco de dados relacional e as expõe através de uma API REST consumida por uma interface web moderna.

O desenvolvimento foi norteado pelos princípios de arquitetura limpa e simplicidade, visando garantir a resiliência do código e a facilidade de execução pelo avaliador.

---

## Stack Tecnológico e Decisões de Arquitetura

### Backend (Python 3.13)
* **FastAPI:** Framework selecionado pela alta performance assíncrona  e pela geração automática de documentação via Swagger UI.
* **SQLite:** Banco de dados relacional embarcado. Escolhido pela portabilidade, eliminando a necessidade de configuração de servidores externos para a avaliação do teste.
* **Pandas:** Motor principal de ETL, utilizado para a limpeza, transformação e consolidação de grandes volumes de dados provenientes de múltiplos arquivos CSV e ZIP.

### Frontend (Vue.js 3 + Vite)
* **Vue 3 (Composition API):** Utilizado para a construção de uma interface reativa, modular e de alto desempenho.
* **Chart.js:** Biblioteca integrada para a visualização dinâmica de dados estatísticos por meio de gráficos de barras.
* **Fetch API Nativa:** Opção técnica para manter o projeto leve, utilizando recursos nativos do navegador para comunicação assíncrona com a API.

---

## Diferenciais Técnicos e Resiliência

1. **Busca Híbrida e Inteligente:**
   A API e o Frontend foram projetados para realizar buscas simultâneas por Razão Social, CNPJ ou Registro ANS em um único campo. O sistema aplica sanitização de strings, permitindo que buscas por CNPJ funcionem com ou sem pontuação (ex: "04.201.372/0014-51" ou "04201372001451").

2. **Pipeline de Dados com Merge Cadastral:**
   O processo ETL não apenas extrai dados financeiros, mas realiza um cruzamento (Merge) com o Cadastro de Operadoras (Cadop). Isso garante que o sistema exiba informações completas, incluindo a UF correta e o CNPJ oficial de cada instituição.

3. **Resiliência a Encoding e Estrutura:**
   O processador de dados implementa lógica de "leitura blindada", detectando automaticamente o encoding dos arquivos (UTF-8 ou CP1252/Latin-1) para evitar corrupção de caracteres especiais. Além disso, o sistema ignora automaticamente metadados ou linhas de cabeçalho inconsistentes nos arquivos da ANS.

4. **Interface Gerencial:**
   Inclusão de um dashboard estatístico que exibe o "Top 10 Estados" por volume de despesas, além de um modal detalhado que apresenta a ficha consolidada de cada operadora.

---

## Instruções de Instalação e Execução

O projeto opera em arquitetura cliente-servidor. É necessário executar os serviços em terminais distintos.

---

## Trade-offs Técnicos e Justificativas
1. Escolha do Framework Backend: FastAPI
Decisão: Opção pelo FastAPI em detrimento ao Flask.

Justificativa: O FastAPI oferece performance superior através de suporte nativo a operações assíncronas (ASGI) e validação de dados automática com Pydantic. A geração automática da documentação via Swagger UI facilita testes imediatos sem necessidade de ferramentas externas.

2. Estratégia de Paginação: Offset-based
Decisão: Implementação de paginação baseada em Offset (page, limit).

Justificativa: Considerando o volume de dados e o requisito de uma interface gerencial, o Offset-based simplifica a navegação direta para páginas específicas no Frontend. Embora o Keyset pagination seja mais performático para tabelas gigantescas, o volume consolidado da ANS é perfeitamente suportado por Offset com índices adequados no SQLite.

3. Gerenciamento de Estado no Frontend: Composition API (Vue 3)
Decisão: Uso de Refs e Reactives locais em vez de Pinia/Vuex.

Justificativa: Para uma aplicação de dashboard com escopo focado, o uso de estados globais introduziria complexidade desnecessária. A Composition API permite a extração de lógicas reutilizáveis de forma limpa, mantendo o bundle final leve e de fácil manutenção.

4. Cache vs. Queries Diretas: Pré-cálculo no ETL
Decisão: Os dados estatísticos são pré-processados e agregados durante a fase de ETL.

Justificativa: Em vez de calcular somas complexas em cada requisição à API, o pipeline de dados já consolida os valores por operadora e UF. Isso reduz a carga do banco de dados e garante respostas imediatas para o usuário final no Frontend.

### 1. Preparação do Ambiente
Instale as dependências necessárias para o Python e Node.js:

```bash
# Dependências do Backend
pip install fastapi uvicorn pandas requests beautifulsoup4

# Dependências do Frontend (na pasta interface-web)
cd interface-web
npm install
```
## Acessando ambientes.

```bash
# No terminal raiz, execute o pipeline (Gera o banco intuitive_care.db)
python main.py

# Inicie a API 
python -m uvicorn src.api:app --reload

# Em outro terminal (pasta interface-web), inicie o Vue
npm run dev
```