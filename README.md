# Teste Técnico - IntuitiveCare (2026)

Solução de automação para coleta, processamento e análise de dados da ANS (Agência Nacional de Saúde Suplementar).

## Tecnologias Utilizadas
A solução foi desenvolvida em **Python 3.13** pois fica muito mais eficiente, também  utilizando as seguintes bibliotecas:

- requests: Para comunicação HTTP e download dos arquivos.
- beautifulsoup4: Para web scraping (navegação na estrutura de pastas do site da ANS).
- zipfile: Para manipulação de arquivos compactados diretamente em memória.
- pandas: Para análise e processamento de dados (CSV).
- openpyxl: Para suporte a arquivos Excel.

## Estrutura do Projeto
- main.py: Arquivo principal que orquestra a execução.
- src/: Pasta contendo os módulos da aplicação.
  - coleta.py: Responsável pelo crawler e download dos arquivos.
  - processamento.py: Responsável pela inspeção e leitura dos dados.
- downloads_ans/: Diretório local onde os arquivos ZIP são salvos.

## Como Executar

1. Instale as dependências:
   pip install requests pandas openpyxl beautifulsoup4

2. Execute o script principal:
   python main.py

## Decisões Técnicas (Trade-offs)

### 1. Estratégia de Coleta de Arquivos (Scraping Dinâmico vs Links Fixos)
- Abordagem Escolhida: Crawler dinâmico.
- Justificativa: Em vez de fixar links no código (hardcoding), implementei um robô que mapeia as pastas de anos (ex: 2025, 2024) e identifica automaticamente os trimestres mais recentes. Isso torna a solução resiliente a mudanças de ano ou atualizações no site da ANS sem necessidade de manutenção manual no código.

### 2. Leitura de Arquivos ZIP (Streaming vs Extração Total)
- Abordagem Escolhida: Inspeção e leitura via stream (zipfile).
- Justificativa: Optei por listar e ler o conteúdo dos arquivos ZIP diretamente pela biblioteca `zipfile` em vez de descompactar todo o conteúdo para o disco. Isso economiza espaço de armazenamento e reduz o tempo de I/O (escrita em disco), sendo uma prática mais eficiente para ambientes com recursos limitados.
- Como a pasta dowloads já está organizada, não é preciso fazer funções para 'caça' dos arquivos corretos.
### 3. Estratégia de Inspeção de Dados (Amostragem vs Carga Total)
- Abordagem Escolhida: Amostragem (`nrows=5`).
- Justificativa: Para identificar a estrutura das colunas e o formato dos dados (separadores, encoding), optei por ler apenas as primeiras 5 linhas do arquivo CSV diretamente do ZIP. Isso evita o consumo desnecessário de memória RAM e processamento que ocorreria ao carregar o arquivo inteiro apenas para verificação de metadados.
- ### 🧹 Análise Crítica e Limpeza de Dados (Item 1.3)

Durante a consolidação, foram aplicadas as seguintes regras de negócio para garantir a qualidade dos dados:

1. **Valores Zerados ou Negativos:**
   - **Problema:** O dataset original continha lançamentos contábeis com valor `0,00` ou negativos (estornos).
   - **Tratamento:** Foram filtrados e removidos. Mantive apenas registros com `ValorDespesas > 0`.
   - **Justificativa:** Para fins de análise de sinistralidade e despesas médicas, registros zerados não agregam valor estatístico e aumentam o tamanho do processamento desnecessariamente.

2. **Inconsistência de Datas:**
   - **Problema:** As datas dentro dos arquivos CSV variavam de formato ou representavam a data contábil exata (dia/mês), dificultando o agrupamento por trimestre.
   - **Tratamento:** Ignorei a coluna de data interna do arquivo e assumi o Trimestre/Ano baseando-me no **nome do arquivo original** (ex: `1T2025.zip` → 1º Trimestre de 2025).
   - **Justificativa:** O nome do arquivo, fornecido pela ANS, é uma fonte de metadados mais confiável e padronizada para o agrupamento temporal macro.

