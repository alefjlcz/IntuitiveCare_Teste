-- ARQUIVO: queries_mysql.sql
-- AUTOR: Alessandro Barbosa
-- PROJETO: Teste Técnico Intuitive Care - Engenharia de Dados

-- ==============================================================================
-- 1. CONFIGURAÇÃO INICIAL (DDL) - REQUISITO 3.2
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS intuitive_care_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE intuitive_care_db;

-- 1.1 Tabela Dimensão: Operadoras (Vem do CSV do Cadop 2.2)
CREATE TABLE IF NOT EXISTS dim_operadoras (
    registro_ans INT NOT NULL PRIMARY KEY,
    cnpj VARCHAR(14) NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    modalidade VARCHAR(100),
    uf CHAR(2),

    -- Índice no CNPJ para buscas rápidas e joins futuros
    INDEX idx_cnpj (cnpj)
) ENGINE=InnoDB;

-- 1.2 Tabela Fato: Despesas Consolidadas (Vem do CSV 1.3/2.2)
CREATE TABLE IF NOT EXISTS fato_despesas_consolidadas (
    id_despesa BIGINT AUTO_INCREMENT PRIMARY KEY,
    registro_ans INT NOT NULL,  -- Chave de ligação (Foreign Key)
    ano INT NOT NULL,
    trimestre CHAR(2) NOT NULL, -- Ex: '1T'
    data_referencia DATE NOT NULL, -- Coluna calculada para ordenação (Ex: 2025-01-01)
    valor_despesas DECIMAL(15, 2) NOT NULL, -- DECIMAL para precisão financeira

    -- Integridade Referencial (Garante que a operadora existe)
    CONSTRAINT fk_operadora_fato
        FOREIGN KEY (registro_ans) REFERENCES dim_operadoras(registro_ans)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- Índice composto para performance em filtros de período
    INDEX idx_tempo (ano, trimestre)
) ENGINE=InnoDB;

-- 1.3 Tabela Agregada: Performance (Vem do CSV 2.3)
CREATE TABLE IF NOT EXISTS analise_agregada_uf (
    id_agregado INT AUTO_INCREMENT PRIMARY KEY,
    razao_social VARCHAR(255),
    uf CHAR(2),
    total_despesas DECIMAL(18, 2),
    media_trimestral DECIMAL(18, 2),
    desvio_padrao DECIMAL(18, 2),

    INDEX idx_uf_ranking (uf, total_despesas DESC)
) ENGINE=InnoDB;

-- ==============================================================================
-- 2. QUERIES DE IMPORTAÇÃO (LOAD DATA) - REQUISITO 3.3
-- ==============================================================================
-- OBS: Os caminhos dos arquivos devem ser ajustados conforme o ambiente do avaliador.

/*
-- 2.1 Carga das Operadoras
LOAD DATA INFILE '/path/to/Relatorio_Cadop.csv'
INTO TABLE dim_operadoras
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(registro_ans, cnpj, razao_social, modalidade, @dummy, @dummy, uf, @dummy...);

-- 2.2 Carga das Despesas Consolidadas
LOAD DATA INFILE '/path/to/consolidado_despesas.csv'
INTO TABLE fato_despesas_consolidadas
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(@cnpj, @razao, trimestre, ano, valor_despesas)
SET
    registro_ans = (SELECT registro_ans FROM dim_operadoras WHERE cnpj = REPLACE(@cnpj, '.', '') LIMIT 1),
    data_referencia = STR_TO_DATE(CONCAT(ano, '-', SUBSTRING(trimestre, 1, 1) * 3 - 2, '-01'), '%Y-%m-%d');

-- 2.3 Carga dos Dados Agregados
LOAD DATA INFILE '/path/to/despesas_agregadas.csv'
INTO TABLE analise_agregada_uf
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ';'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(razao_social, uf, total_despesas, media_trimestral, desvio_padrao);
*/

-- ==============================================================================
-- 3. QUERIES ANALÍTICAS AVANÇADAS - REQUISITO 3.4
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- QUERY 1: Top 5 Operadoras com maior crescimento percentual (1T2025 vs 3T2025)
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
WHERE t1.valor_despesas > 0
ORDER BY crescimento_pct DESC
LIMIT 5;

-- ------------------------------------------------------------------------------
-- QUERY 2: Distribuição por UF (Top 5 Estados e Média por Operadora)
-- ------------------------------------------------------------------------------
SELECT
    o.uf,
    SUM(f.valor_despesas) AS total_despesas_estado,
    COUNT(DISTINCT o.registro_ans) AS qtd_operadoras,
    CAST(SUM(f.valor_despesas) / COUNT(DISTINCT o.registro_ans) AS DECIMAL(15,2)) AS media_por_operadora
FROM fato_despesas_consolidadas f
JOIN dim_operadoras o ON f.registro_ans = o.registro_ans
GROUP BY o.uf
ORDER BY total_despesas_estado DESC
LIMIT 5;

-- ------------------------------------------------------------------------------
-- QUERY 3: Operadoras acima da média em pelo menos 2 trimestres (CTE)
-- ------------------------------------------------------------------------------
WITH MediaPorTrimestre AS (
    SELECT ano, trimestre, AVG(valor_despesas) as media_geral_mercado
    FROM fato_despesas_consolidadas
    GROUP BY ano, trimestre
),
Comparativo AS (
    SELECT
        f.registro_ans,
        CASE WHEN f.valor_despesas > m.media_geral_mercado THEN 1 ELSE 0 END AS acima_da_media
    FROM fato_despesas_consolidadas f
    JOIN MediaPorTrimestre m ON f.ano = m.ano AND f.trimestre = m.trimestre
)
SELECT
    o.razao_social,
    SUM(c.acima_da_media) AS qtd_trimestres_acima
FROM Comparativo c
JOIN dim_operadoras o ON c.registro_ans = o.registro_ans
GROUP BY o.registro_ans, o.razao_social
HAVING SUM(c.acima_da_media) >= 2
ORDER BY qtd_trimestres_acima DESC, o.razao_social ASC;