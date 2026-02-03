# Monitoramento de Despesas - Operadoras ANS

> Teste Técnico para Estágio em Desenvolvimento - Intuitive Care

**Stack:** Python 3.10+, Pandas, SQLite, FastAPI, Vue.js, Docker.

---

## Sobre o Projeto
Este projeto consiste em um pipeline completo de Engenharia de Dados desenvolvido para coletar, processar e visualizar dados financeiros de operadoras de planos de saúde, utilizando dados abertos da Agência Nacional de Saúde Suplementar (ANS).

O sistema automatiza desde a coleta dos arquivos até a disponibilização dos dados em um Dashboard interativo, passando por rigorosos processos de limpeza e transformação.

### Funcionalidades Principais
1.  **Robô de Coleta:** Monitora o site da ANS e baixa automaticamente as planilhas mais recentes de "Demonstrações Contábeis" e o "Cadastros de Operadoras".
2.  **Pipeline ETL:**
    * Padronização de arquivos CSV (correção de encoding e delimitadores).
    * Limpeza de dados financeiros (conversão de formatos brasileiros `1.000,00` para float).
    * Tratamento de inconsistências e remoção de duplicatas (Regras de negócio aplicadas).
    * Enriquecimento de dados (Join entre despesas e cadastro da operadora).
3.  **API RESTful:** Servidor de alta performance (FastAPI) para consulta de dados paginados e estatísticas.
4.  **Dashboard Analytics:** Interface gráfica moderna para visualização de KPIs, gráficos e busca detalhada.

---

## Tecnologias e Bibliotecas

O projeto foi construído com foco em **performance**, **simplicidade de execução** e **manutenibilidade**. 

| Componente | Tecnologia | Motivo da Escolha                                                             |
| :--- | :--- |:------------------------------------------------------------------------------|
| **Linguagem** | Python 3.10+ | Padrão de mercado para Engenharia de Dados.                                   |
| **ETL** | Pandas | Processamento eficiente em memória para datasets médios.                      |
| **API** | FastAPI | Performance assíncrona superior ao Flask e documentação automática.           |
| **Banco** | SQLite | Portabilidade total (arquivo único) para facilitar a avaliação do teste.      |
| **Frontend** | Vue.js (CDN) | Framework reativo leve. O uso via CDN elimina a necessidade de `npm install`. |
| **Container** | Docker | Isolamento de ambiente e facilidade de reprodução.                            |
| **Testes** | Pytest | Framework robusto para testes de integração da API.                           |

---

## Diferenciais 

O projeto foi desenvolvido observando requisitos não-funcionais críticos para ambientes produtivos:

1.  **Performance & Otimização de Banco de Dados**
    * **Paginação Server-Side:** A API utiliza cláusulas `LIMIT` e `OFFSET` no SQL. Isso impede que o banco trafegue megabytes de dados desnecessários, mantendo a resposta rápida (<50ms).
    * **Filtros Nativos:** As buscas utilizam `WHERE LIKE` diretamente no motor SQL.

2.  **Qualidade de Código (QA)**
    * Implementação de testes de integração automatizados com **Pytest** para validar as rotas da API (`tests/test_api.py`).
    * Garante que endpoints críticos (`/operadoras`, `/estatisticas`) retornem status 200 e a estrutura JSON correta.

3.  **Arquitetura Cloud-Ready (Docker)**
    * O projeto é Container Native. O `Dockerfile` incluso permite o deploy imediato em qualquer ambiente que suporte containers, garantindo isolamento total de dependências.

---

## Como Executar o Projeto

Você pode rodar este projeto de duas formas: **Via Docker (Recomendado)** ou **Manualmente (Python Local)**.

### Opção 1: Via Docker (Recomendado)
Este método garante que todo o ambiente seja configurado automaticamente.

**Pré-requisitos:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

**1. Construir a Imagem**
No terminal, na raiz do projeto, execute:
```bash
docker build -t intuitive-app .
```

