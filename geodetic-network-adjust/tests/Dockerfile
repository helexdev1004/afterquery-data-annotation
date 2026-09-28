FROM python:3.13-slim-bookworm

RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2 numpy==2.2.1

# An unprivileged account to run the submitted module as. It owns nothing under
# /logs, so nothing it does can reach the reward file.
RUN useradd --create-home --shell /usr/sbin/nologin runner

COPY . /tests/
RUN mkdir -p /app/solution && chmod -R a+rX /tests
