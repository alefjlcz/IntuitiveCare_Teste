# 1. Imagem base: Python leve
FROM python:3.10-slim

# 2. Define pasta de trabalho no container
WORKDIR /app

# 3. Copia os requisitos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia todo o código do projeto
COPY . .

# 5. Executa o ETL para garantir que o banco exista ao subir
RUN python main.py

# 6. Expõe a porta da API
EXPOSE 8000

# 7. Comando para iniciar a API
CMD ["python", "-m", "uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]