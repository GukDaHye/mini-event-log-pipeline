from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from app.db import fetch_all


EVENT_TYPE_COUNTS_SQL = """
SELECT event_type, COUNT(*) AS cnt
FROM events
GROUP BY event_type
ORDER BY cnt DESC;
"""

HOURLY_TREND_SQL = """
SELECT date_trunc('hour', event_time) AS hour, COUNT(*) AS cnt
FROM events
GROUP BY 1
ORDER BY 1;
"""

ERROR_RATIO_SQL = """
SELECT
    COUNT(*) FILTER (WHERE event_type = 'error') AS error_count,
    COUNT(*) FILTER (WHERE event_type <> 'error') AS normal_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE event_type = 'error') / NULLIF(COUNT(*), 0),
        2
    ) AS error_pct
FROM events;
"""

TOP_PRODUCTS_REVENUE_SQL = """
SELECT product_id, SUM(amount) AS revenue, COUNT(*) AS orders
FROM events
WHERE event_type = 'purchase'
GROUP BY product_id
ORDER BY revenue DESC
LIMIT 10;
"""

FUNNEL_SQL = """
SELECT
    COUNT(*) FILTER (WHERE event_type = 'product_view') AS views,
    COUNT(*) FILTER (WHERE event_type = 'add_to_cart') AS carts,
    COUNT(*) FILTER (WHERE event_type = 'purchase') AS purchases,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE event_type = 'purchase')
        / NULLIF(COUNT(*) FILTER (WHERE event_type = 'product_view'), 0),
        2
    ) AS view_to_purchase_pct
FROM events;
"""


def run_analyses(conn):
    return {
        "event_type_counts": fetch_all(conn, EVENT_TYPE_COUNTS_SQL),
        "hourly_trend": fetch_all(conn, HOURLY_TREND_SQL),
        "error_ratio": fetch_all(conn, ERROR_RATIO_SQL)[0],
        "top_products_revenue": fetch_all(conn, TOP_PRODUCTS_REVENUE_SQL),
        "funnel": fetch_all(conn, FUNNEL_SQL)[0],
    }


def save_bar_chart(rows, x_key, y_key, title, xlabel, ylabel, output_path):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar([row[x_key] for row in rows], [row[y_key] for row in rows], color="#3b82f6")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_hourly_trend(rows, output_path):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot([row["hour"] for row in rows], [row["cnt"] for row in rows], marker="o")
    ax.set_title("Hourly Event Trend")
    ax.set_xlabel("Hour")
    ax.set_ylabel("Events")
    ax.grid(True, linestyle="--", alpha=0.35)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_error_ratio(row, output_path):
    fig, ax = plt.subplots(figsize=(6, 6))
    values = [row["normal_count"], row["error_count"]]
    ax.pie(
        values,
        labels=["normal", "error"],
        autopct="%1.1f%%",
        colors=["#22c55e", "#ef4444"],
        startangle=90,
    )
    ax.set_title("Error Ratio")
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_top_products(rows, output_path):
    fig, ax = plt.subplots(figsize=(9, 5))
    labels = [row["product_id"] for row in rows]
    revenues = [float(row["revenue"]) for row in rows]
    ax.barh(labels, revenues, color="#14b8a6")
    ax.invert_yaxis()
    ax.set_title("Top Products by Revenue")
    ax.set_xlabel("Revenue")
    ax.set_ylabel("Product")
    ax.grid(axis="x", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_funnel(row, output_path):
    stages = ["product_view", "add_to_cart", "purchase"]
    counts = [row["views"], row["carts"], row["purchases"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(stages, counts, color=["#60a5fa", "#f59e0b", "#10b981"])
    ax.set_title("Commerce Funnel")
    ax.set_ylabel("Events")
    ax.grid(axis="y", linestyle="--", alpha=0.35)

    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            str(count),
            ha="center",
            va="bottom",
        )

    ax.text(
        0.5,
        -0.18,
        f"view to purchase: {row['view_to_purchase_pct']}%",
        transform=ax.transAxes,
        ha="center",
    )
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def save_charts(results, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    save_bar_chart(
        results["event_type_counts"],
        "event_type",
        "cnt",
        "Event Type Counts",
        "Event type",
        "Count",
        output_path / "event_type_counts.png",
    )
    save_hourly_trend(results["hourly_trend"], output_path / "hourly_trend.png")
    save_error_ratio(results["error_ratio"], output_path / "error_ratio.png")
    save_top_products(
        results["top_products_revenue"],
        output_path / "top_products_revenue.png",
    )
    save_funnel(results["funnel"], output_path / "funnel.png")
