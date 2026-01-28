-- =============================================================================
-- TESTE 3: BANCO DE DADOS E ANÁLISE SQL
-- =============================================================================

/* --- JUSTIFICATIVAS TÉCNICAS (Trade-offs) ---

   1. Normalização vs Desnormalização:
      Optei por uma abordagem HÍBRIDA.
      - Tabela 'operadoras_cadastral': Normalizada. Dados cadastrais mudam pouco e ocupam espaço se repetidos.
      - Tabela 'despesas_trimestrais': Desnormalizada (Star Schema). Focada em performance de leitura
        para evitar muitos JOINs em queries de agregação massiva.

      Justificativa: Como o volume de dados da ANS é médio/alto e a frequência de atualização é trimestral,
      priorizei a performance de consulta analítica.

   2. Tipos de Dados Monetários:
      Escolha: DECIMAL(15, 2)
      Justificativa: FLOAT/DOUBLE podem ter erros de precisão em cálculos financeiros.
      DECIMAL garante a precisão exata dos centavos, essencial para relatórios contábeis.
*/

-- =============================================================================
-- 3.2 DDL - CRIAÇÃO DAS TABELAS
-- =============================================================================

CREATE TABLE IF NOT EXISTS operadoras_cadastral (
    registro_ans INT PRIMARY KEY,
    razao_social VARCHAR(255),
    cnpj VARCHAR(20),
    uf CHAR(2)
);

CREATE TABLE IF NOT EXISTS despesas_trimestrais (
    id INT AUTO_INCREMENT PRIMARY KEY,
    registro_ans INT,
    trimestre VARCHAR(10), -- Ex: '1T2023'
    data_referencia DATE,
    valor_despesa DECIMAL(15, 2),
    FOREIGN KEY (registro_ans) REFERENCES operadoras_cadastral(registro_ans)
);

-- Index para acelerar busca por trimestre e operadora
CREATE INDEX idx_tempo ON despesas_trimestrais(data_referencia);
CREATE INDEX idx_operadora ON despesas_trimestrais(registro_ans);

-- =============================================================================
-- 3.4 QUERIES ANALÍTICAS
-- =============================================================================

-- QUERY 1: Quais as 5 operadoras com maior crescimento percentual de despesas
-- entre o primeiro e o último trimestre analisado?
WITH despesas_inicio AS (
    SELECT registro_ans, SUM(valor_despesa) as total_ini
    FROM despesas_trimestrais
    WHERE trimestre = '1T2023' -- Exemplo do primeiro trimestre
    GROUP BY registro_ans
),
despesas_fim AS (
    SELECT registro_ans, SUM(valor_despesa) as total_fim
    FROM despesas_trimestrais
    WHERE trimestre = '3T2023' -- Exemplo do último trimestre
    GROUP BY registro_ans
)
SELECT
    c.razao_social,
    ((f.total_fim - i.total_ini) / i.total_ini) * 100 as crescimento_pct
FROM despesas_inicio i
JOIN despesas_fim f ON i.registro_ans = f.registro_ans
JOIN operadoras_cadastral c ON i.registro_ans = c.registro_ans
ORDER BY crescimento_pct DESC
LIMIT 5;

-- QUERY 2: Distribuição de despesas por UF e Média por operadora
SELECT
    c.uf,
    SUM(d.valor_despesa) as total_despesas_estado,
    AVG(d.valor_despesa) as media_por_lancamento
FROM despesas_trimestrais d
JOIN operadoras_cadastral c ON d.registro_ans = c.registro_ans
GROUP BY c.uf
ORDER BY total_despesas_estado DESC
LIMIT 5;

-- QUERY 3: Operadoras com despesas acima da média em pelo menos 2 trimestres
WITH media_geral_trimestre AS (
    SELECT trimestre, AVG(valor_despesa) as media_mercado
    FROM despesas_trimestrais
    GROUP BY trimestre
),
performance_operadora AS (
    SELECT
        d.registro_ans,
        d.trimestre,
        d.valor_despesa,
        m.media_mercado,
        CASE WHEN d.valor_despesa > m.media_mercado THEN 1 ELSE 0 END as acima_media
    FROM despesas_trimestrais d
    JOIN media_geral_trimestre m ON d.trimestre = m.trimestre
)
SELECT
    c.razao_social,
    SUM(p.acima_media) as trimestres_acima_media
FROM performance_operadora p
JOIN operadoras_cadastral c ON p.registro_ans = c.registro_ans
GROUP BY c.razao_social
HAVING trimestres_acima_media >= 2;