import random
from datetime import datetime, timedelta, timezone

from app.config import (
    EVENT_WEIGHTS,
    MAX_SESSIONS_PER_USER,
    RECENT_HOURS,
    USER_COUNT,
)
from app.events import build_event


def build_user_pool(user_count=USER_COUNT):
    return [f"u{number:04d}" for number in range(1, user_count + 1)]


def build_session_pool(users, rng, max_sessions_per_user=MAX_SESSIONS_PER_USER):
    sessions = {}
    for user_id in users:
        session_count = rng.randint(1, max_sessions_per_user)
        sessions[user_id] = [
            f"s-{user_id}-{number:02d}" for number in range(1, session_count + 1)
        ]
    return sessions


def random_event_time(rng, now=None, recent_hours=RECENT_HOURS):
    base_time = now or datetime.now(timezone.utc)
    offset_seconds = rng.randint(0, recent_hours * 60 * 60)
    return base_time - timedelta(seconds=offset_seconds)


def generate_events(count, seed=None, now=None):
    if count < 0:
        raise ValueError("count must be greater than or equal to 0")

    rng = random.Random(seed)
    users = build_user_pool()
    sessions = build_session_pool(users, rng)
    event_types = tuple(EVENT_WEIGHTS)
    weights = tuple(EVENT_WEIGHTS.values())

    events = []
    for _ in range(count):
        event_type = rng.choices(event_types, weights=weights, k=1)[0]
        user_id = rng.choice(users)
        session_id = rng.choice(sessions[user_id])
        event_time = random_event_time(rng, now=now)
        events.append(build_event(event_type, rng, user_id, session_id, event_time))

    return sorted(events, key=lambda event: event["event_time"])
