import pandas as pd
import os
import re

# --- CONFIGURAÇÕES DE CAMINHOS ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_ATUAL)

ARQUIVO_ENTRADA = os.path.join(DIRETORIO_RAIZ, "consolidado_despesas.csv")
ARQUIVO_CADASTRO = os.path.join(DIRETORIO_RAIZ, "downloads_ans", "Relatorio_Cadop.csv")
ARQUIVO_FINAL = os.path.join(DIRETORIO_RAIZ, "despesas_agregadas.csv")


def validar_cnpj_matematica(cnpj):
    """Valida CNPJ (Módulo 11)"""
    cnpj = re.sub(r'\D', '', str(cnpj))
    if len(cnpj) != 14 or len(set(cnpj)) == 1: return False

    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(d) * p for d, p in zip(cnpj[:12], pesos1))
    r = soma % 11
    d1 = 0 if r < 2 else 11 - r
    if int(cnpj[12]) != d1: return False

    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(d) * p for d, p in zip(cnpj[:13], pesos2))
    r = soma % 11
    d2 = 0 if r < 2 else 11 - r
    if int(cnpj[13]) != d2: return False

    return True


def enriquecer_dados(df_financeiro):
    """Parte 2.2: Join com cadastro"""
    print("\n--- 🔗 ENRIQUECIMENTO (JOIN) ---")

    if not os.path.exists(ARQUIVO_CADASTRO):
        return df_financeiro

    cadop = pd.read_csv(ARQUIVO_CADASTRO, sep=';', encoding='utf-8', dtype={'CNPJ': str})
    cadop.columns = [c.strip() for c in cadop.columns]

    # Seleção de colunas para o Join
    colunas_interesse = ['CNPJ', 'REGISTRO_OPERADORA', 'Modalidade', 'UF']
    if not all(col in cadop.columns for col in colunas_interesse):
        return df_financeiro

    cadop_reduzido = cadop[colunas_interesse].copy()
    cadop_reduzido.rename(columns={'REGISTRO_OPERADORA': 'RegistroANS'}, inplace=True)

    # Left Join
    df_enriquecido = pd.merge(df_financeiro, cadop_reduzido, on='CNPJ', how='left')

    # Preenchimento de falhas
    df_enriquecido.fillna({'UF': 'Indefinido', 'Modalidade': 'Indefinido', 'RegistroANS': '000000'}, inplace=True)

    return df_enriquecido


def agregar_dados(df):
    """
    Parte 2.3: Agregação Estatística
    Calcula Soma Total, Média Trimestral e Desvio Padrão.
    """
    print("\n--- 📊 AGREGAÇÃO E ESTATÍSTICA (PARTE 2.3) ---")

    # 1. Agrupamento Intermediário (Por Trimestre)
    # Precisamos somar tudo que aconteceu num trimestre antes de tirar a média entre trimestres.
    print("1. Calculando totais por trimestre...")
    df_trimestral = df.groupby(['RazaoSocial', 'UF', 'Trimestre'])['ValorDespesas'].sum().reset_index()

    # 2. Agrupamento Final (Estatísticas Gerais)
    print("2. Calculando métricas finais (Média e Desvio Padrão)...")
    # 'sum' -> Soma das despesas de todos os trimestres
    # 'mean' -> Média dos valores trimestrais (E não média de cada notinha fiscal)
    # 'std' -> Desvio padrão entre os trimestres
    df_final = df_trimestral.groupby(['RazaoSocial', 'UF'])['ValorDespesas'].agg(['sum', 'mean', 'std']).reset_index()

    # Renomeando para ficar bonito no arquivo final
    df_final.columns = ['RazaoSocial', 'UF', 'TotalDespesas', 'MediaTrimestral', 'DesvioPadrao']

    # Arredondamento para 2 casas decimais
    df_final = df_final.round(2)

    # Tratamento: Se só tem 1 trimestre, o desvio padrão vem NaN. Trocamos por 0.0
    df_final['DesvioPadrao'] = df_final['DesvioPadrao'].fillna(0.0)

    # 3. Ordenação (Do Maior Gastador para o Menor)
    print("3. Ordenando rankings...")
    df_final = df_final.sort_values(by='TotalDespesas', ascending=False)

    return df_final


def executar_transformacao():
    print("--- ⚙️ PIPELINE COMPLETO DE TRANSFORMAÇÃO ---")

    # 1. Carrega
    if not os.path.exists(ARQUIVO_ENTRADA):
        print(f"❌ Erro: {ARQUIVO_ENTRADA} não encontrado.")
        return

    print("📥 Carregando dados...")
    df = pd.read_csv(ARQUIVO_ENTRADA, sep=';', encoding='utf-8-sig', dtype={'CNPJ': str})

    # 2. Valida
    print("🛡️ Validando dados...")
    df = df.dropna(subset=['RazaoSocial'])
    df = df[df['RazaoSocial'].str.strip() != '']
    df['ValorDespesas'] = pd.to_numeric(df['ValorDespesas'], errors='coerce')
    df = df[df['ValorDespesas'] > 0]
    df['CNPJ_Valido'] = df['CNPJ'].apply(validar_cnpj_matematica)
    df = df[df['CNPJ_Valido']].copy()

    # 3. Enriquece
    df_enriquecido = enriquecer_dados(df)

    # 4. Agrega (NOVO!)
    df_final = agregar_dados(df_enriquecido)

    # 5. Salva
    print(f"\n💾 Salvando arquivo final em: {ARQUIVO_FINAL}")
    df_final.to_csv(ARQUIVO_FINAL, index=False, sep=';', encoding='utf-8-sig')
    print(f"✅ SUCESSO! {len(df_final)} operadoras consolidadas.")

    # Mostra o TOP 3 para você conferir
    print("\n🏆 TOP 3 MAIORES DESPESAS:")
    print(df_final.head(3).to_string())


if __name__ == "__main__":
    executar_transformacao()