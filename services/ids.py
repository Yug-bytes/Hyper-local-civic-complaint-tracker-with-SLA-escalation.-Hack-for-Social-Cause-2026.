"""Tracking ID generation for complaints.

Format: CT-YYMMDD-XXXX where XXXX is a random suffix from an
unambiguous alphabet (no characters that look alike: 0/O, 1/I/L, 5/S, 2/Z, 8/B).
"""

import random
from datetime import datetime

# Characters that are hard to confuse when read aloud or handwritten
_ALPHABET: str = "34679ACDEFGHJKMNPQRTUVWXY"
_SUFFIX_LENGTH: int = 4


def generate_tracking_id(now: datetime) -> str:
    """Generate a unique tracking ID like CT-261008-A7K2."""
    date_part = now.strftime("%y%m%d")
    suffix = "".join(random.choices(_ALPHABET, k=_SUFFIX_LENGTH))
    return f"CT-{date_part}-{suffix}"
