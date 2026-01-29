import pandas as pd


def realizar_etl(df):
    print("\n--- INICIANDO TRANSFORMAÇÃO (ETL) ---")

    if df is None or df.empty:
        return None

    # 1. Limpeza de Valores (1.000,00 -> 1000.00)
    coluna_valor = 'VL_SALDO_FINAL'
    if coluna_valor in df.columns:
        df[coluna_valor] = df[coluna_valor].astype(str).str.replace('.', '', regex=False).str.replace(',', '.',
                                                                                                      regex=False)
        df[coluna_valor] = pd.to_numeric(df[coluna_valor], errors='coerce').fillna(0)

    # 2. Agrupar e Somar
    df_final = df.groupby('Razao_Social')[coluna_valor].agg(
        total_despesas='sum',
        media_trimestral='mean',
        desvio_padrao='std'
    ).reset_index()

    # Ajustes finais
    df_final['uf'] = 'SP'  # UF fictícia para o teste
    df_final = df_final[df_final['total_despesas'] > 0]  # Remove quem não gastou
    df_final = df_final.round(2)

    print(f"✅ ETL Concluído! {len(df_final)} registros processados.")
    return df_final