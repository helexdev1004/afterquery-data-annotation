FROM python:3.13-slim-bookworm

RUN pip install --no-cache-dir numpy==2.2.1 scipy==1.15.0

COPY plates /app/plates

WORKDIR /app
CMD ["sleep", "infinity"]
