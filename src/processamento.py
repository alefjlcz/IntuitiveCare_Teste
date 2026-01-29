import pandas as pd
import os
import glob


def ler_csv_blindado(arquivo, separador=';', pular_linhas=0):
    """Lê CSV tentando UTF-8 e depois CP1252"""
    try:
        # Se for um caminho de arquivo (string)
        if isinstance(arquivo, str):
            return pd.read_csv(arquivo, sep=separador, encoding='utf-8', dtype=str, skiprows=pular_linhas)
        # Se for um objeto de arquivo (file-like)
        arquivo.seek(0)
        return pd.read_csv(arquivo, sep=separador, encoding='utf-8', dtype=str, skiprows=pular_linhas)
    except:
        if isinstance(arquivo, str):
            return pd.read_csv(arquivo, sep=separador, encoding='cp1252', dtype=str, skiprows=pular_linhas)
        arquivo.seek(0)
        return pd.read_csv(arquivo, sep=separador, encoding='cp1252', dtype=str, skiprows=pular_linhas)


def encontrar_inicio_cabecalho(caminho_arquivo):
    """Caça a linha onde começa o cabeçalho real"""
    if not os.path.exists(caminho_arquivo): return 0
    try:
        with open(caminho_arquivo, 'r', encoding='cp1252', errors='ignore') as f:
            for i, linha in enumerate(f):
                linha_upper = linha.upper()
                # Procura por colunas chave do Cadop
                if 'CNPJ' in linha_upper and ('RAZAO' in linha_upper or 'REGISTRO' in linha_upper):
                    return i
                if i > 20: break
    except:
        pass
    return 0


