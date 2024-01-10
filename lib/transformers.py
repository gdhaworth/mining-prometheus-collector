import dictlib
import math
import os
import platform
import re

from typing import Optional, Dict


if 'DEBUG_MOCK_HOSTNAME' in os.environ:
    def hostname(*_):
        return os.environ['DEBUG_MOCK_HOSTNAME']
else:
    def hostname(*_):
        return platform.node()


def mining_platform(*_):
    return platform.system()


def si_suffixed(value: str, *_) -> Optional[float]:
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


def worker_from_user_field(user_value: str, *_) -> str:
    match = re.search(r'^[^.]+\.(.+)$', user_value)
    return match[1] if match else ''


def wallet_from_user_field(user_value: str, *_) -> str:
    match = re.search(r'^([^.]+)\..+$', user_value)
    return match[1] if match else ''


def wallet_addr_from_user_field(user_value: str, *_) -> str:
    match = re.search(r'^([^.]+)(\..*)?', user_value)
    return match[1] if match else user_value


def pow10(value_key: str, pow_10_key: str, base: Dict, i: int = None) -> float:
    if i is not None:
        value_key = value_key.replace('[i]', f'[{i}]')
        pow_10_key = pow_10_key.replace('[i]', f'[{i}]')
    exp = round(math.log(dictlib.dig(base, pow_10_key), 10))
    return float(f'{dictlib.dig(base, value_key)}e{exp}')


def pcie_bus_slot_str_to_id(bus_slot: str, *_) -> str:
    bus, slot = bus_slot.split(':')
    return f'{bus.zfill(2)}:{slot.zfill(2)}'


def pcie_bus_slot_paths_to_id(bus_path: str, slot_path: str, base: Dict, i: int = None) -> str:
    if i is not None:
        bus_path = bus_path.replace('[i]', f'[{i}]')
        slot_path = slot_path.replace('[i]', f'[{i}]')
    bus = hex(dictlib.dig(base, bus_path))[2:].zfill(2)
    slot = hex(dictlib.dig(base, slot_path))[2:].zfill(2)
    return f'{bus}:{slot}'


def only_above_0(value, *_) -> Optional:
    return value if value > 0 else None
