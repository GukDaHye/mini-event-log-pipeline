from decimal import Decimal


PAGE_URLS = (
    "/",
    "/search",
    "/products",
    "/cart",
    "/checkout",
    "/campaign/spring-sale",
)

PRODUCT_PRICES = {
    "p001": Decimal("12900.00"),
    "p002": Decimal("18900.00"),
    "p003": Decimal("24900.00"),
    "p004": Decimal("31900.00"),
    "p005": Decimal("45900.00"),
    "p006": Decimal("59900.00"),
    "p007": Decimal("79000.00"),
    "p008": Decimal("99000.00"),
    "p009": Decimal("129000.00"),
    "p010": Decimal("159000.00"),
}

ERRORS = (
    ("E_TIMEOUT", "upstream request timed out"),
    ("E_PAYMENT", "payment approval failed"),
    ("E_STOCK", "product stock is unavailable"),
    ("E_VALIDATION", "invalid checkout request"),
)


def empty_event(event_type, user_id, session_id, event_time):
    return {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id,
        "event_time": event_time,
        "page_url": None,
        "product_id": None,
        "quantity": None,
        "amount": None,
        "error_code": None,
        "error_message": None,
    }


def build_event(event_type, rng, user_id, session_id, event_time):
    event = empty_event(event_type, user_id, session_id, event_time)

    if event_type == "page_view":
        event["page_url"] = rng.choice(PAGE_URLS)
        return event

    if event_type == "product_view":
        event["product_id"] = rng.choice(tuple(PRODUCT_PRICES))
        return event

    if event_type == "add_to_cart":
        event["product_id"] = rng.choice(tuple(PRODUCT_PRICES))
        event["quantity"] = rng.randint(1, 3)
        return event

    if event_type == "purchase":
        product_id = rng.choice(tuple(PRODUCT_PRICES))
        quantity = rng.randint(1, 4)
        event["product_id"] = product_id
        event["quantity"] = quantity
        event["amount"] = PRODUCT_PRICES[product_id] * quantity
        return event

    if event_type == "error":
        event["error_code"], event["error_message"] = rng.choice(ERRORS)
        return event

    raise ValueError(f"unknown event_type: {event_type}")