def processar_arquivos_zip():
    print("--- 1. INICIANDO O PROCESSO DE UNIFICAÇÃO (MERGE) ---")

    # 1. DEFINIÇÃO DE CAMINHOS (Baseado no que você me disse)
    # Pega a pasta onde está este script (src) e sobe um nível para ir à raiz
    DIRETORIO_SRC = os.path.dirname(os.path.abspath(__file__))
    DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)

    PASTA_DOWNLOADS = os.path.join(DIRETORIO_RAIZ, "downloads_ans")

    print(f"📍 Raiz do Projeto: {DIRETORIO_RAIZ}")
    print(f"📍 Pasta Downloads: {PASTA_DOWNLOADS}")

    # --- ETAPA A: PREPARAR O CADASTRO (CADOP) ---
    caminho_cadop = os.path.join(PASTA_DOWNLOADS, "Relatorio_Cadop.csv")
    df_cadastro = pd.DataFrame()

    if os.path.exists(caminho_cadop):
        print(f"📂 Lendo Cadop em: {caminho_cadop}")
        linha_cabecalho = encontrar_inicio_cabecalho(caminho_cadop)
        df_cadastro = ler_csv_blindado(caminho_cadop, pular_linhas=linha_cabecalho)

        # Padroniza colunas
        df_cadastro.columns = [str(c).strip().upper() for c in df_cadastro.columns]

        # LISTA ATUALIZADA DE NOMES POSSÍVEIS (Incluindo REGISTRO_OPERADORA)
        col_id = next(
            (c for c in ['REGISTRO_OPERADORA', 'REGISTRO_ANS', 'CD_OPERADORA', 'REG_ANS'] if c in df_cadastro.columns),
            None)
        col_cnpj = next((c for c in ['CNPJ'] if c in df_cadastro.columns), None)
        col_uf = next((c for c in ['UF', 'SG_UF'] if c in df_cadastro.columns), None)
        col_nome = next((c for c in ['RAZAO_SOCIAL', 'NM_RAZAO_SOCIAL', 'NOME_FANTASIA'] if c in df_cadastro.columns),
                        None)

        if col_id and col_cnpj:
            # Renomeia para o padrão interno
            cols_selecionadas = {col_id: 'Registro_ANS', col_cnpj: 'CNPJ'}
            if col_uf: cols_selecionadas[col_uf] = 'UF'
            if col_nome: cols_selecionadas[col_nome] = 'Razao_Social'

            df_cadastro = df_cadastro.rename(columns=cols_selecionadas)
            df_cadastro = df_cadastro[list(cols_selecionadas.values())]

            # Limpa o ID
            df_cadastro['Registro_ANS'] = df_cadastro['Registro_ANS'].astype(str).str.replace(r'\.0$', '', regex=True)
            print(f"✅ Cadastro carregado: {len(df_cadastro)} registros.")
        else:
            print(f"⚠️ ERRO: Não achei as colunas no Cadop. Disponíveis: {list(df_cadastro.columns)}")
            df_cadastro = pd.DataFrame()
    else:
        print(f"❌ Arquivo não encontrado: {caminho_cadop}")

    # --- ETAPA B: PREPARAR O FINANCEIRO ---
    print("📂 Procurando arquivos financeiros na Raiz e Downloads...")
    dfs_financeiros = []

    # Procura CSVs soltos na Raiz (consolidado_despesas, etc) ou ZIPs em Downloads
    arquivos_csv_raiz = glob.glob(os.path.join(DIRETORIO_RAIZ, "*despesas*.csv"))

    # Se achou CSVs na raiz, usa eles (Prioridade)
    if arquivos_csv_raiz:
        for arquivo in arquivos_csv_raiz:
            print(f"   -> Processando CSV: {os.path.basename(arquivo)}")
            try:
                df_temp = ler_csv_blindado(arquivo)
                df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]

                col_id_fin = next(
                    (c for c in ['REG_ANS', 'CD_OPERADORA', 'REGISTRO_OPERADORA'] if c in df_temp.columns), None)
                col_valor = next((c for c in ['VL_SALDO_FINAL', 'DESPESA', 'VALOR'] if c in df_temp.columns), None)

                if col_id_fin and col_valor:
                    temp_clean = pd.DataFrame()
                    temp_clean['Registro_ANS'] = df_temp[col_id_fin].astype(str).str.replace(r'\.0$', '', regex=True)
                    temp_clean['Total_Despesas'] = df_temp[col_valor].astype(str).str.replace('.', '',
                                                                                              regex=False).str.replace(
                        ',', '.', regex=False)
                    temp_clean['Total_Despesas'] = pd.to_numeric(temp_clean['Total_Despesas'], errors='coerce').fillna(
                        0)
                    temp_clean = temp_clean[temp_clean['Total_Despesas'] > 0]
                    dfs_financeiros.append(temp_clean)
            except Exception as e:
                print(f"Erro ao ler {arquivo}: {e}")

    # Se não achou na raiz, tenta os ZIPs na pasta downloads (Plano B)
    if not dfs_financeiros:
        import zipfile
        arquivos_zip = glob.glob(os.path.join(PASTA_DOWNLOADS, "*.zip"))
        for arquivo in arquivos_zip:
            try:
                with zipfile.ZipFile(arquivo, 'r') as z:
                    for csv_nome in z.namelist():
                        if csv_nome.endswith(".csv"):
                            with z.open(csv_nome) as f:
                                # (Mesma lógica de leitura...)
                                df_temp = ler_csv_blindado(f)
                                df_temp.columns = [str(c).strip().upper() for c in df_temp.columns]
                                col_id_fin = next((c for c in ['REG_ANS', 'CD_OPERADORA'] if c in df_temp.columns),
                                                  None)
                                col_valor = next((c for c in ['VL_SALDO_FINAL', 'DESPESA'] if c in df_temp.columns),
                                                 None)
                                if col_id_fin and col_valor:
                                    temp_clean = pd.DataFrame()
                                    temp_clean['Registro_ANS'] = df_temp[col_id_fin].astype(str).str.replace(r'\.0$',
                                                                                                             '',
                                                                                                             regex=True)
                                    temp_clean['Total_Despesas'] = df_temp[col_valor].astype(str).str.replace('.', '',
                                                                                                              regex=False).str.replace(
                                        ',', '.', regex=False)
                                    temp_clean['Total_Despesas'] = pd.to_numeric(temp_clean['Total_Despesas'],
                                                                                 errors='coerce').fillna(0)
                                    temp_clean = temp_clean[temp_clean['Total_Despesas'] > 0]
                                    dfs_financeiros.append(temp_clean)
            except:
                pass

    if not dfs_financeiros:
        print("❌ Nenhum dado financeiro encontrado (Nem na raiz, nem em ZIPs).")
        return None

    df_financeiro = pd.concat(dfs_financeiros, ignore_index=True)
    df_financeiro = df_financeiro.groupby('Registro_ANS')['Total_Despesas'].sum().reset_index()

    # --- ETAPA C: O GRANDE ENCONTRO ---
    print("🔄 Cruzando Financeiro com Cadastro...")

    if not df_cadastro.empty and 'Registro_ANS' in df_cadastro.columns:
        df_final = pd.merge(df_financeiro, df_cadastro, on='Registro_ANS', how='left')
    else:
        print("⚠️ Usando apenas dados financeiros (Cadastro falhou).")
        df_final = df_financeiro
        df_final['Razao_Social'] = 'Operadora ' + df_final['Registro_ANS']
        df_final['UF'] = 'Indefinido'
        df_final['CNPJ'] = 'Não informado'

    # Preenchimento final de segurança
    if 'Razao_Social' in df_final.columns:
        df_final['Razao_Social'] = df_final['Razao_Social'].fillna('Operadora ' + df_final['Registro_ANS'])

    for col in ['UF', 'CNPJ']:
        if col not in df_final.columns:
            df_final[col] = 'Indefinido'
        else:
            df_final[col] = df_final[col].fillna('Indefinido')

    print(f"🏁 Processamento concluído! Total: {len(df_final)}")
    return df_final