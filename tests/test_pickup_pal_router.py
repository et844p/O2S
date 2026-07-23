"""Tests for Pickup Pal message routing."""

from pickup_pal.router import parse_message, parse_slash_command


def test_extra_pickup_natural_language():
    parsed = parse_message(
        "<@U123> does Flash Furniture have enough volume for an extra pickup?"
    )
    assert parsed.intent == "extra_pickup"
    assert parsed.supplier == "Flash Furniture"
    assert parsed.error is None


def test_pickups_this_week_natural_language():
    parsed = parse_message("<@U123> how many pickups does Fusion Furniture have this week?")
    assert parsed.intent == "pickups_this_week"
    assert parsed.supplier == "Fusion Furniture"


def test_typical_days_natural_language():
    parsed = parse_message("<@U123> what are the typical pickup days for Polywood?")
    assert parsed.intent == "typical_days"
    assert parsed.supplier == "Polywood"


def test_slash_command():
    parsed = parse_slash_command("extra-pickup Flash Furniture")
    assert parsed.intent == "extra_pickup"
    assert parsed.supplier == "Flash Furniture"


def test_help_intent():
    parsed = parse_message("help")
    assert parsed.intent == "help"
