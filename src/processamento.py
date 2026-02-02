import pandas as pd
import os
import glob
import zipfile
import re

# --- CONSTANTES E CONFIGURAÇÕES ---
DIRETORIO_SRC = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_SRC)

PATH_ENTRADA_BRUTA = os.path.join(DIRETORIO_RAIZ, "downloads_ans", "arquivos_extraidos")
PATH_ENTRADA_CADOP = os.path.join(DIRETORIO_RAIZ, "downloads_ans", "arquivos_baixados")
PATH_SAIDA_PROCESSADA = os.path.join(DIRETORIO_RAIZ, "planilhas_processadas")


def inicializar_diretorios():
    """Garante a existência dos diretórios de saída."""
    if not os.path.exists(PATH_SAIDA_PROCESSADA):
        os.makedirs(PATH_SAIDA_PROCESSADA)


def gerenciar_conflito_arquivo(diretorio, nome_base, extensao=".zip"):
    """
    Versão Docker-Friendly: Sobrescreve automaticamente sem perguntar.
    """
    caminho_completo = os.path.join(diretorio, nome_base + extensao)

    if os.path.exists(caminho_completo):
        print(f"   [INFO] O arquivo '{nome_base}{extensao}' já existe e será atualizado.")

    return caminho_completo


def validar_digitos_cnpj(cnpj):
    """Validação aritmética do CNPJ."""
    cnpj = re.sub(r'\D', '', str(cnpj))
    if len(cnpj) != 14 or len(set(cnpj)) == 1: return False
    for i in range(12, 14):
        peso = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        if i == 12: peso = peso[1:]
        soma = sum(int(a) * b for a, b in zip(cnpj[:i], peso))
        resto = soma % 11
        digito = 0 if resto < 2 else 11 - resto
        if int(cnpj[i]) != digito: return False
    return True


def converter_valor_monetario(valor):
    if pd.isna(valor): return 0.0
    try:
        return float(str(valor).replace('.', '').replace(',', '.'))
    except:
        return 0.0


def sanitizar_id_ans(valor):
    return re.sub(r'\D', '', str(valor).split('.')[0]).strip()


def ler_arquivo_csv(caminho_arquivo):
    configs = [
        {'sep': ';', 'encoding': 'utf-8'},
        {'sep': ';', 'encoding': 'latin1'},
        {'sep': ',', 'encoding': 'utf-8'}
    ]
    for cfg in configs:
        try:
            df = pd.read_csv(caminho_arquivo, sep=cfg['sep'], encoding=cfg['encoding'], dtype=str)
            if len(df.columns) > 1: return df
        except:
            continue
    return pd.DataFrame()


def carregar_dados_cadastrais():
    print("[ETAPA] Carregando CADOP...", end=" ")
    arquivo = os.path.join(PATH_ENTRADA_CADOP, "Relatorio_Cadop.csv")
    if not os.path.exists(arquivo): return pd.DataFrame()

    df = ler_arquivo_csv(arquivo)
    if df.empty: return pd.DataFrame()

    df.columns = [c.strip().upper() for c in df.columns]

    col_reg = next((c for c in df.columns if c in ['REGISTRO_OPERADORA', 'REGISTRO_ANS', 'CD_OPERADORA']), None)
    col_cnpj = next((c for c in df.columns if 'CNPJ' in c), None)
    col_razao = next((c for c in df.columns if 'RAZAO' in c), None)
    col_modalidade = next((c for c in df.columns if 'MODALIDADE' in c), None)
    col_uf = next((c for c in df.columns if c in ['UF', 'SG_UF']), None)

    if col_reg and col_cnpj and col_razao:
        df['PK_Registro_ANS'] = df[col_reg].apply(sanitizar_id_ans)
        df_final = df[[
            'PK_Registro_ANS', col_cnpj, col_razao,
            col_modalidade if col_modalidade else col_reg,
            col_uf if col_uf else col_reg
        ]].copy()
        df_final.columns = ['PK_Registro_ANS', 'CNPJ', 'RazaoSocial', 'Modalidade', 'UF']
        df_final = df_final.drop_duplicates(subset=['PK_Registro_ANS'])
        print(f"Sucesso ({len(df_final)} registros).")
        return df_final
    return pd.DataFrame()


def gerar_relatorio_agregado_2_3(df_detalhado):
    """
    Implementa o Requisito 2.3: Agregação, Estatística e Ordenação.
    """
    print("\n[ETAPA 2.3] Gerando Relatório Agregado (Estatísticas)...")

    if df_detalhado.empty:
        print("[AVISO] Dataset vazio, pulando agregação.")
        return

    # Agrupamento e cálculo de métricas
    df_agg = df_detalhado.groupby(['RazaoSocial', 'UF'])['ValorDespesas'].agg(
        Total_Despesas='sum',
        Media_Trimestral='mean',
        Desvio_Padrao='std'
    ).reset_index()

    df_agg['Desvio_Padrao'] = df_agg['Desvio_Padrao'].fillna(0.0)
    df_agg = df_agg.sort_values(by='Total_Despesas', ascending=False)

    print(
        f"   [INFO] Agregação concluída. Top 1: {df_agg.iloc[0]['RazaoSocial']} (R$ {df_agg.iloc[0]['Total_Despesas']:,.2f})")

    caminho_zip = gerenciar_conflito_arquivo(PATH_SAIDA_PROCESSADA, "Teste_Alessandro_Barbosa", ".zip")

    print(f"[EXPORT] Salvando Agregado em: {caminho_zip}")
    df_agg.to_csv(
        caminho_zip,
        index=False,
        sep=';',
        encoding='utf-8-sig',
        decimal=',',
        compression=dict(method='zip', archive_name='despesas_agregadas.csv')
    )


