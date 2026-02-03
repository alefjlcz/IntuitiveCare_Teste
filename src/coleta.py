import os
import requests
import zipfile
import io
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

# Necessário pois muitos servidores governamentais possuem cadeias de certificados incompletas.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# --- CONFIGURAÇÕES DE AMBIENTE ---
URL_FONTE_CADOP = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"
URL_BASE_DEMONSTRACOES = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis/"

# Definição de caminhos relativos para garantir portabilidade (Docker/Local)
DIR_DOWNLOADS = "downloads_ans"
DIR_EXTRAIDOS = os.path.join(DIR_DOWNLOADS, "arquivos_extraidos")
DIR_BAIXADOS = os.path.join(DIR_DOWNLOADS, "arquivos_baixados")

# Headers para simular um navegador real e evitar bloqueios de WAF (Web Application Firewall) simples
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}


def inicializar_estrutura_pastas():
    """
    Cria a hierarquia de diretórios necessária para o armazenamento dos dados brutos.
    Garante que as pastas existam antes de qualquer tentativa de I/O.
    """
    for diretorio in [DIR_DOWNLOADS, DIR_EXTRAIDOS, DIR_BAIXADOS]:
        if not os.path.exists(diretorio):
            os.makedirs(diretorio)


def extrair_links_pagina(url):
    """
    Realiza o parsing de uma página de diretório Apache/FTP HTTP.

    Args:
        url (str): A URL do diretório a ser listado.

    Returns:
        list: Lista de strings contendo os hrefs (links) encontrados.
              Retorna lista vazia em caso de erro de conexão.
    """
    try:
        # Timeout definido para evitar hang em conexões instáveis
        response = requests.get(url, verify=False, timeout=15, headers=HTTP_HEADERS)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Filtra links de navegação do servidor ('Parent Directory', ordenação, etc)
        return [
            a['href'] for a in soup.find_all('a')
            if 'Parent' not in a.text and '?C=' not in a['href']
        ]
    except Exception as e:
        print(f"[ERRO] Falha ao acessar índice do diretório {url}: {e}")
        return []


def identificar_periodos_recentes(qtd_trimestres=3):
    """
    Navega na estrutura de pastas da ANS para identificar os trimestres mais recentes.
    Lógica: Lista anos -> Ordena Decrescente -> Entra no ano -> Busca Trimestres.

    Args:
        qtd_trimestres (int): Quantidade de trimestres a serem coletados (Padrão: 3).

    Returns:
        list[dict]: Lista de dicionários contendo metadados dos alvos (url, periodo, tipo).
    """
    print("[INFO] Mapeando disponibilidade de dados no servidor (Crawler)...")

    anos_disponiveis = extrair_links_pagina(URL_BASE_DEMONSTRACOES)

    # Filtra apenas diretórios numéricos (anos) e ordena do mais recente para o antigo
    anos = sorted(
        [a.replace('/', '') for a in anos_disponiveis if a.replace('/', '').isdigit()],
        reverse=True
    )

    alvos_coleta = []

    for ano in anos:
        url_ano = URL_BASE_DEMONSTRACOES + ano + "/"
        recursos = extrair_links_pagina(url_ano)

        # Filtra recursos que contenham 'T' (indicativo de Trimestre) no nome
        candidatos = [i for i in recursos if 'T' in i.upper() and ano in i]
        candidatos.sort(reverse=True)

        for item in candidatos:
            periodo = item.replace('/', '').replace('.zip', '')

            # Evita duplicatas (O servidor pode listar tanto a pasta quanto o zip do mesmo período)
            if any(a['periodo'] == periodo for a in alvos_coleta):
                continue

            alvos_coleta.append({
                "periodo": periodo,
                "url_origem": url_ano + item,
                "is_zip": item.lower().endswith('.zip')
            })

            # Critério de Parada: Já encontramos a quantidade desejada
            if len(alvos_coleta) >= qtd_trimestres:
                return alvos_coleta

    return alvos_coleta


def realizar_download_extrair(alvo):
    """
    Baixa o arquivo compactado e extrai diretamente em memória (Stream).

    Args:
        alvo (dict): Dicionário contendo 'url_origem' e 'periodo'.
    """
    dir_destino = os.path.join(DIR_EXTRAIDOS, alvo['periodo'])

    # Verificação de Idempotência: Se já baixou e extraiu, pula para economizar banda/tempo
    if os.path.exists(dir_destino) and os.listdir(dir_destino):
        print(f"[SKIP] Dados de {alvo['periodo']} já existem localmente.")
        return

    if not os.path.exists(dir_destino):
        os.makedirs(dir_destino)

    url_recurso = alvo['url_origem']

    # Lógica para tratar diretórios que não são links diretos para o ZIP
    if not alvo['is_zip']:
        arquivos = extrair_links_pagina(alvo['url_origem'])
        zips = [x for x in arquivos if x.endswith('.zip')]
        if zips:
            url_recurso += zips[0]
        else:
            print(f"[AVISO] Nenhum arquivo compactado encontrado dentro de {alvo['periodo']}")
            return

    print(f"[DOWNLOAD] Iniciando transferência: {alvo['periodo']}...")
    try:
        # stream=True permite baixar arquivos grandes sem carregar tudo na RAM de uma vez
        response = requests.get(url_recurso, verify=False, stream=True, headers=HTTP_HEADERS)

        if response.status_code == 200:
            # io.BytesIO permite tratar o download como um arquivo em memória,
            # evitando criar um .zip temporário no disco antes de extrair.
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                z.extractall(dir_destino)
            print(f"   [OK] Extração concluída em: {dir_destino}")
        else:
            print(f"   [ERRO] HTTP Status inválido: {response.status_code}")

    except Exception as e:
        print(f"   [ERRO] Exceção durante download/extração: {e}")


def baixar_cadop():
    """
    Realiza o download do Relatório de Informações Cadastrais das Operadoras (CADOP).
    Este arquivo é essencial para o enriquecimento dos dados financeiros.
    """
    arquivo_destino = os.path.join(DIR_BAIXADOS, "Relatorio_Cadop.csv")

    # Verifica se o arquivo já existe e não está vazio (bytes > 0)
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
        print(f"[ERRO] Exceção ao baixar CADOP: {e}")


def executar_coleta():
    """
    Função orquestradora do processo de coleta.
    """
    print("=== INICIANDO MÓDULO DE COLETA DE DADOS ===")
    inicializar_estrutura_pastas()

    # Identificação e Download dos Dados Financeiros (Demonstrações Contábeis)
    alvos = identificar_periodos_recentes()
    print(f"[INFO] Períodos identificados para download: {[a['periodo'] for a in alvos]}")

    for alvo in alvos:
        realizar_download_extrair(alvo)

    # Download dos Dados Cadastrais
    baixar_cadop()

    print("\n=== COLETA FINALIZADA ===")


if __name__ == "__main__":
    executar_coleta()