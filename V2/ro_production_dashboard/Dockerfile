# Dockerfile for Daily RO Production Dashboard (v2.0-beta)
# Builds a containerized Streamlit app with Microsoft ODBC Driver for SQL Server.
# Recommended for consistent deploys on Linux hosts or orchestration.
# For Windows Server production, prefer NSSM-wrapped Python service + reverse proxy (see SRS).

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# System deps + Microsoft ODBC 18 (preferred)
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    curl \
    apt-transport-https \
    unixodbc \
    && curl https://packages.microsoft.com/keys/microsoft.asc | tee /etc/apt/trusted.gpg.d/microsoft.asc \
    && curl https://packages.microsoft.com/config/ubuntu/24.04/prod.list | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Python venv for isolation
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create .streamlit dir if missing and set permissions
RUN mkdir -p .streamlit && chown -R appuser:appuser /app

USER appuser

EXPOSE 8501

# Run Streamlit, bind to all interfaces inside container (reverse proxy terminates TLS/auth outside)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
