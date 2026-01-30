# Teste Técnico - Engenharia de Dados (Intuitive Care)

**Stack:** Python 3.10+, Pandas, SQLite, FastAPI, Vue.js (CDN)

---

## 📋 Sobre o Projeto
Este projeto consiste em um pipeline completo de Engenharia de Dados (End-to-End) desenvolvido para coletar, processar e visualizar dados financeiros de operadoras de planos de saúde, utilizando dados abertos da Agência Nacional de Saúde Suplementar (ANS).

O sistema automatiza desde a coleta dos arquivos (Web Scraping) até a disponibilização dos dados em um Dashboard interativo, passando por rigorosos processos de limpeza e transformação (ETL).

### 🚀 Funcionalidades Principais
1.  **Robô de Coleta (Web Scraping):** Monitora o site da ANS e baixa automaticamente as planilhas mais recentes de "Demonstrações Contábeis" e o "Cadastros de Operadoras".
2.  **Pipeline ETL:**
    * Padronização de arquivos CSV (correção de encoding e delimitadores).
    * Limpeza de dados financeiros (conversão de formatos brasileiros `1.000,00` para float).
    * Enriquecimento de dados (Join entre despesas e cadastro da operadora).
3.  **API RESTful:** Servidor de alta performance para consulta de dados paginados e estatísticas.
4.  **Dashboard Analytics:** Interface gráfica moderna para visualização de KPIs, gráficos e busca detalhada.

---

## 🛠️ Tecnologias e Bibliotecas

O projeto foi construído com foco em **performance**, **simplicidade de execução** e **manutenibilidade**.

| Componente | Tecnologia | Motivo da Escolha |
| :--- | :--- | :--- |
| **Linguagem** | Python 3.10+ | Padrão de mercado para Engenharia de Dados. |
| **ETL** | Pandas | Processamento eficiente em memória para datasets médios (< 2GB). |
| **API** | FastAPI | Performance assíncrona (ASGI) superior ao Flask e documentação automática. |
| **Banco** | SQLite | Portabilidade total (arquivo único) para facilitar a avaliação do teste. |
| **Frontend** | Vue.js (CDN) | Framework reativo leve. O uso via CDN elimina a necessidade de `npm install` e builds complexos. |
| **Scraping** | BeautifulSoup4 | Parsing robusto de HTML para localizar links de arquivos dinâmicos. |

## 🌟 Diferenciais Implementados

O projeto foi desenvolvido observando requisitos não-funcionais críticos para ambientes produtivos:

1.  **🚀 Performance & Otimização de Banco de Dados**
    * **Paginação Server-Side:** A API utiliza cláusulas `LIMIT` e `OFFSET` no SQL. Isso impede que o banco trafegue megabytes de dados desnecessários, mantendo a resposta rápida (<50ms) mesmo com milhares de registros.
    * **Filtros Nativos:** As buscas por texto utilizam `WHERE LIKE` diretamente no motor SQLite, sendo muito mais eficientes que filtrar listas em Python.

2.  **🛡️ Qualidade de Código (QA)**
    * Implementação de testes de integração automatizados com **Pytest**.
    * Comando para execução: `pytest`

3.  **☁️ Arquitetura Cloud-Ready (Docker)**
    * O projeto é "Container Native". O `Dockerfile` incluso permite o deploy imediato em orquestradores como Kubernetes ou serviços Serverless (AWS Fargate, Google Cloud Run).
    * Isolamento total de dependências.

4.  **🧩 Arquitetura Desacoplada**
    * **ETL (Coleta/Processamento)** separado da **API**, permitindo que o pipeline de dados rode em agendadores (como Airflow) sem impactar a performance do site.
---

## 🚀 Como Executar o Projeto

Siga este guia passo a passo para rodar a aplicação completa em seu ambiente local.

### Pré-requisitos
* **Python 3.10** ou superior instalado.
* **Git** instalado.
* Um navegador web moderno (Chrome, Edge, Firefox).

---

### 1. Clonar o Repositório
Baixe o código fonte para sua máquina. Abra o terminal e execute:

```bash
git clone [https://github.com/alefjlcz/IntuitiveCare_Teste.git](https://github.com/alefjlcz/IntuitiveCare_Teste.git)
cd IntuitiveCare_Teste
```

### Instalar Pendências
Instale as bibliotecas necessárias (FastAPI, Pandas, Uvicorn, etc.) listadas no arquivo de requisitos:
```
pip install -r requirements.txt
```

### 3. Executar o Pipeline de Dados (ETL)
Esta etapa é fundamental. O script abaixo irá conectar-se ao site da ANS, baixar os arquivos CSV mais recentes, realizar a limpeza dos dados e criar o banco de dados local (intuitive_care.db).
```
python main.py
```

### 4. Iniciar o Servidor (Backend)
Com o banco de dados criado, inicie a API RESTful:
```
python -m uvicorn src.api:app --reload
```
O terminal exibirá que a aplicação está rodando em: http://127.0.0.1:8000.

### 5. Acessar o Dashboard (Frontend)
Para visualizar os dados, não é necessário instalar Node.js ou servidores adicionais.

1- Navegue até a pasta interface-web/ dentro do projeto.

2- Dê um duplo clique no arquivo index.html.

3- O navegador abrirá o dashboard interativo conectado automaticamente à API.

### 🐳 Alternativa: Execução via Docker (Nuvem)
Caso prefira rodar a aplicação em um container isolado (sem instalar Python na sua máquina), utilize o Docker:

```
# 1. Construir a imagem
docker build -t intuitive-app .

# 2. Rodar o container
docker run -p 8000:8000 intuitive-app
```
Após rodar, acesse o arquivo index.html normalmente.