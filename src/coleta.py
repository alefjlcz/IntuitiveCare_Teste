import requests
from bs4 import BeautifulSoup
import os

# --- CONFIGURAÇÕES ---
URL_CONTABIL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"
URL_CADASTRO = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/"
PASTA_DOWNLOADS = "downloads_ans"


def baixar_arquivo(url, nome_arquivo):
    """Baixa um arquivo específico."""
    caminho_completo = os.path.join(PASTA_DOWNLOADS, nome_arquivo)

    if os.path.exists(caminho_completo):
        print(f"⚠️ Arquivo já existe: {nome_arquivo}")
        return

    print(f"⬇️ Baixando: {nome_arquivo}...")
    try:
        resposta = requests.get(url, timeout=60)
        if resposta.status_code == 200:
            with open(caminho_completo, 'wb') as f:
                f.write(resposta.content)
            print("✅ Sucesso!")
        else:
            print(f"❌ Erro {resposta.status_code} ao baixar.")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")


def listar_anos_disponiveis():
    """Descobre os anos disponíveis na ANS."""
    print("🔎 Mapeando anos...")
    try:
        resposta = requests.get(URL_CONTABIL, timeout=30)
        soup = BeautifulSoup(resposta.text, 'html.parser')
        anos = []
        for link in soup.find_all('a'):
            texto = link.get('href')
            if texto and texto.replace('/', '').isdigit() and len(texto.replace('/', '')) == 4:
                anos.append(texto.replace('/', ''))
        anos.sort(reverse=True)
        return anos
    except Exception as e:
        print(f"❌ Erro ao listar anos: {e}")
        return []


def buscar_arquivos_no_ano(ano):
    """Busca arquivos ZIP dentro da pasta do ano."""
    url_ano = URL_CONTABIL + f"{ano}/"
    print(f"📂 Verificando ano {ano}...")
    try:
        resposta = requests.get(url_ano, timeout=30)
        soup = BeautifulSoup(resposta.text, 'html.parser')
        arquivos = []
        for link in soup.find_all('a'):
            nome = link.get('href')
            if nome and nome.lower().endswith('.zip'):
                arquivos.append((url_ano + nome, nome))
        return arquivos
    except:
        return []


def baixar_cadastral():
    """
    BAIXA A LISTA DE OPERADORAS (O 'DICIONÁRIO').
    Isso é necessário para descobrirmos o CNPJ e o Nome a partir do REG_ANS.
    """
    print("\n🔎 Procurando arquivo de Operadoras Ativas...")
    try:
        resposta = requests.get(URL_CADASTRO, timeout=30)
        soup = BeautifulSoup(resposta.text, 'html.parser')

        # Procura o arquivo CSV dentro da página
        for link in soup.find_all('a'):
            nome = link.get('href')
            # Geralmente chama Relatorio_Cadop.csv ou algo assim
            if nome and nome.lower().endswith('.csv'):
                url_completa = URL_CADASTRO + nome
                # Vamos salvar com um nome padrão para facilitar
                baixar_arquivo(url_completa, "Relatorio_Cadop.csv")
                return

        print("⚠️ Não achei o CSV de operadoras. Verifique o site.")

    except Exception as e:
        print(f"❌ Erro ao baixar cadastral: {e}")


def robo_inteligente():
    print("--- 🤖 INICIANDO ROBÔ COMPLETO ---")
    if not os.path.exists(PASTA_DOWNLOADS):
        os.makedirs(PASTA_DOWNLOADS)

    # 1. Baixa os dados contábeis (O que já fizemos)
    anos = listar_anos_disponiveis()
    candidatos = []
    for ano in anos:
        arquivos = buscar_arquivos_no_ano(ano)
        arquivos.sort(key=lambda x: x[1], reverse=True)
        candidatos.extend(arquivos)
        if len(candidatos) >= 3:
            break

    top_3 = candidatos[:3]
    print(f"\n🏆 Arquivos contábeis selecionados: {[f[1] for f in top_3]}")
    for url, nome in top_3:
        baixar_arquivo(url, nome)

    # 2. NOVO: Baixa o arquivo de cadastro (O Dicionário)
    baixar_cadastral()

    print("\n✅ Coleta Finalizada!")