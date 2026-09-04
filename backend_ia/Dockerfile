FROM python:3.12-slim

WORKDIR /app

# Instala dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicação
COPY . .

# Variável de ambiente PORT é injetada pelo Cloud Run
ENV PORT=8080
ENV TZ="America/Sao_Paulo"

# Inicia o servidor na porta determinada pela variável de ambiente
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
