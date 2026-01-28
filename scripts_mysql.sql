-- =============================================================================
-- TESTE 3: BANCO DE DADOS E ANÁLISE SQL (Completo)
-- =============================================================================

/* =============================================================================
   3.2 e 3.3 - JUSTIFICATIVAS TÉCNICAS E ANÁLISE CRÍTICA (Respondendo ao PDF)
   =============================================================================

   [A] TRADE-OFF: NORMALIZAÇÃO (Opção B Escolhida)
       Optei por separar os dados em duas tabelas: 'operadoras_cadastral' e 'despesas_trimestrais'.
       - Motivo 1 (Manutenibilidade): Dados cadastrais (Razão Social, UF) mudam pouco. Se a operadora mudar de nome, atualizo em apenas 1 lugar.
       - Motivo 2 (Performance): A tabela de despesas fica mais leve (menos colunas de texto repetido), acelerando as queries de soma.

   [B] TRADE-OFF: TIPOS DE DADOS
       - Monetário: Usei DECIMAL(15, 2).
         Justificativa: Tipos FLOAT/DOUBLE introduzem erros de arredondamento em ponto flutuante.
         Para dados contábeis da ANS, a precisão exata dos centavos é obrigatória.
       - Datas: Usei DATE.
         Justificativa: Não é necessário armazenar hora/minuto (TIMESTAMP) para dados de balanço trimestral.

   [C] ANÁLISE CRÍTICA DA IMPORTAÇÃO (Tratamento de Inconsistências)
       Conforme solicitado no item 3.3, identifiquei os seguintes problemas nos CSVs brutos:
       1. Strings em campos numéricos (ex: "1.234,56").
       2. Valores NULL/Vazios em chaves primárias.
       3. Codificação de texto (Latin1 vs UTF-8).

       SOLUÇÃO ADOTADA: Pipeline de ETL em Python.
       Em vez de importar "lixo" para o banco e tentar limpar com SQL, utilizei o Pandas (Python) para:
       - Converter vírgulas para pontos.
       - Remover operadoras sem identificação.
       - Gerar um CSV limpo e padronizado ('despesas_agregadas.csv') pronto para carga.
*/

-- =============================================================================
-- DDL - ESTRUTURAÇÃO DAS TABELAS
-- =============================================================================

CREATE TABLE IF NOT EXISTS operadoras_cadastral (
    registro_ans INT PRIMARY KEY COMMENT 'Código único da operadora (PK)',
    razao_social VARCHAR(255),
    cnpj VARCHAR(20),
    uf CHAR(2)
);

CREATE TABLE IF NOT EXISTS despesas_trimestrais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registro_ans INT,
    trimestre VARCHAR(10) COMMENT 'Ex: 1T2023',
    data_referencia DATE,
    valor_despesa DECIMAL(15, 2) COMMENT 'Precisão monetária garantida',
    FOREIGN KEY (registro_ans) REFERENCES operadoras_cadastral(registro_ans)
);

CREATE INDEX idx_analise_temporal ON despesas_trimestrais(data_referencia);
CREATE INDEX idx_analise_geo ON operadoras_cadastral(uf);

-- =============================================================================
-- 3.4 QUERIES ANALÍTICAS
-- =============================================================================

-- QUERY 1: Top 5 operadoras com maior crescimento (%) entre 1º e Último Trimestre
-- Desafio: Operadoras podem não ter dados em todos os trimestres.
-- Solução: Utilizei INNER JOIN para considerar apenas operadoras que existem em AMBOS os períodos,
-- garantindo que o cálculo de crescimento seja matemático e justo.
WITH despesas_inicio AS (
    SELECT registro_ans, SUM(valor_despesa) as total_ini
    FROM despesas_trimestrais
    WHERE trimestre = '1T2023'
    GROUP BY registro_ans
),
despesas_fim AS (
    SELECT registro_ans, SUM(valor_despesa) as total_fim
    FROM despesas_trimestrais
    WHERE trimestre = '3T2023'
    GROUP BY registro_ans
)
SELECT
    c.razao_social,
    CONCAT(ROUND(((f.total_fim - i.total_ini) / i.total_ini) * 100, 2), '%') as crescimento_pct
FROM despesas_inicio i
JOIN despesas_fim f ON i.registro_ans = f.registro_ans
JOIN operadoras_cadastral c ON i.registro_ans = c.registro_ans
ORDER BY ((f.total_fim - i.total_ini) / i.total_ini) DESC
LIMIT 5;

-- QUERY 2: Top 5 Estados com maiores despesas e Média por Operadora
-- Desafio: Calcular agregado (Soma) e média granular na mesma query.
SELECT
    c.uf,
    SUM(d.valor_despesa) as total_despesas_estado,
    AVG(d.valor_despesa) as media_por_lancamento
FROM despesas_trimestrais d
JOIN operadoras_cadastral c ON d.registro_ans = c.registro_ans
GROUP BY c.uf
ORDER BY total_despesas_estado DESC
LIMIT 5;

-- QUERY 3: Operadoras acima da média em 2+ trimestres
-- Trade-off: Utilizei CTEs (Common Table Expressions) para legibilidade, dividindo o problema
-- em "Calcular Média do Mercado" -> "Comparar Operadora" -> "Contar Ocorrências".
WITH media_mercado AS (
    SELECT trimestre, AVG(valor_despesa) as media_geral
    FROM despesas_trimestrais
    GROUP BY trimestre
),
performance AS (
    SELECT
        d.registro_ans,
        CASE WHEN d.valor_despesa > m.media_geral THEN 1 ELSE 0 END as superou_media
    FROM despesas_trimestrais d
    JOIN media_mercado m ON d.trimestre = m.trimestre
)
SELECT
    c.razao_social,
    SUM(p.superou_media) as trimestres_acima_da_media
FROM performance p
JOIN operadoras_cadastral c ON p.registro_ans = c.registro_ans
GROUP BY c.razao_social
HAVING trimestres_acima_da_media >= 2;