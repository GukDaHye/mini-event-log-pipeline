from collections import Counter
from datetime import datetime, timezone

import pytest

from app.config import EVENT_WEIGHTS
from app.generator import generate_events


def test_event_weights_sum_to_one():
    assert sum(EVENT_WEIGHTS.values()) == pytest.approx(1.0)


def test_generate_events_count():
    events = generate_events(100, seed=42, now=datetime(2026, 5, 25, tzinfo=timezone.utc))
    assert len(events) == 100


def test_generated_event_types_are_defined():
    events = generate_events(500, seed=42, now=datetime(2026, 5, 25, tzinfo=timezone.utc))
    event_types = {event["event_type"] for event in events}
    assert event_types <= set(EVENT_WEIGHTS)


def test_event_distribution_is_close_to_expected_weights():
    count = 50_000
    events = generate_events(count, seed=42, now=datetime(2026, 5, 25, tzinfo=timezone.utc))
    observed = Counter(event["event_type"] for event in events)

    for event_type, expected_ratio in EVENT_WEIGHTS.items():
        actual_ratio = observed[event_type] / count
        assert actual_ratio == pytest.approx(expected_ratio, abs=0.02)
