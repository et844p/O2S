"""Pickup Pal Slack bot — Bolt app for large parcel pickup questions."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

_default_creds = ROOT / ".gcp" / "credentials.json"
if _default_creds.exists():
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", str(_default_creds))

from flask import Flask, jsonify, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.adapter.socket_mode import SocketModeHandler

from pickup_pal.queries import run_query
from pickup_pal.router import help_text, parse_message, parse_slash_command

logger = logging.getLogger(__name__)


def _allowed_channel(channel_id: str | None) -> bool:
    allowed = os.environ.get("PICKUP_PAL_ALLOWED_CHANNELS", "").strip()
    if not allowed:
        return True
    allowed_ids = {item.strip() for item in allowed.split(",") if item.strip()}
    return channel_id in allowed_ids


def _channel_denied_message() -> str:
    return (
        "This channel is not enabled for Pickup Pal. "
        "Ask an admin to add the channel ID to `PICKUP_PAL_ALLOWED_CHANNELS`."
    )


def _handle_lookup(intent: str, supplier: str) -> str:
    try:
        return run_query(intent, supplier)
    except Exception as exc:  # noqa: BLE001 - surface query failures to Slack
        logger.exception("Pickup Pal query failed for %s / %s", intent, supplier)
        return f"Query failed: {exc}"


def create_bolt_app() -> App:
    slack_app = App(
        token=os.environ["SLACK_BOT_TOKEN"],
        signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    )

    @slack_app.event("app_mention")
    def handle_mention(event, say, client):
        channel = event.get("channel")
        if not _allowed_channel(channel):
            say(text=_channel_denied_message(), thread_ts=event.get("ts"))
            return

        parsed = parse_message(event.get("text", ""))
        if parsed.error == "empty" or parsed.intent == "help":
            say(text=help_text(), thread_ts=event.get("ts"))
            return
        if parsed.error:
            say(text=f"{parsed.error}\n\n{help_text()}", thread_ts=event.get("ts"))
            return

        client.reactions_add(channel=channel, timestamp=event["ts"], name="hourglass_flowing_sand")
        try:
            response = _handle_lookup(parsed.intent, parsed.supplier)
        finally:
            try:
                client.reactions_remove(channel=channel, timestamp=event["ts"], name="hourglass_flowing_sand")
            except Exception:  # noqa: BLE001
                pass

        say(text=response, thread_ts=event.get("ts"))

    @slack_app.event("message")
    def handle_message(event, say):
        if event.get("channel_type") != "im":
            return
        if event.get("subtype") or event.get("bot_id"):
            return

        parsed = parse_message(event.get("text", ""))
        if parsed.error == "empty" or parsed.intent == "help":
            say(text=help_text())
            return
        if parsed.error:
            say(text=f"{parsed.error}\n\n{help_text()}")
            return

        say(text=_handle_lookup(parsed.intent, parsed.supplier))

    @slack_app.command("/pickup-pal")
    def handle_slash(ack, respond, command):
        ack()
        if not _allowed_channel(command.get("channel_id")):
            respond(_channel_denied_message())
            return

        parsed = parse_slash_command(command.get("text", ""))
        if parsed.intent == "help":
            respond(help_text())
            return
        if parsed.error:
            respond(f"{parsed.error}\n\n{help_text()}")
            return

        respond(_handle_lookup(parsed.intent, parsed.supplier))

    return slack_app


def create_flask_app() -> Flask:
    bolt_app = create_bolt_app()
    flask_app = Flask(__name__)
    handler = SlackRequestHandler(bolt_app)

    @flask_app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "pickup-pal"})

    @flask_app.route("/slack/events", methods=["POST"])
    def slack_events():
        return handler.handle(request)

    return flask_app


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    app_token = os.environ.get("SLACK_APP_TOKEN")
    if app_token:
        logger.info("Starting Pickup Pal in Socket Mode")
        SocketModeHandler(create_bolt_app(), app_token).start()
        return

    port = int(os.environ.get("PORT", "3000"))
    logger.info("Starting Pickup Pal HTTP server on port %s", port)
    create_flask_app().run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
