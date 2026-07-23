# utils/generate_ref.py
# Generates a unique payment reference number.
# Kept in its own module so payment_service.py can import it
# without pulling in the rest of helpers.py.

import random
import string


def generate_reference_number() -> str:
    """Returns a random 13-char reference number. e.g. TXNA3F8K2M9X"""
    random_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    return f"TXN{random_part}"
