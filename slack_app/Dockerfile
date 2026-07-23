FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gbq/ gbq/
COPY pickup_pal/ pickup_pal/
COPY sql/ sql/
COPY slack_app/ slack_app/

ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "slack_app.wsgi:app"]
