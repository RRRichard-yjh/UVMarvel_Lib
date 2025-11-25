"""
Minimal demonstration of how to browse the Bus Protocol Library.

This script is intentionally small and focused on showing how to
locate and read the AHB/APB UVM skeleton files from a local clone
of the repository. It does not perform any network or API calls.

Run it from the repository root, for example:

    python -m Bus_Protocol_Library.examples.demo_bus_skeletons
"""

from __future__ import annotations

import pathlib
from typing import List

from Bus_Protocol_Library import get_skeleton_dir  # type: ignore


def list_protocol_files(protocol: str) -> None:
    """Print all skeleton files for a given protocol."""
    proto_dir = get_skeleton_dir(protocol)  # type: ignore[arg-type]
    print(f"\n=== {protocol.upper()} SKELETON FILES ===")
    for path in sorted(proto_dir.glob("*.sv")):
        print(f"- {path.name}")


def show_file_head(protocol: str, filename: str, n_lines: int = 20) -> None:
    """Print the first few lines of a specific skeleton file."""
    proto_dir = get_skeleton_dir(protocol)  # type: ignore[arg-type]
    target = proto_dir / filename
    print(f"\n--- {protocol.upper()} :: {filename} (first {n_lines} lines) ---")
    if not target.exists():
        print(f"[missing] {target}")
        return

    lines: List[str] = target.read_text(encoding="utf-8").splitlines(keepends=True)
    for line in lines[:n_lines]:
        print(line, end="")


def main() -> None:
    """
    Run a small demo that:
      1. Lists all skeleton files for AHB and APB.
      2. Prints the first few lines of the driver skeletons as examples.
    """

    for proto in ("ahb", "apb"):
        list_protocol_files(proto)

    show_file_head("ahb", "ahb_driver.sv", n_lines=30)
    show_file_head("apb", "apb_driver.sv", n_lines=30)


if __name__ == "__main__":
    main()


