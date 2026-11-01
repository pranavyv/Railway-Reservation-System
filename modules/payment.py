"""Mock payment processing for railway bookings."""

from uuid import uuid4


VALID_OUTCOMES = {"SUCCESS", "FAILED", "TIMEOUT"}


def process_payment(user_id, booking_id, payment_outcome="SUCCESS", repo=None):
    """Process mock payment without accepting or storing card details."""

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    if not isinstance(booking_id, int) or isinstance(booking_id, bool) or booking_id <= 0:
        raise ValueError("Invalid booking ID.")

    outcome = str(payment_outcome or "").strip().upper()

    if outcome not in VALID_OUTCOMES:
        raise ValueError("Invalid mock payment outcome.")

    if repo is None:
        from repository import payment_repo
        repo = payment_repo

    transaction_ref = f"MOCK-{uuid4().hex.upper()}"

    return repo.record_payment(
        user_id=user_id,
        booking_id=booking_id,
        transaction_ref=transaction_ref,
        status=outcome,
    )
