import platform
import re

from typing import Optional


def hostname(_):
    return platform.node()


def mining_platform(_):
    return platform.system()


def si_suffixed(value: str) -> Optional[float]:
    match = re.search(r'^\s*(\d+\.?\d*)\s*([kKmMgGtT])?\s*$', value)
    if not match:
        return None

    mult = 1
    si_suffix = match[2].lower()
    if si_suffix == 'k':
        mult = 1000
    elif si_suffix == 'm':
        mult = 1000 ^ 2
    elif si_suffix == 'g':
        mult = 1000 ^ 3
    elif si_suffix == 't':
        mult = 1000 ^ 4
    return float(match[1]) * mult