### Opção 2: Execução Manual (Local)
Caso não queira usar Docker, siga os passos abaixo.

**Pré-requisitos: Python 3.10+, Git e Pip.**

**1. Clonar o Repositório**
```
git clone [https://github.com/alefjlcz/IntuitiveCare_Teste.git](https://github.com/alefjlcz/IntuitiveCare_Teste.git)
cd IntuitiveCare_Teste
```

**2. Instalar Dependências**
```
pip install -r requirements.txt
```

**3. Executar o Pipeline de Dados**
Este script conecta-se à ANS, baixa os arquivos, processa os dados e cria o banco intuitive_care.db.
```
python main.py
```

**4. Iniciar o Servidor**
```
python -m uvicorn src.api:app --reload
```

**5. Executar Testes Automatizados***
Para validar a API, execute na raiz do projeto:
```
pytest
```

## Acessando o Dashboard
Independente de como você rodou o backend (Docker ou Manual), a forma de acessar o visual é a mesma:

1. **Navegue até a pasta interface-web/ dentro do projeto.**

2. **Dê um duplo clique no arquivo index.html.**

3. **O navegador abrirá o dashboard conectado automaticamente à sua API local.**

```
 Dica: Para ver a Documentação da API, acesse: http://localhost:8000/docs
 ```

### Testando a API (Postman)
Para facilitar a validação das rotas, incluí uma coleção pronta para uso.

1. **Abra o Postman.**

2. **Clique em Import -> Upload Files.**

3. **Selecione o arquivo collection.json localizado na raiz deste projeto.**

4. **Execute as requisições já configuradas.**

## Decisões Técnicas e Trade-offs

### 1.2. Processamento de Arquivos
 * Decisão: Processamento Incremental.

 * Justificativa: Carregar todos os arquivos brutos simultaneamente poderia exceder o limite de memória, especialmente em ambientes conteinerizados (Docker). A abordagem incremental mantém o consumo de recursos baixo, pois realiza a leitura, limpeza e pré-agregação de cada arquivo individualmente antes da consolidação final.

### 1.3. Tratamento de Inconsistências e Limpeza de Dados

#### 1. Inconsistência: CNPJs duplicados com razões sociais diferentes

 * Decisão: Padronização pelo Cadastro Oficial (CADOP).

 * Justificativa: Notei que os arquivos financeiros frequentemente trazem nomes escritos de formas diferentes para o mesmo CNPJ (erros de digitação ou abreviações). Para corrigir isso, defini que o arquivo de Cadastros da ANS seria a referência oficial. Ao cruzar os dados, mantive apenas a Razão Social deste cadastro e descartei as variações das planilhas de despesas, garantindo que cada empresa tenha um único nome correto no sistema.

#### 2. Inconsistência: Valores zerados ou negativos

 * Decisão: Conversão Segura com preservação de negativos.

 * Justificativa: Em contabilidade, valores negativos são válidos (prejuízos ou estornos), portanto foram mantidos. Porém, células contendo texto inválido, nulos ou erros de formatação (ex: -) foram convertidos forçosamente para 0.0 para garantir a integridade das somas e evitar quebras no pipeline.

#### 3. Inconsistência: Trimestres com formatos de data inconsistentes

 * Decisão: Extração de Metadados da Estrutura de Pastas.

 * Justificativa: Como as colunas de data dentro dos CSVs variavam muito (formatos diferentes ou inexistentes), optou-se por ignorar o conteúdo da coluna de data e inferir o período (Trimestre/Ano) diretamente do nome do diretório onde o arquivo foi baixado (ex: pasta 2025/1T). Isso eliminou os erros de inconsistência.
