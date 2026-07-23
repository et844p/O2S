"""WSGI entrypoint for Cloud Run / gunicorn."""

from slack_app.app import create_flask_app

app = create_flask_app()
