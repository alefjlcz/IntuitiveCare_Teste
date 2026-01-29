import sqlite3
import pandas as pd
import os
from src.processamento import processar_arquivos_zip

# Configuração do Banco
DIRETORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(DIRETORIO_RAIZ, "intuitive_care.db")


def salvar_no_banco(df):
    if df is None or df.empty:
        print("❌ Nada para salvar.")
        return

    print(f"💾 Salvando {len(df)} registros no banco de dados...")
    conn = sqlite3.connect(ARQUIVO_DB)

    # Salva na tabela 'operadoras_despesas'
    # if_exists='replace' garante que recriamos a tabela com as novas colunas (CNPJ, UF)
    df.to_sql('operadoras_despesas', conn, if_exists='replace', index=False)

    conn.close()
    print("✅ Banco de dados atualizado com sucesso!")


def main():
    # 1. Executa o ETL (Extração e Tratamento)
    df_final = processar_arquivos_zip()

    # 2. Salva o resultado
    salvar_no_banco(df_final)


if __name__ == "__main__":
    main()