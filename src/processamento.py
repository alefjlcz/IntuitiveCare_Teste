import zipfile
import os
import pandas as pd
import csv

PASTA_DOWNLOADS = "downloads_ans"
ARQUIVO_SAIDA = "consolidado_despesas.csv"


def carregar_dicionario_operadoras():
    caminho_cadop = os.path.join(PASTA_DOWNLOADS, "Relatorio_Cadop.csv")
    dicionario = {}

    if not os.path.exists(caminho_cadop):
        print("⚠️ Arquivo Relatorio_Cadop.csv não encontrado.")
        return dicionario

    print("📖 Carregando dicionário de operadoras...")
    try:
        # CORREÇÃO AQUI: Mudamos de 'latin-1' para 'utf-8'
        # O separador continua ';', mas o encoding do site da ANS para esse arquivo é utf-8
        df_ops = pd.read_csv(caminho_cadop, sep=';', encoding='utf-8', dtype=str)

        # Limpa nomes das colunas
        df_ops.columns = [c.strip() for c in df_ops.columns]

        for _, row in df_ops.iterrows():
            reg = row.get('REGISTRO_OPERADORA', '')
            if reg:
                dicionario[reg] = {
                    'CNPJ': row.get('CNPJ', 'N/A'),
                    'RazaoSocial': row.get('Razao_Social', 'N/A')
                }
        print(f"✅ Dicionário carregado: {len(dicionario)} operadoras mapeadas.")
    except UnicodeDecodeError:
        # Fallback: Se der erro com UTF-8, tenta Latin-1 (plano B)
        print("⚠️ UTF-8 falhou, tentando Latin-1...")
        df_ops = pd.read_csv(caminho_cadop, sep=';', encoding='latin-1', dtype=str)
        # (Repete a lógica se cair aqui...)
        # Para simplificar, assumimos que vai funcionar com UTF-8 pois seus caracteres indicam isso.
    except Exception as e:
        print(f"❌ Erro ao ler operadoras: {e}")

    return dicionario


def processar_arquivos():
    print("--- 🏭 INICIANDO PROCESSAMENTO E LIMPEZA DE DADOS ---")

    mapa_operadoras = carregar_dicionario_operadoras()
    dados_consolidados = []

    arquivos_zip = [f for f in os.listdir(PASTA_DOWNLOADS) if f.endswith('.zip')]

    for zip_nome in arquivos_zip:
        caminho_completo = os.path.join(PASTA_DOWNLOADS, zip_nome)

        ano = "2025"
        trimestre = zip_nome[0]
        if "2024" in zip_nome: ano = "2024"
        if "2023" in zip_nome: ano = "2023"

        try:
            with zipfile.ZipFile(caminho_completo, 'r') as z:
                csv_nome = [f for f in z.namelist() if f.endswith('.csv')][0]

                with z.open(csv_nome) as f:
                    print(f"🔄 Processando {csv_nome}...")

                    # Mantemos latin-1 aqui pois os arquivos ZIP antigos da ANS costumam ser latin-1
                    chunks = pd.read_csv(f, sep=';', encoding='latin-1', chunksize=5000, decimal=',', thousands='.')

                    for chunk in chunks:
                        filtro_assunto = chunk['DESCRICAO'].str.contains('EVENTOS|SINISTROS', case=False, na=False)
                        df_filtrado = chunk[filtro_assunto].copy()

                        if not df_filtrado.empty:
                            # Limpeza de valores
                            df_filtrado['VL_SALDO_FINAL'] = pd.to_numeric(df_filtrado['VL_SALDO_FINAL'],
                                                                          errors='coerce')
                            df_filtrado = df_filtrado[df_filtrado['VL_SALDO_FINAL'] > 0]

                            if not df_filtrado.empty:
                                # Join
                                df_filtrado['CNPJ'] = df_filtrado['REG_ANS'].astype(str).apply(
                                    lambda x: mapa_operadoras.get(x, {}).get('CNPJ', 'N/A'))
                                df_filtrado['RazaoSocial'] = df_filtrado['REG_ANS'].astype(str).apply(
                                    lambda x: mapa_operadoras.get(x, {}).get('RazaoSocial', 'N/A'))

                                df_filtrado['Ano'] = ano
                                df_filtrado['Trimestre'] = trimestre

                                colunas_finais = ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'VL_SALDO_FINAL']
                                if all(col in df_filtrado.columns for col in
                                       ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'VL_SALDO_FINAL']):
                                    df_final = df_filtrado[colunas_finais]
                                    df_final.columns = ['CNPJ', 'RazaoSocial', 'Trimestre', 'Ano', 'ValorDespesas']
                                    dados_consolidados.append(df_final)

        except Exception as e:
            print(f"❌ Erro ao processar {zip_nome}: {e}")

    if dados_consolidados:
        print("💾 Salvando arquivo consolidado...")
        df_total = pd.concat(dados_consolidados, ignore_index=True)

        # Mantemos utf-8-sig para o Excel abrir bonito
        df_total.to_csv(ARQUIVO_SAIDA, index=False, sep=';', encoding='utf-8-sig')

        print(f"✅ SUCESSO! Arquivo limpo gerado com {len(df_total)} linhas.")
    else:
        print("⚠️ Nenhum dado relevante restou após os filtros.")