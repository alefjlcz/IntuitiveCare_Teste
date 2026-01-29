from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os

app = FastAPI(
    title="IntuitiveCare - Teste Alessandro",
    description="API Avançada com Busca Híbrida e Filtros",
    version="1.3"
)

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
        raise HTTPException(status_code=500, detail="Banco não encontrado. Execute 'python main.py' primeiro.")
    conn = sqlite3.connect(ARQUIVO_DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/api/ufs")
def listar_ufs():
    """Lista UFs para o filtro"""
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT DISTINCT UF FROM operadoras_despesas WHERE UF IS NOT NULL AND UF != 'Indefinido' ORDER BY UF")
    ufs = [row["UF"] for row in cursor.fetchall()]
    conn.close()
    return ufs


@app.get("/api/estatisticas/uf")
def obter_despesas_por_uf():
    """Dados para o Gráfico"""
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT UF as Estado, SUM(total_despesas) as total
                   FROM operadoras_despesas
                   WHERE UF IS NOT NULL
                     AND UF != 'Indefinido'
                   GROUP BY UF
                   ORDER BY total DESC
                       LIMIT 10
                   """)
    dados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {
        "labels": [d["Estado"] for d in dados],
        "values": [d["total"] for d in dados]
    }


@app.get("/api/operadoras")
def listar_operadoras(search: str = "", uf: str = "", page: int = 1, limit: int = 10):
    conn = get_conexao()
    cursor = conn.cursor()
    offset = (page - 1) * limit

    query_base = "FROM operadoras_despesas WHERE 1=1"
    params = []

    if search:
        term = search.strip().upper()

        # 1. Tenta limpar o termo para busca de CNPJ (remove ., - e /)
        # Isso permite que se o user digitar "04.201", vire "04201" para comparar
        term_clean = term.replace('.', '').replace('-', '').replace('/', '')

        # Prepara os termos para o LIKE
        term_like = f"%{term}%"  # Para Nome (com formatação original)
        term_clean_like = f"%{term_clean}%"  # Para CNPJ e Registro (apenas números)

        # A query verifica:
        # 1. Nome (Razao Social)
        # 2. Registro ANS
        # 3. CNPJ (Aqui usamos REPLACE para limpar a coluna do banco na hora da comparação)
        query_base += """ AND (
            UPPER(Razao_Social) LIKE ? 
            OR CAST(Registro_ANS AS TEXT) LIKE ?
            OR REPLACE(REPLACE(REPLACE(CNPJ, '.', ''), '/', ''), '-', '') LIKE ?
        )"""

        params.extend([term_like, term_clean_like, term_clean_like])

    if uf:
        query_base += " AND UF = ?"
        params.append(uf.upper())

    # Contagem
    cursor.execute(f"SELECT COUNT(*) as total {query_base}", params)
    total = cursor.fetchone()["total"]

    # Busca Paginada
    cursor.execute(f"SELECT * {query_base} LIMIT ? OFFSET ?", params + [limit, offset])
    resultados = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "data": resultados,
        "meta": {"page": page, "limit": limit, "total": total, "pages": (total // limit) + 1}
    }


@app.get("/api/operadoras/{id}")
def obter_detalhes_operadora(id: int):
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM operadoras_despesas WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Operadora não encontrada")
    return dict(row)


@app.get("/api/estatisticas")
def obter_estatisticas():
    conn = get_conexao()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT SUM(total_despesas) as total_mercado, AVG(total_despesas) as media_mercado FROM operadoras_despesas")
    stats = dict(cursor.fetchone())
    cursor.execute("SELECT razao_social, total_despesas FROM operadoras_despesas ORDER BY total_despesas DESC LIMIT 5")
    top5 = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"metricas": stats, "ranking": top5}