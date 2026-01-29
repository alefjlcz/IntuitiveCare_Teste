import sqlite3
import pandas as pd
import os
from src.processamento import processar_arquivos_zip

# Configuração do caminho do banco (na raiz do projeto)
DIRETORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_DB = os.path.join(DIRETORIO_RAIZ, "intuitive_care.db")


def salvar_no_banco(dados):
    """
    Recebe o dicionário com 'resumo' e 'historico' e grava no SQLite.
    """
    if dados is None:
        print("❌ Falha no processamento. Nada a salvar.")
        return

    print(f"💾 Salvando dados no banco: {ARQUIVO_DB}...")

    try:
        conn = sqlite3.connect(ARQUIVO_DB)

        # 1. Salva a tabela principal (Dashboard/Lista)
        # O 'replace' garante que a tabela seja recriada com as colunas corretas (CNPJ, UF, etc)
        dados['resumo'].to_sql('operadoras_despesas', conn, if_exists='replace', index=False)
        print(f"   ✅ Tabela 'operadoras_despesas' atualizada ({len(dados['resumo'])} registros).")

        # 2. Salva a tabela de histórico detalhado (Requisito 4.3)
        dados['historico'].to_sql('historico_despesas', conn, if_exists='replace', index=False)
        print(f"   ✅ Tabela 'historico_despesas' atualizada ({len(dados['historico'])} registros).")

        conn.close()
        print("\n✨ Tudo pronto! O banco de dados está sincronizado.")

    except Exception as e:
        print(f"❌ Erro ao salvar no banco: {e}")


def main():
    print("=== INICIANDO PIPELINE DE DADOS (ETL) ===\n")

    # 1. Executa o processamento que unifica Cadop e Financeiro
    # Agora lidando com a coluna REGISTRO_OPERADORA identificada no seu log
    resultado = processar_arquivos_zip()

    # 2. Persiste os dados no banco SQLite
    salvar_no_banco(resultado)


if __name__ == "__main__":
    main()