``
### 2.1. Tratamento de CNPJs Inválidos
 * Decisão: Filtragem Rigorosa (Exclusão).

 * Justificativa: Optei por remover do pipeline qualquer registro cujo CNPJ falhasse na validação matemática (dígitos verificadores).


 * Prós: Garante 100% de integridade referencial ao realizar o cruzamento (Join) com a base cadastral (CADOP) e previne erros de inserção no Banco de Dados Relacional.


 * Contras: Existe uma perda mínima de dados caso o erro seja apenas um dígito trocado por erro humano, mas assumiu-se que dados financeiros sem identificação confiável não possuem valor analítico para este projeto.

### 2.2. Enriquecimento de Dados com Tratamento de Falhas

 * Decisão: Processamento em Memória.

 * Justificativa: Considerando que o arquivo de "Operadoras Ativas" (CADOP) possui volume reduzido e cabe confortavelmente na memória RAM, optou-se por utilizar o método otimizado pd.merge do Pandas. Essa abordagem elimina a latência de I/O de banco de dados e a complexidade de infraestrutura para este volume específico, garantindo alta performance através de operações vetorizadas.

### 2.3. Agregação com Múltiplas Estratégias
 * Decisão: Ordenação em Memória.

 * Justificativa


 * Redução de Volume: A ordenação é aplicada sobre o dataset já agregado (agrupado por Operadora/UF), o que reduz drasticamente a cardinalidade dos dados (apenas ~1 linha por Operadora/UF) em comparação ao arquivo bruto.


 * Recursos: Como o resultado final ocupa apenas alguns Kilobytes ou Megabytes, o uso da memória RAM é instantâneo e computacionalmente mais eficiente do que IO de disco ou ordenação externa.

### 3.2. Trade-off: Normalização de Dados

 * Decisão: Opção B: Tabelas normalizadas separadas.

 * Justificativa:


 * Redução de Redundância: A Razão Social e o CNPJ se repetem milhares de vezes nos lançamentos financeiros. Separar em Tabela Fato (fato_despesas) e Dimensão (dim_operadoras) economiza armazenamento.

 * Manutenibilidade: Se uma operadora mudar de nome, atualizamos apenas 1 registro na tabela de Dimensão, ao invés de milhares de linhas na tabela de despesas.

### 3.2. Trade-off: Tipos de Dados
 * Decisão: DECIMAL para Dinheiro e DATE para Datas.

 * Justificativa:


 *  Monetário: Escolhi DECIMAL(15,2) (MySQL) pois dados financeiros exigem precisão exata. O uso de FLOAT pode gerar erros de arredondamento (ponto flutuante) inaceitáveis em contabilidade.


 * Datas: Escolhi o tipo nativo DATE (YYYY-MM-DD) pois permite indexação temporal eficiente e o uso de funções nativas do banco (ex: filtrar por trimestre, ordenar cronologicamente), o que seria lento e complexo usando VARCHAR.

### 3.2. Trade-off técnico - Normalização

 * Decisão: Opção B: Tabelas normalizadas separadas.

 * Justificativa:


 * Volume de Dados: A normalização reduz o desperdício de armazenamento, evitando a repetição de textos longos (como a Razão Social e a Modalidade) em cada uma das milhares de linhas de lançamentos financeiros.


 * Frequência de Atualizações: Garante a integridade dos dados e facilita a manutenção. Caso uma operadora altere sua Razão Social, atualizamos apenas um registro na tabela de Dimensão (dim_operadoras), sem a necessidade de reescrever milhões de linhas na tabela de despesas.


 * Complexidade: Embora exija o uso de JOINS, essa estrutura organiza melhor as queries analíticas, separando claramente o que é métrica financeira (Tabela Fato) do que é atributo descritivo (Tabela Dimensão).

### 3.3. Tratamento de Inconsistências na Importação

1. Caso: Encoding incorreto (UTF-8 vs Latin-1)

 * Decisão: Estratégia de Fallback.

 * Justificativa: Arquivos governamentais legados frequentemente misturam codificações. O script foi configurado para tentar ler inicialmente em UTF-8; caso falhe, ele recorre automaticamente ao Latin-1. Isso garante que o pipeline não quebre devido a caracteres especiais.

