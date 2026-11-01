from pathlib import Path
import re


def test_payments_table_does_not_store_card_details():
    schema = Path("schema.sql").read_text(encoding="utf-8")

    match = re.search(
        r"CREATE TABLE IF NOT EXISTS payments\s*\((.*?)\);",
        schema,
        re.IGNORECASE | re.DOTALL,
    )

    assert match is not None, "Payments table not found in schema."

    columns = match.group(1).lower()

    assert "transaction_ref" in columns
    assert re.search(r"\bstatus\b", columns)

    forbidden_fields = [
        "card_number",
        "card_no",
        "card_number_hash",
        "cvv",
        "cvc",
        "expiry",
        "expiry_date",
        "expiration_date",
        "cardholder_name",
        "card_holder_name",
    ]

    for field in forbidden_fields:
        assert not re.search(rf"\b{re.escape(field)}\b", columns), (
            f"Forbidden card-related field found: {field}"
        )
