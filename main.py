import sqlite3
import os
import sys
# Importa a função renomeada
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

    try:
        conn = sqlite3.connect(DB_PATH)

        # Persistência da tabela consolidada
        dataset['resumo'].to_sql('operadoras_despesas', conn, if_exists='replace', index=False)
        print(f"[DB] Tabela 'operadoras_despesas' atualizada.")

        # Persistência da tabela de histórico
        dataset['historico'].to_sql('historico_despesas', conn, if_exists='replace', index=False)
        print(f"[DB] Tabela 'historico_despesas' atualizada.")

    except Exception as e:
        print(f"[ERRO] Falha na persistência SQL: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
        print("\n=== PIPELINE FINALIZADO COM SUCESSO ===")


def main():
    print("=== INICIANDO ORQUESTRADOR DE DADOS ===")

    # Execução do ETL (Extract, Transform, Load)
    try:
        resultado_etl = executar_etl_financeiro()

        # Persistência
        persistir_dados_sqlite(resultado_etl)

    except Exception as e:
        print(f"[CRITICAL ERROR] O pipeline foi interrompido: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()