2. Caso: Valores NULL em campos obrigatórios (Ex: CNPJ)

 * Decisão: Rejeição do Registro.

 * Justificativa: Registros sem identificadores primários (como CNPJ ou Nome da Conta) violam a integridade referencial do modelo de dados. Optou-se por descartar essas linhas silenciosamente, pois um dado financeiro "órfão" (sem dono) não possui valor analítico e poderia distorcer as contagens de operadoras.

3. Caso: Strings em campos numéricos (Ex: "-", "ND", "1.000,00")

 * Decisão: Sanitização e Conversão com Valor Padrão.

 * Justificativa:


 * Formatação: Implementou-se uma função para remover pontos e trocar vírgulas por pontos (padrão US).


 * Lixo: Células contendo texto não numérico (como traços ou notas) foram convertidas forçosamente para 0.0. Isso evita quebras de execução e assume que uma despesa não informada equivale a zero para fins de soma.

4. Caso: Datas em formatos inconsistentes

 * Decisão: Inferência via Metadados.

 * Justificativa: As colunas de data dentro dos arquivos CSVs mostraram-se não confiáveis (formatos mistos ou ausentes). A decisão foi ignorar o conteúdo da coluna de data e inferir o trimestre e ano diretamente da estrutura de pastas de onde o arquivo foi baixado (ex: pasta 2025_1T), que é uma fonte de verdade mais estável.

### 3.4. Query Analítica 

 * Decisão: Uso de Common Table Expressions.

 * Justificativa:


 * Legibilidade: Ao contrário de subqueries aninhadas (que forçam a leitura "de dentro para fora"), as CTEs permitem estruturar o código de forma linear e lógica: 1. Calcular a Média de Mercado -> 2. Comparar Operadoras -> 3. Contar Ocorrências. Isso torna o código auto-explicativo.


 * Manutenibilidade: A lógica de cálculo da "Média Geral" fica isolada em um bloco nomeado. Caso a regra de negócio mude futuramente, basta alterar a definição da CTE sem risco de quebrar a lógica de contagem final.


 * Performance: O otimizador do MySQL 8.0 consegue tratar a CTE como uma tabela temporária derivada, calculando as médias agregadas uma única vez antes de realizar o Join com a tabela fato. Isso é computacionalmente mais eficiente do que Subqueries Correlacionadas, que poderiam forçar o banco a recalcular a média para cada linha da tabela.

### 4.2.1. Escolha do Framework

 * Decisão: Opção B: FastAPI.

 * Justificativa:


 * Performance: O FastAPI utiliza o padrão ASGI, oferecendo uma performance significativamente superior ao Flask (WSGI) para operações de I/O, como as leituras de banco de dados e requisições externas realizadas neste projeto.


 * Facilidade de Manutenção: A integração nativa com o Pydantic para validação de dados elimina a necessidade de escrever validações manuais repetitivas. Além disso, o uso de Type Hints torna o código auto-documentado e mais seguro contra erros de tipo.


 * Complexidade: Embora seja um framework "micro" como o Flask, o FastAPI entrega funcionalidades "batteries-included" essenciais para APIs modernas (como geração automática de Swagger/OpenAPI), reduzindo a complexidade de desenvolvimento e documentação.

### 4.2.2. Estratégia de Paginação

 * Decisão: Opção A: Offset-based.

 * Justificativa:


 * Volume de Dados: O número de operadoras ativas é relativamente baixo. Nesse volume, o custo de performance do OFFSET no banco de dados é negligenciável.


 * Experiência do Usuário (UX): Em dashboards administrativos, é comum o usuário querer navegar para uma página específica (ex: "Ir para a Página 5"). A paginação por Offset suporta isso nativamente (Acesso Aleatório), enquanto as estratégias de Cursor/Keyset são limitadas a navegação sequencial ("Próximo/Anterior"), o que prejudicaria a usabilidade da tabela.

