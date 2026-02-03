/*
  ==============================================================================
  Script DDL e DML para estruturação do Data Warehouse e
  execução das queries analíticas solicitadas no teste técnico.
  ==============================================================================
*/

-- ==============================================================================
-- 1. CONFIGURAÇÃO INICIAL E DDL
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS intuitive_care_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE intuitive_care_db;

-- ------------------------------------------------------------------------------
-- 1.1 Tabela Dimensão: Operadoras (dim_operadoras)
-- Decisão de Design (Trade-off): Normalização
-- Optou-se por separar os dados cadastrais em uma tabela dimensão para evitar
-- redundância de strings (Razão Social, UF) na tabela de fatos, economizando
-- armazenamento e facilitando atualizações cadastrais.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_operadoras (
    registro_ans INT NOT NULL PRIMARY KEY,
    cnpj VARCHAR(14) NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    modalidade VARCHAR(100),
    uf CHAR(2),

    -- Índice no CNPJ para otimizar o JOIN durante o processo de ETL/Carga
    INDEX idx_cnpj (cnpj)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 1.2 Tabela Fato: Despesas (fato_despesas_consolidadas)
-- Decisão de Design (Trade-off): Tipos de Dados
-- Utilizou-se DECIMAL(15,2) para valores monetários para evitar erros de
-- precisão de ponto flutuante comuns em tipos FLOAT.
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fato_despesas_consolidadas (
    id_despesa BIGINT AUTO_INCREMENT PRIMARY KEY,
    registro_ans INT NOT NULL,
    ano INT NOT NULL,
    trimestre CHAR(2) NOT NULL, -- Ex: '1T'
    data_referencia DATE NOT NULL, -- Coluna calculada para facilitar ordenação cronológica
    valor_despesas DECIMAL(15, 2) NOT NULL,

    -- Integridade Referencial
    CONSTRAINT fk_operadora_fato
        FOREIGN KEY (registro_ans) REFERENCES dim_operadoras(registro_ans)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Índice composto: Essencial para performance em queries de Time Series
    INDEX idx_tempo (ano, trimestre)
) ENGINE=InnoDB;

-- ------------------------------------------------------------------------------
-- 1.3 Tabela Agregada: Performance (analise_agregada_uf)
-- Armazena o resultado pré-calculado do processamento Python (Requisito 2.3)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analise_agregada_uf (
    id_agregado INT AUTO_INCREMENT PRIMARY KEY,
    razao_social VARCHAR(255),
    uf CHAR(2),
    total_despesas DECIMAL(18, 2),
    media_trimestral DECIMAL(18, 2),
    desvio_padrao DECIMAL(18, 2),

    -- Índice para ordenar rapidamente os relatórios de top operadoras por estado
    INDEX idx_uf_ranking (uf, total_despesas DESC)
) ENGINE=InnoDB;


-- ==============================================================================
-- 2. QUERIES DE IMPORTAÇÃO - REQUISITO 3.3
-- ==============================================================================
-- NOTA: O comando LOAD DATA é a forma mais performática de inserir grandes volumes.
-- Os caminhos abaixo são ilustrativos e devem ser ajustados ao ambiente do servidor.

/*
-- 2.1 Carga das Operadoras
LOAD DATA INFILE '/var/lib/mysql-files/Relatorio_Cadop.csv'
INTO TABLE dim_operadoras
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(registro_ans, cnpj, razao_social, modalidade, @dummy, @dummy, uf, @dummy...);

-- 2.2 Carga das Despesas Consolidadas
LOAD DATA INFILE '/var/lib/mysql-files/consolidado_despesas.csv'
INTO TABLE fato_despesas_consolidadas
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@cnpj, @razao, trimestre, ano, valor_despesas)
SET
    registro_ans = (SELECT registro_ans FROM dim_operadoras WHERE cnpj = REPLACE(@cnpj, '.', '') LIMIT 1),
    -- Lógica para converter '1T' em Data (Dia 01 do primeiro mês do trimestre)
    data_referencia = STR_TO_DATE(CONCAT(ano, '-', SUBSTRING(trimestre, 1, 1) * 3 - 2, '-01'), '%Y-%m-%d');
*/


-- ==============================================================================
-- 3. QUERIES ANALÍTICAS AVANÇADAS - REQUISITO 3.4
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- QUERY 1: Top 5 Operadoras com maior crescimento percentual de despesas
-- (Comparativo: 1º Trimestre vs 3º Trimestre de 2025)
-- ------------------------------------------------------------------------------
SELECT
    o.razao_social,
    t1.valor_despesas AS despesas_1t,
    t3.valor_despesas AS despesas_3t,
    CAST(((t3.valor_despesas - t1.valor_despesas) / t1.valor_despesas * 100) AS DECIMAL(10,2)) AS crescimento_pct
FROM dim_operadoras o
JOIN fato_despesas_consolidadas t1
    ON o.registro_ans = t1.registro_ans AND t1.ano = 2025 AND t1.trimestre = '1T'
JOIN fato_despesas_consolidadas t3
    ON o.registro_ans = t3.registro_ans AND t3.ano = 2025 AND t3.trimestre = '3T'
WHERE t1.valor_despesas > 0 -- Evita divisão por zero
ORDER BY crescimento_pct DESC
LIMIT 5;

-- ------------------------------------------------------------------------------
-- QUERY 2: Distribuição Geográfica de Despesas
-- Retorna: Top 5 Estados com maiores gastos totais e a média por operadora.
-- ------------------------------------------------------------------------------
SELECT
    o.uf,
    SUM(f.valor_despesas) AS total_despesas_estado,
    COUNT(DISTINCT o.registro_ans) AS qtd_operadoras_atuantes,
    CAST(SUM(f.valor_despesas) / COUNT(DISTINCT o.registro_ans) AS DECIMAL(15,2)) AS media_por_operadora
FROM fato_despesas_consolidadas f
JOIN dim_operadoras o ON f.registro_ans = o.registro_ans
GROUP BY o.uf
ORDER BY total_despesas_estado DESC
LIMIT 5;

-- ------------------------------------------------------------------------------
-- QUERY 3: Operadoras com desempenho acima da média de mercado
-- Critério: Despesas > Média Geral em pelo menos 2 trimestres analisados.
-- Abordagem: Uso de CTE para legibilidade e performance.
-- ------------------------------------------------------------------------------
WITH MediaPorTrimestre AS (
    -- Passo 1: Calcular a média geral de mercado para cada período
    SELECT ano, trimestre, AVG(valor_despesas) as media_geral_mercado
    FROM fato_despesas_consolidadas
    GROUP BY ano, trimestre
),
Comparativo AS (
    -- Passo 2: Comparar cada operadora com a média do seu respectivo período
    SELECT
        f.registro_ans,
        CASE WHEN f.valor_despesas > m.media_geral_mercado THEN 1 ELSE 0 END AS superou_media
    FROM fato_despesas_consolidadas f
    JOIN MediaPorTrimestre m ON f.ano = m.ano AND f.trimestre = m.trimestre
)
-- Passo 3: Filtrar operadoras consistentes (Superaram a média em >= 2 trimestres)
SELECT
    o.razao_social,
    SUM(c.superou_media) AS qtd_trimestres_acima_media
FROM Comparativo c
JOIN dim_operadoras o ON c.registro_ans = o.registro_ans
GROUP BY o.registro_ans, o.razao_social
HAVING SUM(c.superou_media) >= 2
ORDER BY qtd_trimestres_acima_media DESC, o.razao_social ASC;