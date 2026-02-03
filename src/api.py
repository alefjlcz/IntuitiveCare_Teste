import sqlite3
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
app = FastAPI(
    title="Intuitive Care API - Monitoramento de Operadoras",
    description="API RESTful para consulta de despesas financeiras de operadoras de planos de saúde (Dados ANS).",
    version="1.0.0"
)

# Configuração de CORS (Permite acesso do Frontend Vue.js)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Caminhos absolutos para garantir execução via Docker ou Local
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "intuitive_care.db")


# --- MODELOS DE DADOS ---
class OperadoraSimples(BaseModel):
    """Modelo para listagem resumida na tabela principal."""
    registro_ans: str
    cnpj: str
    razao_social: str
    uf: str
    total_despesas: float


class PaginacaoResponse(BaseModel):
    """Envelope de resposta para endpoints paginados."""
    data: List[OperadoraSimples]
    meta: Dict[str, Any]


class OperadoraDetalhes(OperadoraSimples):
    """Modelo estendido com detalhes adicionais."""
    modalidade: str


class Despesa(BaseModel):
    """Modelo de histórico financeiro trimestral."""
    trimestre: str
    ano: int
    data_referencia: str
    valor: float


# --- CAMADA DE ACESSO A DADOS ---
def get_conexao_banco():
    """
    Estabelece conexão com o banco SQLite.
    Configura o row_factory para retornar resultados como dicionários.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Erro de conexão com banco de dados: {e}")


# --- ROTAS DA API ---

@app.get("/api/operadoras", response_model=PaginacaoResponse, summary="Listar Operadoras")
def listar_operadoras(
        page: int = Query(1, ge=1, description="Número da página atual"),
        limit: int = Query(10, ge=1, le=100, description="Itens por página"),
        q: Optional[str] = Query(None, description="Termo de busca"),
        field: str = Query("razao", pattern="^(razao|cnpj|uf|registro|geral)$", description="Campo de filtro"),
        sort_order: Optional[str] = Query(None, pattern="^(asc|desc)$", description="Ordenação por Total de Despesas")
):
    """
    Retorna uma lista paginada de operadoras com filtros dinâmicos e ordenação.
    """
    offset = (page - 1) * limit
    conexao = get_conexao_banco()
    cursor = conexao.cursor()

    # Construção Dinâmica da Query
    query_base = "FROM operadoras_despesas"
    params = []

    # Aplicação de Filtros (Busca)
    if q:
        if field == "cnpj":
            # Sanitiza a entrada para buscar apenas números
            q_clean = q.replace('.', '').replace('/', '').replace('-', '')
            query_base += " WHERE replace(replace(replace(CNPJ, '.', ''), '/', ''), '-', '') LIKE ?"
            params.append(f"%{q_clean}%")
        elif field == "uf":
            query_base += " WHERE UF LIKE ?"
            params.append(f"%{q}%")
        elif field == "registro":
            query_base += " WHERE Registro_ANS LIKE ?"
            params.append(f"%{q}%")
        elif field == "razao" or field == "geral":
            query_base += " WHERE Razao_Social LIKE ?"
            params.append(f"%{q}%")

    # 1. Obter Contagem Total (para a paginação no frontend)
    query_count = f"SELECT COUNT(DISTINCT CNPJ) {query_base}"
    total_registros = cursor.execute(query_count, params).fetchone()[0]

    # 2. Definir Ordenação
    order_clause = "ORDER BY Razao_Social"  # Ordenação padrão alfabética
    if sort_order == "desc":
        order_clause = "ORDER BY total_despesas DESC"
    elif sort_order == "asc":
        order_clause = "ORDER BY total_despesas ASC"

    # 3. Executar Query Principal
    # Agrupa por CNPJ para somar despesas de todos os trimestres disponíveis
    query_data = f"""
        SELECT Registro_ANS, CNPJ, Razao_Social, UF, SUM(Total_Despesas) as total_despesas 
        {query_base} 
        GROUP BY CNPJ 
        {order_clause} 
        LIMIT ? OFFSET ?
    """

    params.extend([limit, offset])
    resultados = cursor.execute(query_data, params).fetchall()
    conexao.close()

    # Formatação de Resposta
    dados_formatados = [
        {
            "registro_ans": str(row["Registro_ANS"]),
            "cnpj": row["CNPJ"],
            "razao_social": row["Razao_Social"],
            "uf": row["UF"],
            "total_despesas": row["total_despesas"]
        }
        for row in resultados
    ]

    return {
        "data": dados_formatados,
        "meta": {
            "page": page,
            "limit": limit,
            "total": total_registros,
            "sort": sort_order
        }
    }


@app.get("/api/operadoras/{cnpj}", response_model=OperadoraDetalhes, summary="Detalhes da Operadora")
def detalhes_operadora(cnpj: str):
    """
    Retorna os dados cadastrais completos e o somatório total de despesas de uma operadora específica.
    """
    conexao = get_conexao_banco()

    query = """
            SELECT Registro_ANS, CNPJ, Razao_Social, UF, Modalidade, SUM(Total_Despesas) as total_despesas
            FROM operadoras_despesas
            WHERE CNPJ = ?
            GROUP BY CNPJ \
            """

    row = conexao.execute(query, (cnpj,)).fetchone()
    conexao.close()

    if not row:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")

    return {
        "registro_ans": str(row["Registro_ANS"]),
        "cnpj": row["CNPJ"],
        "razao_social": row["Razao_Social"],
        "uf": row["UF"],
        "modalidade": row["Modalidade"],
        "total_despesas": row["total_despesas"]
    }


@app.get("/api/operadoras/{cnpj}/despesas", response_model=List[Despesa], summary="Histórico de Despesas")
def historico_despesas(cnpj: str):
    """
    Retorna a evolução temporal das despesas da operadora, agrupada por Trimestre/Ano.
    """
    conexao = get_conexao_banco()

    # O Group By garante a unicidade dos dados temporais
    query = """
            SELECT Trimestre, Ano, Data, SUM(Total_Despesas) as valor
            FROM operadoras_despesas
            WHERE CNPJ = ?
            GROUP BY Ano, Trimestre, Data
            ORDER BY Ano, Trimestre \
            """

    registros = conexao.execute(query, (cnpj,)).fetchall()
    conexao.close()

    return [
        {
            "trimestre": r["Trimestre"],
            "ano": r["Ano"],
            "data_referencia": r["Data"],
            "valor": r["valor"]
        }
        for r in registros
    ]


@app.get("/api/estatisticas", summary="KPIs e Dashboard")
def obter_estatisticas():
    """
    Retorna métricas agregadas para o Dashboard:
    - Total Geral de Despesas
    - Média por Trimestre
    - Top 5 Operadoras
    - Top 5 Estados com maiores gastos
    """
    conexao = get_conexao_banco()
    cursor = conexao.cursor()

    # KPIs Gerais
    total = cursor.execute("SELECT SUM(Total_Despesas) FROM operadoras_despesas").fetchone()[0] or 0
    media = cursor.execute("SELECT AVG(Total_Despesas) FROM operadoras_despesas").fetchone()[0] or 0

    # Query 1: Top 5 Operadoras com maior volume financeiro
    top_5_ops = cursor.execute("""
                               SELECT Razao_Social as nome, CNPJ as cnpj, SUM(Total_Despesas) as valor
                               FROM operadoras_despesas
                               GROUP BY CNPJ
                               ORDER BY valor DESC LIMIT 5
                               """).fetchall()

    # Query 2: Distribuição Geográfica (Top 5 Estados)
    uf_stats = cursor.execute("""
                              SELECT UF as nome, SUM(Total_Despesas) as valor
                              FROM operadoras_despesas
                              GROUP BY UF
                              ORDER BY valor DESC LIMIT 5
                              """).fetchall()

    conexao.close()

    return {
        "total_geral": total,
        "media_trimestral": media,
        "top_operadoras": [{"nome": r["nome"], "cnpj": r["cnpj"], "valor": r["valor"]} for r in top_5_ops],
        "distribuicao_uf": [{"nome": r["nome"], "valor": r["valor"]} for r in uf_stats]
    }