### 4.2.3. Cache vs Queries Diretas

 * Decisão: Opção C: Pré-calcular e armazenar em tabela.

 * Justificativa:


 * Frequência de Atualização: Os dados da ANS são atualizados apenas 4 vezes ao ano (trimestralmente). Não faz sentido recalcular métricas estáticas a cada requisição da API (Opção A).


 * Consistência e Performance: O padrão de acesso é Write-Once, Read-Many. Ao pré-calcular as estatísticas pesadas (como médias e desvios padrões) durante o pipeline de ETL e persistí-las no banco, garantimos que a API tenha latência mínima e que os dados apresentados no Dashboard sejam sempre consistentes, sem sobrecarregar o banco de dados com agregações repetitivas.

### 4.2.4. Estrutura de Resposta da API

 * Decisão: Opção B: Dados + Metadados.

 * Justificativa:


 * Usabilidade no Frontend: Para renderizar um componente de paginação funcional (ex: "Página 1 de 50"), o Frontend precisa obrigatoriamente saber o Total Geral de registros. Retornar apenas o array de dados (Opção A) deixaria a interface "cega", impedindo o cálculo do número de páginas e desabilitando a navegação direta.


 * Padronização: O uso de um envelope JSON ({ data: [], meta: {} }) separa claramente o conteúdo útil das informações de controle, facilitando a expansão futura da API sem quebrar contratos existentes.

### 4.3.1. Estratégia de Busca/Filtro

 * Decisão: Opção A: Busca no servidor.

 * Justificativa:
 

 * Performance e Escalabilidade: Carregar a lista completa de operadoras no navegador aumentaria drasticamente o tempo de carregamento inicial e o consumo de memória do dispositivo do usuário. A busca no servidor delega o processamento pesado ao banco de dados (via cláusulas WHERE otimizadas), garantindo que a interface permaneça leve mesmo se o volume de dados crescer para milhões de registros.
 

 * Consistência com Paginação: Como optamos pela paginação no servidor, a busca no cliente seria funcionalmente incorreta, pois filtraria apenas os 10 itens visíveis na página atual, e não o banco de dados inteiro.

### 4.3.2. Gerenciamento de Estado

 * Decisão: Opção A: Props/Events simples.

 * Justificativa:

 * Complexidade: A aplicação possui uma hierarquia de componentes rasa (Basicamente App -> Tabela / Filtros). Introduzir uma biblioteca de gerenciamento de estado global como Vuex ou Pinia (Opção B) adicionaria complexidade e boilerplate desnecessários para este escopo.

 * Arquitetura: O fluxo de dados é simples e unidirecional: o componente pai busca os dados na API e os passa para a tabela via props. As interações do usuário (como digitar na busca) emitem eventos (emits) de volta para o pai. Essa abordagem mantém o acoplamento baixo e o código extremamente leve.

### 4.3.4. Tratamento de Erros e Loading

 * Decisão: Feedback Visual Ativo e Mensagens Híbridas.

 * Justificativa:


 * Loading: Implementou-se uma variável de estado reativa (isLoading) que controla a exibição de um spinner e desabilita botões durante as requisições. Isso atende à heurística de "Visibilidade do Status do Sistema", prevenindo cliques repetidos e ansiedade do usuário.


 * Tratamento de Erros:


 * Decisão: Optou-se por exibir mensagens genéricas e amigáveis na interface (ex: "Não foi possível carregar os dados. Tente novamente.") para o usuário final.


 * Por quê? Exibir stack traces ou erros 500 crus expõe detalhes da infraestrutura (risco de segurança) e confunde usuários não técnicos. O erro técnico detalhado é enviado apenas para o console.error do navegador para fins de depuração do desenvolvedor.


 * Dados Vazios: O sistema diferencia explicitamente "Erro de API" de "Busca sem resultados". Caso a API retorne uma lista vazia (status 200), exibe-se um componente visual amigável ("Nenhum registro encontrado"), garantindo que o usuário saiba que o sistema funcionou corretamente.