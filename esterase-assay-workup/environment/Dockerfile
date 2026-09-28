FROM python:3.13-slim-bookworm

# the program is marked under Python 3 with numpy and nothing else
RUN pip install --no-cache-dir numpy==2.2.1

COPY app/ /app/
WORKDIR /app
CMD ["sleep", "infinity"]
