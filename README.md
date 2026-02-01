# Teste Técnico - Intuitive Care

**Stack:** Python 3.10+, Pandas, SQLite, FastAPI, Vue.js, Docker (CDN)

---

## 📋 Sobre o Projeto
Este projeto consiste em um pipeline completo de Engenharia de Dados desenvolvido para coletar, processar e visualizar dados financeiros de operadoras de planos de saúde, utilizando dados abertos da Agência Nacional de Saúde Suplementar (ANS).

O sistema automatiza desde a coleta dos arquivos até a disponibilização dos dados em um Dashboard interativo, passando por rigorosos processos de limpeza e transformação.

### 🚀 Funcionalidades Principais
1.  **Robô de Coleta:** Monitora o site da ANS e baixa automaticamente as planilhas mais recentes de "Demonstrações Contábeis" e o "Cadastros de Operadoras".
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

Você pode rodar este projeto de duas formas: **Via Docker (Recomendado)** ou **Manualmente (Python Local)**.

---

## 🐳 Opção 1: Via Docker (Recomendado)
Este método garante que todo o ambiente (Banco de Dados, Dependências, Python) seja configurado automaticamente, sem risco de conflitos na sua máquina.

**Pré-requisitos:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

**Construir a Imagem**
No terminal, na raiz do projeto, execute:
```bash
docker build -t intuitive-app .
```

**Rodar a Aplicação**
sistema fará automaticamente o download dos dados, o processamento e iniciará a API.
```
docker run -p 8000:8000 intuitive-app
```

## 🐍 Opção 2: Execução Manual (Local)
Caso não queira usar Docker, siga os passos abaixo.

**Pré-requisitos:** Python 3.10+, Git e Pip.

**Clonar o Repositório**

```
git clone [https://github.com/alefjlcz/IntuitiveCare_Teste.git](https://github.com/alefjlcz/IntuitiveCare_Teste.git)
cd IntuitiveCare_Teste
```

**Instalar Dependências**
Instale as bibliotecas listadas no arquivo de requisitos:
```
pip install -r requirements.txt
```

**Executar o Pipeline de Dados**
Este script conecta-se à ANS, baixa os arquivos, processa os dados e cria o banco intuitive_care.db.
```
python main.py
```

**Iniciar o Servidor**
```
python -m uvicorn src.api:app --reload
```

## 📊 Acessando o Dashboard (Método 1 ou 2)
### **Independente de como você rodou o backend (Docker ou Manual), a forma de acessar o visual é a mesma:**

1- Navegue até a pasta interface-web dentro do projeto.

2- Dê um duplo clique no arquivo index.html. (Se caso não funcionar, aperte botão direito -> Open In -> Browser -> Default)

3- O navegador abrirá o dashboard conectado automaticamente à sua API local.