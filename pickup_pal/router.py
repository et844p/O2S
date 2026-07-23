"""Lightweight natural-language routing for Pickup Pal Slack messages."""

from __future__ import annotations

import re
from dataclasses import dataclass

from pickup_pal.queries import QUERIES

INTENT_PATTERNS: list[tuple[str, str]] = [
    ("extra_pickup", r"\b(extra pickup|enough volume|cancel pickup|additional pickup|add pickup)\b"),
    ("pickups_this_week", r"\b(this week|pickups this week|how many pickups|pickup count)\b"),
    ("typical_days", r"\b(typical|pickup days|usually pick|normal pickup|what days)\b"),
]

SLASH_ALIASES = {
    "extra-pickup": "extra_pickup",
    "extra_pickup": "extra_pickup",
    "pickups": "pickups_this_week",
    "pickups-this-week": "pickups_this_week",
    "pickups_this_week": "pickups_this_week",
    "typical-days": "typical_days",
    "typical_days": "typical_days",
    "days": "typical_days",
}


@dataclass
class ParsedMessage:
    intent: str | None
    supplier: str | None
    error: str | None = None


def _strip_bot_mention(text: str) -> str:
    return re.sub(r"<@[A-Z0-9]+>", "", text).strip()


def _extract_supplier(text: str) -> str | None:
    quoted = re.search(r'"([^"]+)"|\'([^\']+)\'', text)
    if quoted:
        return (quoted.group(1) or quoted.group(2)).strip()

    patterns = [
        r"\bdoes\s+(.+?)\s+have\b",
        r"\bhow many pickups does\s+(.+?)\s+have\b",
        r"\bwhat are the typical pickup days for\s+(.+?)(?:\?|$)",
        r"\btypical pickup days for\s+(.+?)(?:\?|$)",
        r"\bfor\s+(.+?)(?:\?|$)",
        r"\bsupplier[:\s]+(.+?)(?:\?|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            supplier = match.group(1).strip(" .?!,")
            if supplier:
                return supplier

    # Fallback: trailing words after removing intent keywords
    cleaned = text
    for _, pattern in INTENT_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"\b(pickup|pickups|please|help|what|how|many|does|the|for|are|is|a|an)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .?!,")
    return cleaned or None


def detect_intent(text: str) -> str | None:
    lowered = text.lower()
    for intent, pattern in INTENT_PATTERNS:
        if re.search(pattern, lowered):
            return intent
    return None


def parse_message(text: str) -> ParsedMessage:
    """Parse a Slack message into query intent and supplier name."""
    cleaned = _strip_bot_mention(text)
    if not cleaned:
        return ParsedMessage(intent=None, supplier=None, error="empty")

    lowered = cleaned.lower()
    if lowered in {"help", "?", "commands"}:
        return ParsedMessage(intent="help", supplier=None)

    intent = detect_intent(cleaned)
    supplier = _extract_supplier(cleaned)

    if intent is None:
        return ParsedMessage(
            intent=None,
            supplier=supplier,
            error="Could not determine question type. Try `help` for examples.",
        )
    if not supplier:
        return ParsedMessage(
            intent=intent,
            supplier=None,
            error="Could not find a supplier name. Try quoting it, e.g. `\"Flash Furniture\"`.",
        )
    return ParsedMessage(intent=intent, supplier=supplier)


def parse_slash_command(text: str) -> ParsedMessage:
    """Parse `/pickup-pal <command> <supplier>` style input."""
    cleaned = text.strip()
    if not cleaned or cleaned.lower() in {"help", "?"}:
        return ParsedMessage(intent="help", supplier=None)

    parts = cleaned.split(maxsplit=1)
    command = parts[0].lower()
    intent = SLASH_ALIASES.get(command)
    if intent is None:
        return ParsedMessage(
            intent=None,
            supplier=None,
            error=f"Unknown command `{command}`. Use one of: {', '.join(sorted(set(SLASH_ALIASES)))}.",
        )

    if len(parts) < 2:
        return ParsedMessage(
            intent=intent,
            supplier=None,
            error=f"Please include a supplier name, e.g. `/pickup-pal {command} Flash Furniture`.",
        )

    return ParsedMessage(intent=intent, supplier=parts[1].strip().strip('"'))


def help_text() -> str:
    lines = [
        "*Pickup Pal* — Large Parcel OTR pickup assistant",
        "",
        "*Ask naturally in channel:*",
        '• `@Pickup Pal does Flash Furniture have enough volume for an extra pickup?`',
        '• `@Pickup Pal how many pickups does Fusion Furniture have this week?`',
        '• `@Pickup Pal what are the typical pickup days for Polywood?`',
        "",
        "*Slash commands:*",
        "• `/pickup-pal extra-pickup Flash Furniture`",
        "• `/pickup-pal pickups Fusion Furniture`",
        "• `/pickup-pal typical-days Polywood`",
        "",
        "*Supported queries:*",
    ]
    for name, meta in QUERIES.items():
        lines.append(f"• `{name}` — {meta['description']}")
    return "\n".join(lines)
