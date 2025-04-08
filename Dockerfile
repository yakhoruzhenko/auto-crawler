FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

RUN apt-get remove -y gcc && apt-get autoremove -y

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY entrypoint.sh .

RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app

STOPSIGNAL SIGINT

CMD ["python", "-m", "app.services.crawler"]
