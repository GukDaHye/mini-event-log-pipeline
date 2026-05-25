from datetime import datetime, timezone

from app.generator import generate_events


def test_event_time_is_timezone_aware():
    events = generate_events(20, seed=7, now=datetime(2026, 5, 25, tzinfo=timezone.utc))
    assert all(event["event_time"].tzinfo is not None for event in events)


def test_type_specific_fields_are_populated():
    events = generate_events(1_000, seed=7, now=datetime(2026, 5, 25, tzinfo=timezone.utc))

    for event in events:
        event_type = event["event_type"]

        if event_type == "page_view":
            assert event["page_url"] is not None
            assert event["product_id"] is None
            assert event["amount"] is None
            assert event["error_code"] is None

        if event_type == "product_view":
            assert event["product_id"] is not None
            assert event["quantity"] is None
            assert event["amount"] is None
            assert event["error_code"] is None

        if event_type == "add_to_cart":
            assert event["product_id"] is not None
            assert event["quantity"] is not None
            assert event["amount"] is None
            assert event["error_code"] is None

        if event_type == "purchase":
            assert event["product_id"] is not None
            assert event["quantity"] is not None
            assert event["amount"] is not None
            assert event["error_code"] is None

        if event_type == "error":
            assert event["error_code"] is not None
            assert event["error_message"] is not None
            assert event["product_id"] is None
            assert event["amount"] is None
