FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema (psycopg2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Requisitos python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Proyecto
COPY . /app