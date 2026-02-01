import sqlite3
import os
import sys

# --- IMPORTAÇÕES CORRETAS (Baseadas nos seus arquivos) ---
from src.coleta import executar_coleta
from src.processamento import executar_etl_financeiro

# Configuração do Ambiente
DIRETORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DIRETORIO_RAIZ, "intuitive_care.db")


def persistir_dados_sqlite(dataset):
    """
    Persiste os DataFrames processados no banco de dados SQLite.
    """
    if not dataset:
        print("[ERRO] O dataset está vazio. Verifique o log de processamento.")
        return

    print(f"\n--- ATUALIZANDO BANCO DE DADOS ({DB_PATH}) ---")

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)

        # Salva a tabela consolidada (Resumo/Analítica)
        # O processamento retorna um dict, usamos a chave 'operadoras_despesas'
        if 'operadoras_despesas' in dataset and not dataset['operadoras_despesas'].empty:
            dataset['operadoras_despesas'].to_sql('operadoras_despesas', conn, if_exists='replace', index=False)
            print(f"[DB] Tabela 'operadoras_despesas' atualizada com sucesso.")

        # Salva a tabela de histórico (se houver lógica diferente, aqui é igual)
        if 'historico_despesas' in dataset and not dataset['historico_despesas'].empty:
            dataset['historico_despesas'].to_sql('historico_despesas', conn, if_exists='replace', index=False)
            print(f"[DB] Tabela 'historico_despesas' atualizada com sucesso.")

    except Exception as e:
        print(f"[ERRO] Falha na persistência SQL: {e}")
    finally:
        if conn:
            conn.close()
        print("\n=== PIPELINE FINALIZADO COM SUCESSO ===")


def main():
    print("=== INICIANDO ORQUESTRADOR DE DADOS ===")

    try:
        # 1. ETAPA DE COLETA (Scraper)
        # O Docker vai baixar os arquivos da ANS aqui
        print("\n>>> [1/3] Iniciando Download dos Dados (Crawler)...")
        executar_coleta()

        # 2. ETAPA DE PROCESSAMENTO (ETL)
        # Lê os arquivos baixados, processa, limpa e gera os CSVs finais
        print("\n>>> [2/3] Iniciando Processamento (ETL)...")
        resultado_etl = executar_etl_financeiro()

        # 3. ETAPA DE PERSISTÊNCIA (Banco de Dados)
        # Pega o resultado do ETL e salva no SQLite para a API ler
        print("\n>>> [3/3] Salvando no Banco de Dados...")
        persistir_dados_sqlite(resultado_etl)

    except Exception as e:
        print(f"[CRITICAL ERROR] O pipeline foi interrompido: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()