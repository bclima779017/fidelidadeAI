FROM python:3.11-slim

WORKDIR /app

# Instalar dependências primeiro (cache de camada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Copiar knowledge base do diretório raiz (se existir)
COPY knowledge/ /app/knowledge/ 2>/dev/null || true

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
