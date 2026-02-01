FROM python:3.12-slim

WORKDIR /app

# REMOVIDA A LINHA DO MKDIR AQUI

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD python main.py && python -m uvicorn src.api:app --host 0.0.0.0 --port 8000