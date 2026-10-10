"""Reserved for typed response models.

Version 0.x returns X's raw GraphQL JSON as plain dicts and lists, exactly as the API sends
it. Typed models (for example ``User`` and ``Tweet`` parsed from those responses) will live
in this package once their shapes are settled. Resource methods will keep returning raw JSON
by default so existing code does not break.
"""

from typing import List

__all__: List[str] = []
