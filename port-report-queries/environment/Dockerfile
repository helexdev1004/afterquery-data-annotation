FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        postgresql postgresql-client procps \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir psycopg==3.2.3

COPY data /app/data
COPY queries /app/queries
COPY expected /app/expected
COPY schema.sql /app/schema.sql
COPY pgboot.sh reports-up /usr/local/bin/
RUN chmod +x /usr/local/bin/pgboot.sh /usr/local/bin/reports-up \
    && mkdir -p /app/ported

ENV DATABASE_URL=postgresql://postgres@127.0.0.1:5432/reports
WORKDIR /app
CMD ["/usr/local/bin/reports-up", "--foreground"]
