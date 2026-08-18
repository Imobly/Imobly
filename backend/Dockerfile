# =============================================================================
# Multi-stage Dockerfile para Backend Imobly
# Suporta: development, production, testing
# =============================================================================

# -----------------------------------------------------------------------------
# Stage: Base - Dependências comuns a todos os ambientes
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage: Development - Com ferramentas de debug
# -----------------------------------------------------------------------------
FROM base AS development

# Ferramentas extras para desenvolvimento
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências (dev + prod)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copiar código
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/uploads /app/logs && \
    chmod 777 /app/uploads /app/logs

EXPOSE 8000

# Servidor com reload para desenvolvimento.
#
# `--reload-dir src` limita o watcher ao código da aplicação. Sem isso o
# uvicorn observa /app inteiro — incluindo alembic/, tests/, logs/ e scripts/ —
# e sobre o compartilhamento de arquivos do Docker Desktop no Windows esse
# volume de varredura satura a camada FUSE, que passa a devolver ENOMEM:
#   WatchfilesRustInternalError: error in underlying watcher: Cannot allocate
#   memory (os error 12)
# Quando isso acontece o servidor continua respondendo, mas o hot reload morre
# em silêncio — você edita o código e nada muda, sem nenhum erro visível.
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--reload", "--reload-dir", "src"]

# -----------------------------------------------------------------------------
# Stage: Testing - Para CI/CD e testes locais
# -----------------------------------------------------------------------------
FROM base AS testing

# Ferramentas de teste
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências de teste
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copiar código
COPY . .

ENV PYTHONPATH=/app

# Comando para executar linting + testes
CMD ["sh", "-c", "\
    echo '=== Running Black ===' && \
    black --check --line-length 100 src tests && \
    echo '=== Running isort ===' && \
    isort --check-only src tests && \
    echo '=== Running Flake8 ===' && \
    flake8 src tests && \
    echo '=== Running MyPy ===' && \
    mypy src && \
    echo '=== Running Tests ===' && \
    pytest -v --cov=src --cov-report=html --cov-report=term-missing && \
    echo '✅ All tests passed!' \
"]

# -----------------------------------------------------------------------------
# Stage: Production - Otimizado e seguro
# -----------------------------------------------------------------------------
FROM base AS production

# Copiar apenas requirements de produção
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/uploads /app/logs

# Criar usuário não-root para segurança
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

EXPOSE 8000

# Servidor em produção (sem reload)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
