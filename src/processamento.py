import pandas as pd
import os
import glob


def ler_csv_blindado(arquivo, separador=';', pular_linhas=0):
    """Lê CSV tentando UTF-8 e depois CP1252 para evitar erros de acento."""
    try:
        if isinstance(arquivo, str):
            return pd.read_csv(arquivo, sep=separador, encoding='utf-8', dtype=str, skiprows=pular_linhas)
        arquivo.seek(0)
        return pd.read_csv(arquivo, sep=separador, encoding='utf-8', dtype=str, skiprows=pular_linhas)
    except:
        if isinstance(arquivo, str):
            return pd.read_csv(arquivo, sep=separador, encoding='cp1252', dtype=str, skiprows=pular_linhas)
        arquivo.seek(0)
        return pd.read_csv(arquivo, sep=separador, encoding='cp1252', dtype=str, skiprows=pular_linhas)


def processar_arquivos_zip():
    print("--- 1. INICIANDO O PROCESSO DE UNIFICAÇÃO E HISTÓRICO ---")

    DIRETORIO_SRC = os.path.dirname(os.path.abspath(__file__))
    DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)
    PASTA_DOWNLOADS = os.path.join(DIRETORIO_RAIZ, "downloads_ans")

    # --- ETAPA A: PREPARAR O CADASTRO (CADOP) ---
    caminho_cadop = os.path.join(PASTA_DOWNLOADS, "Relatorio_Cadop.csv")
    df_cadastro = pd.DataFrame()

    if os.path.exists(caminho_cadop):
        print(f"📂 Lendo Cadop em: {caminho_cadop}")
        # Lê o cadastro (Relatorio_Cadop)
        df_cadastro = ler_csv_blindado(caminho_cadop)
        df_cadastro.columns = [str(c).strip().upper() for c in df_cadastro.columns]

        # Identifica as colunas conforme o seu log
        col_id = next((c for c in ['REGISTRO_OPERADORA', 'REGISTRO_ANS', 'CD_OPERADORA'] if c in df_cadastro.columns),
                      None)
        col_cnpj = next((c for c in ['CNPJ'] if c in df_cadastro.columns), None)
        col_uf = next((c for c in ['UF', 'SG_UF'] if c in df_cadastro.columns), None)
        col_nome = next((c for c in ['RAZAO_SOCIAL', 'RAZAOSOCIAL', 'NM_RAZAO_SOCIAL'] if c in df_cadastro.columns),
                        None)

        if col_id and col_cnpj:
            df_cadastro = df_cadastro[[col_id, col_cnpj, col_uf, col_nome]].copy()
            df_cadastro.rename(
                columns={col_id: 'Registro_ANS', col_cnpj: 'CNPJ', col_uf: 'UF', col_nome: 'Razao_Social'},
                inplace=True)
            df_cadastro['Registro_ANS'] = df_cadastro['Registro_ANS'].astype(str).str.replace(r'\.0$', '', regex=True)
            print(f"✅ Cadastro carregado: {len(df_cadastro)} registros.")
        else:
            print(f"⚠️ ERRO no Cadop. Colunas: {list(df_cadastro.columns)}")

    # --- ETAPA B: PREPARAR O HISTÓRICO (CONSOLIDADO_DESPESAS.CSV) ---
    caminho_consolidado = os.path.join(DIRETORIO_RAIZ, "consolidado_despesas.csv")

    if not os.path.exists(caminho_consolidado):
        print(f"❌ Arquivo de histórico não encontrado na raiz: {caminho_consolidado}")
        return None

    print(f"   -> Processando Histórico: consolidado_despesas.csv")
    df_hist = ler_csv_blindado(caminho_consolidado)
    df_hist.columns = [str(c).strip().upper() for c in df_hist.columns]

    # MAPEAMENTO BASEADO NO SEU LOG: ['CNPJ', 'RAZAOSOCIAL', 'TRIMESTRE', 'ANO', 'VALORDESPESAS']
    col_id_h = next((c for c in ['CNPJ', 'REG_ANS', 'REGISTRO_OPERADORA'] if c in df_hist.columns), None)
    col_trimestre = next((c for c in ['TRIMESTRE'] if c in df_hist.columns), None)
    col_ano = next((c for c in ['ANO'] if c in df_hist.columns), None)
    col_valor = next((c for c in ['VALORDESPESAS', 'VL_SALDO_FINAL', 'VALOR'] if c in df_hist.columns), None)

    if not col_id_h or not col_valor:
        print(f"❌ Colunas essenciais não encontradas. Disponíveis: {list(df_hist.columns)}")
        return None

    # Limpeza e Padronização do Histórico
    df_hist_clean = pd.DataFrame()
    df_hist_clean['CNPJ'] = df_hist[col_id_h].astype(str).str.replace(r'\.0$', '', regex=True)

    # Cria a coluna de Data combinando Trimestre e Ano
    if col_trimestre and col_ano:
        df_hist_clean['Data'] = df_hist[col_trimestre] + "/" + df_hist[col_ano]
    else:
        df_hist_clean['Data'] = "Período Único"

    # Converte valor
    df_hist_clean['Valor'] = df_hist[col_valor].astype(str).str.replace('.', '', regex=False).str.replace(',', '.',
                                                                                                          regex=False)
    df_hist_clean['Valor'] = pd.to_numeric(df_hist_clean['Valor'], errors='coerce').fillna(0)

    # --- ETAPA C: CRUZAMENTO (MERGE) ---
    print("🔄 Cruzando Financeiro com Cadastro...")

    if not df_cadastro.empty:
        # Tabela de histórico (já tem CNPJ, então batemos por ele)
        df_historico_final = df_hist_clean.copy()

        # Resumo para a tabela principal (soma total por CNPJ)
        df_resumo_fin = df_hist_clean.groupby('CNPJ')['Valor'].sum().reset_index()
        df_resumo_fin.rename(columns={'Valor': 'Total_Despesas'}, inplace=True)

        # Junta com o cadastro para ter Razao_Social, UF e Registro_ANS
        df_resumo_final = pd.merge(df_resumo_fin, df_cadastro, on='CNPJ', how='left')
    else:
        # Fallback caso não tenha cadastro
        df_resumo_final = df_hist_clean.groupby('CNPJ')['Valor'].sum().reset_index()
        df_resumo_final.rename(columns={'Valor': 'Total_Despesas'}, inplace=True)
        df_resumo_final['Razao_Social'] = 'Operadora ' + df_resumo_final['CNPJ']
        df_resumo_final['UF'] = 'Indefinido'
        df_historico_final = df_hist_clean

    print(f"🏁 Processamento concluído! Total: {len(df_resumo_final)} operadoras.")

    return {
        "resumo": df_resumo_final,
        "historico": df_historico_final
    }