3. **Encoding de Caracteres:**
   - **Problema:** Acentos apareciam corrompidos (`ÃƒO`) ao abrir no Excel.
   - **Tratamento:** O arquivo final foi salvo utilizando encoding `utf-8-sig`.
   - **Justificativa:** Isso adiciona o BOM (Byte Order Mark), forçando o Excel a reconhecer corretamente os caracteres especiais da língua portuguesa.
-## ⚖️ Trade-off Técnico: Validação de CNPJs (Item 2.1)

Durante a etapa de validação, deparei-me com a necessidade de tratar registros com CNPJs matematicamente inválidos (dígitos verificadores incorretos).

**Estratégias consideradas:**
1. **Correção Automática:** Tentar recalcular os dígitos. *Contra:* Risco de alterar a identidade fiscal da empresa incorretamente.
2. **Flagging (Marcação):** Manter o dado mas marcar como "Suspeito". *Contra:* Polui as agregações estatísticas subsequentes.
3. **Remoção Estrita (Drop):** Descartar o registro.

**Decisão Adotada:** Remoção Estrita.
**Justificativa:** Em aplicações financeiras e contábeis reguladas pela ANS, a integridade da identificação da operadora é crítica. Um CNPJ inválido indica um erro grave na fonte ou na transmissão. Optei por garantir que 100% dos dados no pipeline final (`despesas_agregadas.csv`) sejam de entidades verificadas, garantindo confiabilidade para a análise estatística.
## 🧩 Enriquecimento de Dados (Item 2.2)

Realizei o cruzamento (Join) entre os dados financeiros e o cadastro de operadoras utilizando o **CNPJ** como chave.

**Trade-off Técnico: Estratégia de Join**
- **Estratégia:** `Left Join` (Manter a esquerda).
- **Justificativa:** O objetivo principal é analisar as despesas financeiras. O arquivo de cadastro contém apenas operadoras *Ativas*. Se eu utilizasse um `Inner Join`, perderia dados financeiros de operadoras que tiveram despesas no trimestre, mas que foram canceladas ou baixadas recentemente. Para garantir a integridade contábil, mantivemos todas as despesas e preenchemos os dados cadastrais faltantes como "Indefinido".

**Análise Crítica: Falhas de Correspondência**
- **Ocorrência:** Alguns CNPJs do arquivo financeiro não foram encontrados no cadastro.
- **Causa:** Divergência temporal (Operadoras que deixaram de ser ativas entre a data da despesa e a data do download do cadastro).
- **Tratamento:** Os campos `UF` e `Modalidade` foram preenchidos com o valor `Indefinido` para permitir o agrupamento na etapa seguinte sem descartar o valor financeiro.
- ## 📊 Agregação e Estatística (Item 2.3)

Para gerar o relatório final (`despesas_agregadas.csv`), adotei uma estratégia de agregação em dois níveis para garantir a precisão estatística.

**Metodologia de Cálculo:**
1. **Agrupamento Primário:** `(Operadora, UF, Trimestre)` -> Soma das despesas.
   * *Motivo:* Uma operadora pode ter múltiplos lançamentos contábeis dentro do mesmo trimestre. Precisamos consolidar isso primeiro para ter o "gasto do trimestre".
2. **Cálculo Final:** `(Operadora, UF)` -> Aplicação das funções `sum` (Total), `mean` (Média dos Trimestres) e `std` (Desvio Padrão).

**Trade-off Técnico: Ordenação**
- **Estratégia:** Ordenação Decrescente pelo `TotalDespesas`.
- **Justificativa:** Em análises financeiras e de auditoria, o foco principal (Princípio de Pareto) deve estar nas entidades com maior volume financeiro. Ordenar do maior para o menor facilita a identificação imediata dos maiores "players" e potenciais outliers.
---
Desenvolvido por Alessandro Barbosa