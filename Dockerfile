# ── SENTINEL ENGINE DOCKERFILE ──────────────────────────────────────────────
# Hardened Python Base Image
FROM python:3.12-slim-bookworm

# 1. Environment Variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="." \
    SOC_PATH="/app/soc"

# 2. System Dependencies (Security & Diagnostics)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nmap \
    tcpdump \
    libpcap-dev \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Create Non-Privileged User (Least Privilege)
RUN groupadd -g 1000 socgroup && \
    useradd -u 1000 -g socgroup -m -s /bin/bash socuser

WORKDIR /app

# 4. Install Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Application Source Code
COPY . .

# 6. Secure Directory Permissions
# Ensure the non-privileged user can write to bus, reports, and configs
RUN chown -R socuser:socgroup /app/soc/bus /app/soc/reports /app/soc/configs && \
    chmod -R 770 /app/soc/bus /app/soc/reports /app/soc/configs

# Note: soc-scout may still need root/privileged for ARP/Sniffing. 
# We default to socuser for security, and override if necessary in compose.
USER socuser

# API Port
EXPOSE 8000

# Default entry point (Overridden by docker-compose)
CMD ["python", "main.py", "start", "api"]
