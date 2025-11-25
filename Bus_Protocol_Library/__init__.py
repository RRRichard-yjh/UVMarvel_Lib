"""
Bus Protocol Library
====================

Human-readable UVM skeletons for standard bus protocols.

Currently supported:
    - AHB
    - APB

Each protocol directory (``ahb/``, ``apb/``) contains separate
SystemVerilog skeletons for:
    - interface
    - transaction item
    - driver
    - sequencer
    - monitor
    - agent

These skeletons are intended to capture the *stable* protocol control
flow and handshake rules. When adapting them to a specific DUT, users
or LLMs should primarily specialise:
    - signal names and widths
    - configuration fields
    - address ranges and data payloads

while keeping the core timing and handshake behaviour intact.
"""

from __future__ import annotations

import pathlib
from typing import Literal


ProtocolName = Literal["ahb", "apb"]


def get_library_root() -> pathlib.Path:
    """Return the root directory of the Bus Protocol Library."""
    return pathlib.Path(__file__).resolve().parent


def get_skeleton_dir(protocol: ProtocolName) -> pathlib.Path:
    """
    Return the directory containing skeletons for a given protocol.

    Parameters
    ----------
    protocol:
        One of ``\"ahb\"`` or ``\"apb\"`` (case-insensitive).
    """
    root = get_library_root()
    proto = protocol.lower()
    if proto not in {"ahb", "apb"}:
        raise ValueError(f"Unsupported protocol '{protocol}'. Expected 'ahb' or 'apb'.")
    return root / proto


