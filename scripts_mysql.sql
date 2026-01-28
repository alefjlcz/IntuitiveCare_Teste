-- SCRIPT SQL PARA MYSQL 8.0
-- Este arquivo atende ao requisito 3 do teste: "Scripts SQL compatíveis com MySQL 8.0"

-- 1. Criação da Tabela
-- Diferença para SQLite: Usamos AUTO_INCREMENT e VARCHAR definido
CREATE TABLE IF NOT EXISTS operadoras_despesas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    razao_social VARCHAR(255),
    uf CHAR(2),
    total_despesas DECIMAL(15, 2),
    media_trimestral DECIMAL(15, 2),
    desvio_padrao DECIMAL(15, 2)
);

-- 2. Carga de Dados
-- Em produção MySQL, usaríamos LOAD DATA INFILE.
-- Exemplo do comando:
/*
LOAD DATA INFILE '/var/lib/mysql-files/despesas_agregadas.csv'
INTO TABLE operadoras_despesas
FIELDS TERMINATED BY ';'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(razao_social, uf, total_despesas, media_trimestral, desvio_padrao);
*/

-- 3. Queries Analíticas (Solicitadas no Teste)

-- A. Top 10 Operadoras com maiores despesas
SELECT razao_social, total_despesas
FROM operadoras_despesas
ORDER BY total_despesas DESC
LIMIT 10;

-- B. Despesas totais por Estado (UF)
SELECT uf, SUM(total_despesas) as total_estado
FROM operadoras_despesas
GROUP BY uf
ORDER BY total_estado DESC;