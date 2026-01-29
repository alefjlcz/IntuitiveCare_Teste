import sqlite3
import pandas as pd
import os

# --- CONFIGURAÇÕES DE CAMINHO ---
# Isso garante que o Python encontre o banco não importa de onde você rode o script
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_ATUAL)
ARQUIVO_DB = os.path.join(DIRETORIO_RAIZ, "intuitive_care.db")


def criar_conexao():
    """
    Cria conexão com o banco de dados.

    NOTA TÉCNICA:
    O projeto utiliza SQLite para garantir a portabilidade (execução sem instalação de servidor).
    Para produção em ambiente corporativo, recomenda-se MySQL/PostgreSQL.
    Abaixo deixamos preparado o conector para MySQL (comentado).
    """

    # --- OPÇÃO ATIVA: SQLite ---
    conn = sqlite3.connect(ARQUIVO_DB)
    return conn

    # --- OPÇÃO FUTURA: MySQL (Exemplo de Implementação) ---
    # import mysql.connector
    # return mysql.connector.connect(
    #     host="localhost", user="root", password="senha", database="intuitive_care"
    # )


def preparar_banco():
    """Cria a tabela se ela ainda não existir."""
    conn = criar_conexao()
    cursor = conn.cursor()

    # Sintaxe compatível com SQLite
    query_criacao = """
                    CREATE TABLE IF NOT EXISTS operadoras_despesas \
                    ( \
                        id \
                        INTEGER \
                        PRIMARY \
                        KEY \
                        AUTOINCREMENT, \
                        razao_social \
                        TEXT, \
                        uf \
                        TEXT, \
                        total_despesas \
                        REAL, \
                        media_trimestral \
                        REAL, \
                        desvio_padrao \
                        REAL
                    ); \
                    """
    cursor.execute(query_criacao)
    conn.commit()
    conn.close()
    print("✅ Banco de dados preparado (Tabela verificada).")


def salvar_dados(df):
    """
    Recebe um DataFrame do Pandas e salva no Banco de Dados.
    Substitui os dados antigos (if_exists='replace') para evitar duplicação em testes.
    """
    if df is None or df.empty:
        print("⚠️ DataFrame vazio. Nada para salvar.")
        return

    conn = criar_conexao()

    # O Pandas faz a mágica de transformar as linhas em INSERT SQL
    df.to_sql('operadoras_despesas', conn, if_exists='replace', index=False)

    conn.close()
    print(f"💾 Sucesso! {len(df)} registros salvos no banco SQLite.")


def consultar_top_10():
    """Retorna as 10 operadoras com maiores despesas para validação."""
    conn = criar_conexao()
    query = """
            SELECT razao_social, total_despesas
            FROM operadoras_despesas
            ORDER BY total_despesas DESC LIMIT 10 \
            """
    resultado = pd.read_sql(query, conn)
    conn.close()
    return resultado