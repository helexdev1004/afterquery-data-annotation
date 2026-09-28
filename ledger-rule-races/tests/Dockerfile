FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PGBIN=/usr/lib/postgresql/15/bin \
    PGDATA=/var/lib/pgdata \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/tests

# Everything the verifier needs is installed here; test.sh never apt-gets,
# curls or downloads packages at verify time.
RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql \
        postgresql-client \
        curl \
        procps \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# The deployment package set, identical to the agent's environment, so the
# submitted service runs here unchanged.
RUN pip install --no-cache-dir \
        pytest==9.1.1 \
        pytest-json-ctrf==0.5.2 \
        fastapi==0.115.6 \
        uvicorn==0.34.0 \
        asyncpg==0.30.0 \
        pydantic==2.10.4 \
        httpx==0.28.1 \
        sqlalchemy==2.0.36 \
        psycopg==3.2.3 \
        tenacity==9.0.0

# Bake the sealed grader; nothing under tests/ is uploaded at verify time.
COPY . /tests/
RUN chmod +x /tests/pgboot.sh /tests/test.sh

# The submitted service is executed here, so it does not get to run as root.
# `runner` owns nothing: it cannot write to /logs/verifier, cannot touch /tests,
# and cannot replace the reward file.
RUN useradd --create-home --shell /usr/sbin/nologin runner

RUN mkdir -p /var/lib/pgdata /logs/verifier /app/service \
    && chown -R postgres:postgres /var/lib/pgdata \
    && chown root:root /logs/verifier && chmod 755 /logs/verifier \
    && chown -R root:root /tests && chmod -R go-w /tests

WORKDIR /tests
