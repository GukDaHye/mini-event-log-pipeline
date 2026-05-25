from app.analysis import run_analyses, save_charts
from app.config import EVENT_COUNT, OUTPUT_DIR
from app.db import connect, insert_events, reset_events
from app.generator import generate_events


def main():
    print(f"Generating {EVENT_COUNT} commerce events")
    events = generate_events(EVENT_COUNT)

    conn = connect()
    try:
        reset_events(conn)
        insert_events(conn, events)
        print(f"Inserted {len(events)} events into PostgreSQL")

        results = run_analyses(conn)
        save_charts(results, OUTPUT_DIR)
        print(f"Saved charts to {OUTPUT_DIR}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
