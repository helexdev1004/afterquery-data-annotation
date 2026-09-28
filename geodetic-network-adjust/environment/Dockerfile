FROM python:3.13-slim-bookworm

RUN pip install --no-cache-dir numpy==2.2.1

COPY networks /app/networks
COPY published /app/published
COPY solution /app/solution

WORKDIR /app
CMD ["sleep", "infinity"]