def executar_etl_financeiro():
    inicializar_diretorios()
    df_cadastro = carregar_dados_cadastrais()

    print("\n--- INICIANDO PROCESSAMENTO FINANCEIRO ---")
    arquivos = glob.glob(os.path.join(PATH_ENTRADA_BRUTA, "**", "*.csv"), recursive=True) + \
               glob.glob(os.path.join(PATH_ENTRADA_BRUTA, "**", "*.CSV"), recursive=True)

    lista_dfs = []

    for arquivo in arquivos:
        nome_pasta = os.path.basename(os.path.dirname(arquivo))
        if 'T' not in nome_pasta.upper(): continue

        df = ler_arquivo_csv(arquivo)
        if df.empty: continue
        df.columns = [c.strip().upper() for c in df.columns]

        col_reg = next((c for c in df.columns if c in ['REG_ANS', 'CD_OPERADORA', 'REGISTRO_OPERADORA']), None)
        col_conta = next((c for c in df.columns if c in ['CD_CONTA', 'CD_CONTA_CONTABIL', 'CONTA']), None)
        col_valor = next((c for c in df.columns if c in ['VL_SALDO_FINAL', 'VALOR', 'SALDO']), None)

        if col_reg and col_conta and col_valor:
            df_filtrado = df[df[col_conta].str.startswith('4', na=False)].copy()
            if df_filtrado.empty: continue

            temp = pd.DataFrame()
            temp['PK_Registro_ANS'] = df_filtrado[col_reg].apply(sanitizar_id_ans)

            # Garante que lê o trimestre corretamente (case insensitive)
            try:
                temp['Trimestre'] = nome_pasta.upper().split('T')[0] + 'T'
                temp['Ano'] = nome_pasta.upper().split('T')[1]
            except:
                temp['Trimestre'] = 'ND';
                temp['Ano'] = 'ND'

            temp['ValorDespesas'] = df_filtrado[col_valor].apply(converter_valor_monetario)

            temp_agrupado = temp.groupby(['PK_Registro_ANS', 'Trimestre', 'Ano'])['ValorDespesas'].sum().reset_index()
            lista_dfs.append(temp_agrupado)
            print(f"   [OK] Processado: {os.path.basename(arquivo)}")

    if not lista_dfs: return None

    df_consolidado = pd.concat(lista_dfs, ignore_index=True)

    if not df_cadastro.empty:
        df_final = pd.merge(df_consolidado, df_cadastro, on='PK_Registro_ANS', how='left')
        df_final['RazaoSocial'] = df_final['RazaoSocial'].fillna('DESCONHECIDA')
        df_final['Modalidade'] = df_final['Modalidade'].fillna('ND')
        df_final['UF'] = df_final['UF'].fillna('BR')
    else:
        df_final = df_consolidado
        for c in ['CNPJ', 'RazaoSocial', 'Modalidade', 'UF']: df_final[c] = 'N/A'

    # Validação (2.1)
    df_final['CNPJ_Limpo'] = df_final['CNPJ'].astype(str).str.replace(r'\D', '', regex=True)
    df_validos = df_final[df_final['CNPJ_Limpo'].apply(validar_digitos_cnpj)].copy()

    print(f"[INFO] Registros Validados: {len(df_validos)}")

    # Gera relatórios
    gerar_relatorio_agregado_2_3(df_validos)

    caminho_cons = gerenciar_conflito_arquivo(PATH_SAIDA_PROCESSADA, "consolidado_despesas", ".zip")
    df_validos[['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']].to_csv(
        caminho_cons, index=False, sep=';', encoding='utf-8-sig',
        compression=dict(method='zip', archive_name='consolidado_despesas.csv')
    )
    print(f"[EXPORT] Consolidado Detalhado: {caminho_cons}")

    # --- PREPARAÇÃO PARA O BANCO (COM CORREÇÃO DE DUPLICATAS) ---
    df_banco = df_validos.rename(
        columns={'ValorDespesas': 'Total_Despesas', 'RazaoSocial': 'Razao_Social', 'PK_Registro_ANS': 'Registro_ANS'})

    if not df_banco.empty:
        df_banco['Data'] = df_banco['Trimestre'] + '/' + df_banco['Ano']

        # 1. Ordena para garantir que a seleção seja consistente
        df_banco = df_banco.sort_values(by=['Registro_ANS', 'Ano', 'Trimestre'])

        # 2. REMOVE DUPLICATAS: Garante apenas 1 linha por Operadora/Trimestre/Ano
        # Isso corrige o bug de "linhas repetidas" no modal do frontend
        linhas_antes = len(df_banco)
        df_banco = df_banco.drop_duplicates(subset=['Registro_ANS', 'Ano', 'Trimestre'], keep='first')
        linhas_depois = len(df_banco)

        if linhas_antes != linhas_depois:
            print(f"   [FIX] Removidas {linhas_antes - linhas_depois} linhas duplicadas antes de salvar no banco.")

    return {"operadoras_despesas": df_banco, "historico_despesas": df_banco}