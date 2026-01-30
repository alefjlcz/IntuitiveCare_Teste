from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_api_online():
    """Testa se a API está respondendo na raiz ou docs"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_listar_operadoras():
    """Testa se a rota principal retorna dados e a estrutura correta"""
    response = client.get("/api/operadoras?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert isinstance(data["data"], list)

def test_busca_operadora_especifica():
    """Testa a busca por uma operadora que sabemos que existe (ex: Bradesco)"""
    # Nota: Depende do banco estar populado. Se falhar, verifique se rodou o ETL.
    response = client.get("/api/operadoras?q=BRADESCO&field=razao")
    assert response.status_code == 200
    data = response.json()
    # Se houver dados, verifica se o primeiro contém 'BRADESCO'
    if data["data"]:
        assert "BRADESCO" in data["data"][0]["razao_social"].upper()

def test_estatisticas():
    """Testa se o endpoint de estatísticas calcula os totais"""
    response = client.get("/api/estatisticas")
    assert response.status_code == 200
    data = response.json()
    assert "total_geral" in data
    assert "top_operadoras" in data