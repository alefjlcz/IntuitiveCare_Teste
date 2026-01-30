import os
import requests
import zipfile
import io
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

# Configuração de SSL
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# --- CONFIGURAÇÕES DE AMBIENTE ---
URL_FONTE_CADOP = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"
URL_BASE_DEMONSTRACOES = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"

DIR_DOWNLOADS = "downloads_ans"
DIR_EXTRAIDOS = os.path.join(DIR_DOWNLOADS, "arquivos_extraidos")
DIR_BAIXADOS = os.path.join(DIR_DOWNLOADS, "arquivos_baixados")

# Headers para simular requisição de navegador (Bypass em proteções simples)
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def inicializar_estrutura_pastas():
    """Cria a hierarquia de diretórios necessária para o projeto."""
    for diretorio in [DIR_DOWNLOADS, DIR_EXTRAIDOS, DIR_BAIXADOS]:
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)


def extrair_links_pagina(url):
    """Faz o parse da página HTML e retorna lista de recursos disponíveis."""
    try:
        response = requests.get(url, verify=False, timeout=15, headers=HTTP_HEADERS)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        return [
            a['href'] for a in soup.find_all('a')
            if 'Parent' not in a.text and '?C=' not in a['href']
        ]
    except Exception as e:
        print(f"[ERRO] Falha ao acessar {url}: {e}")
        return []


def identificar_periodos_recentes(qtd=3):
    """Identifica os trimestres mais recentes disponíveis no servidor."""
    print("[INFO] Mapeando disponibilidade de dados no servidor...")
    anos_disponiveis = extrair_links_pagina(URL_BASE_DEMONSTRACOES)
    # Filtra apenas diretórios numéricos (anos)
    anos = sorted(
        [a.replace('/', '') for a in anos_disponiveis if a.replace('/', '').isdigit()],
        reverse=True
    )

    alvos_coleta = []

    for ano in anos:
        url_ano = URL_BASE_DEMONSTRACOES + ano + "/"
        recursos = extrair_links_pagina(url_ano)

        # Filtra recursos que contenham 'T' (Trimestre) e o ano corrente
        candidatos = [i for i in recursos if 'T' in i.upper() and ano in i]
        candidatos.sort(reverse=True)

        for item in candidatos:
            periodo = item.replace('/', '').replace('.zip', '')

            # Evita duplicatas (Zip vs Pasta)
            if any(a['periodo'] == periodo for a in alvos_coleta):
                continue

            alvos_coleta.append({
                "periodo": periodo,
                "url_origem": url_ano + item,
                "is_zip": item.lower().endswith('.zip')
            })

            if len(alvos_coleta) >= qtd:
                return alvos_coleta

    return alvos_coleta


def realizar_download_extrair(alvo):
    """Baixa e extrai os dados de um período específico."""
    dir_destino = os.path.join(DIR_EXTRAIDOS, alvo['periodo'])

    # Verificação de idempotência (Skip if exists)
    if os.path.exists(dir_destino) and os.listdir(dir_destino):
        print(f"[SKIP] Dados de {alvo['periodo']} já existem localmente.")
        return

    if not os.path.exists(dir_destino):
        os.makedirs(dir_destino)

    url_recurso = alvo['url_origem']

    # Se o alvo for um diretório, precisamos encontrar o arquivo .zip dentro dele
    if not alvo['is_zip']:
        arquivos = extrair_links_pagina(alvo['url_origem'])
        zips = [x for x in arquivos if x.endswith('.zip')]
        if zips:
            url_recurso += zips[0]
        else:
            print(f"[AVISO] Nenhum arquivo compactado encontrado em {alvo['periodo']}")
            return

    print(f"[DOWNLOAD] Iniciando transferência: {alvo['periodo']}...")
    try:
        response = requests.get(url_recurso, verify=False, stream=True, headers=HTTP_HEADERS)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                z.extractall(dir_destino)
            print(f"   [OK] Extração concluída em {dir_destino}")
        else:
            print(f"   [ERRO] HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"   [ERRO] Exceção durante download: {e}")


def baixar_cadop():
    """Realiza o download do relatório de cadastro de operadoras."""
    arquivo_destino = os.path.join(DIR_BAIXADOS, "Relatorio_Cadop.csv")

    if os.path.exists(arquivo_destino) and os.path.getsize(arquivo_destino) > 0:
        print(f"[SKIP] Relatório CADOP já existente.")
        return

    print(f"[DOWNLOAD] Baixando Relatório CADOP...")
    try:
        response = requests.get(URL_FONTE_CADOP, verify=False, headers=HTTP_HEADERS)
        if response.status_code == 200:
            with open(arquivo_destino, 'wb') as f:
                f.write(response.content)
            print("[OK] CADOP atualizado com sucesso.")
        else:
            print(f"[ERRO] Falha no download do CADOP. Status: {response.status_code}")
    except Exception as e:
        print(f"[ERRO] Exceção no CADOP: {e}")


def executar_coleta():
    print("=== INICIANDO MÓDULO DE COLETA DE DADOS (CRAWLER) ===")
    inicializar_estrutura_pastas()

    # Fase 1: Dados Financeiros
    alvos = identificar_periodos_recentes()
    print(f"[INFO] Períodos identificados: {[a['periodo'] for a in alvos]}")

    for alvo in alvos:
        realizar_download_extrair(alvo)

    # Fase 2: Dados Cadastrais
    baixar_cadop()

    print("\n=== COLETA FINALIZADA ===")


if __name__ == "__main__":
    executar_coleta()