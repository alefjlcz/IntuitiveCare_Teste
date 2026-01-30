import sqlite3
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

app = FastAPI(title="Intuitive Care API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "intuitive_care.db")


# --- MODELOS ---
class OperadoraSimples(BaseModel):
    registro_ans: str
    cnpj: str
    razao_social: str
    uf: str
    total_despesas: float  # NOVO CAMPO


class PaginacaoResponse(BaseModel):
    data: List[OperadoraSimples]
    meta: Dict[str, Any]


class OperadoraDetalhes(OperadoraSimples):
    modalidade: str


class Despesa(BaseModel):
    trimestre: str
    ano: int
    data_referencia: str
    valor: float


# --- CONEXÃO ---
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --- ROTAS ---

@app.get("/api/operadoras", response_model=PaginacaoResponse)
def listar_operadoras(
        page: int = Query(1, ge=1),
        limit: int = Query(10, ge=1, le=100),
        q: Optional[str] = Query(None),
        field: str = Query("razao", pattern="^(razao|cnpj|uf|registro|geral)$"),
        sort_order: Optional[str] = Query(None, pattern="^(asc|desc)$")  # NOVO: Ordenação
):
    offset = (page - 1) * limit
    conn = get_db_connection()
    cursor = conn.cursor()

    # Base da Query
    query_base = "FROM operadoras_despesas"
    params = []

    # Filtros
    if q:
        if field == "cnpj":
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

    # Contagem Total
    query_count = f"SELECT COUNT(DISTINCT CNPJ) {query_base}"
    total = cursor.execute(query_count, params).fetchone()[0]

    # ORDENAÇÃO (Lógica Nova)
    order_clause = "ORDER BY Razao_Social"  # Padrão
    if sort_order == "desc":
        order_clause = "ORDER BY total_despesas DESC"
    elif sort_order == "asc":
        order_clause = "ORDER BY total_despesas ASC"

    # Query Principal com Soma
    # Calculamos o SUM(Total_Despesas) aqui para exibir na tabela
    query_data = f"""
        SELECT Registro_ANS, CNPJ, Razao_Social, UF, SUM(Total_Despesas) as total_despesas 
        {query_base} 
        GROUP BY CNPJ 
        {order_clause} 
        LIMIT ? OFFSET ?
    """

    params.extend([limit, offset])
    rows = cursor.execute(query_data, params).fetchall()
    conn.close()

    dados_formatados = []
    for row in rows:
        dados_formatados.append({
            "registro_ans": str(row["Registro_ANS"]),
            "cnpj": row["CNPJ"],
            "razao_social": row["Razao_Social"],
            "uf": row["UF"],
            "total_despesas": row["total_despesas"]
        })

    return {
        "data": dados_formatados,
        "meta": {"page": page, "limit": limit, "total": total, "sort": sort_order}
    }


@app.get("/api/operadoras/{cnpj}", response_model=OperadoraDetalhes)
def detalhes_operadora(cnpj: str):
    conn = get_db_connection()
    # Pega detalhes + soma total
    row = conn.execute("""
                       SELECT Registro_ANS, CNPJ, Razao_Social, UF, Modalidade, SUM(Total_Despesas) as total_despesas
                       FROM operadoras_despesas
                       WHERE CNPJ = ?
                       GROUP BY CNPJ
                       """, (cnpj,)).fetchone()
    conn.close()
    if not row: raise HTTPException(404, "Não encontrado")

    return {
        "registro_ans": str(row["Registro_ANS"]),
        "cnpj": row["CNPJ"],
        "razao_social": row["Razao_Social"],
        "uf": row["UF"],
        "modalidade": row["Modalidade"],
        "total_despesas": row["total_despesas"]
    }


@app.get("/api/operadoras/{cnpj}/despesas", response_model=List[Despesa])
def historico_despesas(cnpj: str):
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT Trimestre, Ano, Data, Total_Despesas as valor FROM operadoras_despesas WHERE CNPJ = ? ORDER BY Ano, Trimestre",
        (cnpj,)).fetchall()
    conn.close()
    return [{"trimestre": r["Trimestre"], "ano": r["Ano"], "data_referencia": r["Data"], "valor": r["valor"]} for r in
            rows]


@app.get("/api/estatisticas")
def obter_estatisticas():
    conn = get_db_connection()
    cursor = conn.cursor()

    total = cursor.execute("SELECT SUM(Total_Despesas) FROM operadoras_despesas").fetchone()[0] or 0
    media = cursor.execute("SELECT AVG(Total_Despesas) FROM operadoras_despesas").fetchone()[0] or 0

    top_10 = cursor.execute("""
                            SELECT Razao_Social as nome, CNPJ as cnpj, SUM(Total_Despesas) as valor
                            FROM operadoras_despesas
                            GROUP BY CNPJ
                            ORDER BY valor DESC LIMIT 10
                            """).fetchall()

    uf_stats = cursor.execute("""
                              SELECT UF as nome, SUM(Total_Despesas) as valor
                              FROM operadoras_despesas
                              GROUP BY UF
                              ORDER BY valor DESC
                              """).fetchall()

    conn.close()

    return {
        "total_geral": total,
        "media_trimestral": media,
        "top_operadoras": [{"nome": r["nome"], "cnpj": r["cnpj"], "valor": r["valor"]} for r in top_10],
        "distribuicao_uf": [{"nome": r["nome"], "valor": r["valor"]} for r in uf_stats]
    }