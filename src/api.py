from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os

# 1. CRIAÇÃO DO APP (Deve vir antes das rotas)
app = FastAPI(
    title="IntuitiveCare - Teste Alessandro",
    description="API de Consulta de Despesas - Versão Final (Requisito 4.2)",
    version="2.0"
)

# 2. CONFIGURAÇÃO DE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURAÇÃO DO BANCO ---
DIRETORIO_ATUAL = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_RAIZ = os.path.dirname(DIRETORIO_ATUAL)
ARQUIVO_DB = os.path.join(DIRETORIO_RAIZ, "intuitive_care.db")

def get_conexao():
    if not os.path.exists(ARQUIVO_DB):
        raise HTTPException(status_code=500, detail="Banco não encontrado.")
    conn = sqlite3.connect(ARQUIVO_DB)
    conn.row_factory = sqlite3.Row
    return conn

def limpar_documento(doc: str):
    return doc.replace('.', '').replace('-', '').replace('/', '').strip()

# --- ROTAS DA API ---

@app.get("/api/operadoras")
def listar_operadoras(page: int = 1, limit: int = 10, search: str = "", uf: str = ""):
    conn = get_conexao()
    cursor = conn.cursor()
    offset = (page - 1) * limit
    query_base = "FROM operadoras_despesas WHERE 1=1"
    params = []

    if search:
        term = f"%{search.strip().upper()}%"
        term_clean = f"%{limpar_documento(search)}%"
        query_base += """ AND (UPPER(Razao_Social) LIKE ? OR CAST(Registro_ANS AS TEXT) LIKE ? 
                          OR REPLACE(REPLACE(REPLACE(CNPJ, '.', ''), '/', ''), '-', '') LIKE ?)"""
        params.extend([term, term_clean, term_clean])

    if uf:
        query_base += " AND UF = ?"
        params.append(uf.upper())

    cursor.execute(f"SELECT COUNT(*) as total {query_base}", params)
    total = cursor.fetchone()["total"]
    cursor.execute(f"SELECT * {query_base} LIMIT ? OFFSET ?", params + [limit, offset])
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"data": resultados, "meta": {"page": page, "limit": limit, "total": total, "pages": (total // limit) + 1}}

@app.get("/api/operadoras/{cnpj}")
def obter_detalhes_operadora(cnpj: str):
    cnpj_limpo = limpar_documento(cnpj)
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM operadoras_despesas WHERE REPLACE(REPLACE(REPLACE(CNPJ, '.', ''), '/', ''), '-', '') = ?", (cnpj_limpo,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    return dict(row)

# CORREÇÃO DO INDENTATION ERROR: Rota de Histórico com código real
@app.get("/api/operadoras/{cnpj}/despesas")
def obter_historico_despesas(cnpj: str):
    cnpj_limpo = limpar_documento(cnpj)
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Data, Valor 
        FROM historico_despesas 
        WHERE REPLACE(REPLACE(REPLACE(CNPJ, '.', ''), '/', ''), '-', '') = ?
        ORDER BY Data DESC
    """, (cnpj_limpo,))
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return resultados

@app.get("/api/estatisticas")
def obter_estatisticas_agregadas():
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(total_despesas) as total_despesas, AVG(total_despesas) as media_despesas FROM operadoras_despesas")
    stats = dict(cursor.fetchone())
    cursor.execute("SELECT Razao_Social, CNPJ, total_despesas FROM operadoras_despesas ORDER BY total_despesas DESC LIMIT 5")
    top5 = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"total_despesas": stats["total_despesas"], "media_despesas": stats["media_despesas"], "top_5_operadoras": top5}

@app.get("/api/ufs")
def listar_ufs():
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT UF FROM operadoras_despesas WHERE UF IS NOT NULL AND UF != 'Indefinido' ORDER BY UF")
    ufs = [row["UF"] for row in cursor.fetchall()]
    conn.close()
    return ufs

@app.get("/api/estatisticas/uf")
def obter_despesas_por_uf():
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT UF as Estado, SUM(total_despesas) as total FROM operadoras_despesas WHERE UF IS NOT NULL GROUP BY UF ORDER BY total DESC LIMIT 10")
    dados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"labels": [d["Estado"] for d in dados], "values": [d["total"] for d in dados]}