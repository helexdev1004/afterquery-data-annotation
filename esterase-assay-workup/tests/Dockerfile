FROM python:3.13-slim-bookworm

# everything the marker needs is here already; test.sh installs nothing.
# numpy is for the program under test, which is promised it.
RUN pip install --no-cache-dir pytest==9.1.1 pytest-json-ctrf==0.5.2 numpy==2.2.1

COPY . /tests/

# /app is where the agent's program arrives; /tests and the reward directory
# are root's alone, because the program is run as `nobody`
RUN mkdir -p /app /logs/verifier && chmod 700 /tests /logs/verifier
