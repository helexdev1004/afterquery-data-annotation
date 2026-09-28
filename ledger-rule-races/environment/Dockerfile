FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PGBIN=/usr/lib/postgresql/15/bin \
    PGDATA=/var/lib/pgdata \
    DATABASE_URL=postgresql://ledger@127.0.0.1:5432/ledger \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql \
        postgresql-client \
        curl \
        procps \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The deployment package set. The fix has to run on exactly this; the grader
# installs nothing at verify time.
RUN pip install --no-cache-dir \
        fastapi==0.115.6 \
        uvicorn==0.34.0 \
        asyncpg==0.30.0 \
        pydantic==2.10.4 \
        httpx==0.28.1 \
        sqlalchemy==2.0.36 \
        psycopg==3.2.3 \
        tenacity==9.0.0 \
        pytest==9.1.1

RUN mkdir -p /app/service /var/lib/pgdata /var/log/ledger \
    && chown -R postgres:postgres /var/lib/pgdata

COPY service/ /app/service/
COPY pgboot.sh /usr/local/bin/pgboot.sh
COPY ledger-up.sh /usr/local/bin/ledger-up.sh
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/pgboot.sh /usr/local/bin/ledger-up.sh \
        /usr/local/bin/entrypoint.sh /app/service/run.sh \
    && ln -s /usr/local/bin/ledger-up.sh /usr/local/bin/ledger-up

WORKDIR /app/service

CMD ["/usr/local/bin/entrypoint.sh"]
