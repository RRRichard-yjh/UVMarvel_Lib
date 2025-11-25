"""
Minimal demonstration of how to use the Verilog Patch Template Library.

This script is intentionally small and focused on showing the "stitching"
behavior on a few hand-written RTL fragments. It is not a full test suite.

Run it from the repository root, for example:

    python -m Verilog_Patch_Template_Library.examples.patch_demo_basic
"""

from __future__ import annotations

import pathlib
import sys
from typing import List


# Make the package importable when running from a cloned repository.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from Verilog_Patch_Template_Library import SyntaxErrorPatcher  # type: ignore  # noqa: E402


def demo_assign_template() -> None:
    print("\n=== ASSIGN TEMPLATE DEMO ===")
    rtl: List[str] = [
        "assign coreclk_div1_en =\n",
        "        (clk_sel == 2'b00) ?\n",
        "        1'b1 :\n",
        "        1'b0\n",
        "\n",
    ]
    patcher = SyntaxErrorPatcher()
    patched = patcher.assign_patcher.fix_assign_statements(rtl)

    print("---- before ----")
    print("".join(rtl))
    print("---- after  ----")
    print("".join(patched))


def demo_if_else_template() -> None:
    print("\n=== IF-ELSE TEMPLATE DEMO ===")
    rtl: List[str] = [
        "// original 'if (reset_n == 1'b0)' was trimmed away\n",
        "else if (force_div1)\n",
        "  coreclk_div1 <= 1'b1;\n",
        "else\n",
        "  coreclk_div1 <= 1'b0;\n",
        "\n",
    ]
    patcher = SyntaxErrorPatcher()
    patched = patcher.if_else_patcher.fix_if_else_statements(rtl)

    print("---- before ----")
    print("".join(rtl))
    print("---- after  ----")
    print("".join(patched))


def demo_case_template() -> None:
    print("\n=== CASE TEMPLATE DEMO ===")
    rtl: List[str] = [
        "case (coreclk_div1_cfg)\n",
        "  2'b00: coreclk_div1_next = clk_div1_in;\n",
        "  2'b01: coreclk_div1_next = clk_div2_in;\n",
        "  default: coreclk_div1_next = 1'b0;\n",
        "// note: missing endcase on purpose\n",
        "\n",
    ]
    patcher = SyntaxErrorPatcher()
    patched = patcher.case_patcher.fix_case_statements(rtl)

    print("---- before ----")
    print("".join(rtl))
    print("---- after  ----")
    print("".join(patched))


def demo_always_template() -> None:
    print("\n=== ALWAYS TEMPLATE DEMO ===")
    rtl: List[str] = [
        "module demo(input clk, input reset_n, input coreclk_div1_en, input next_coreclk_div1);\n",
        "  // incomplete always header, sequential logic in the body\n",
        "  always\n",
        "    if (reset_n == 1'b0)\n",
        "      coreclk_div1 <= 1'b0;\n",
        "    else if (coreclk_div1_en)\n",
        "      coreclk_div1 <= next_coreclk_div1;\n",
        "endmodule\n",
        "\n",
    ]
    patcher = SyntaxErrorPatcher()
    patched = patcher.always_patcher.fix_always_blocks(rtl)

    print("---- before ----")
    print("".join(rtl))
    print("---- after  ----")
    print("".join(patched))


def main() -> None:
    """
    Run all small demos sequentially.

    Each demo prints a "before" and "after" view of a tiny RTL fragment to
    illustrate how the corresponding template patches the structure.
    """

    demo_assign_template()
    demo_if_else_template()
    demo_case_template()
    demo_always_template()


if __name__ == "__main__":
    main()


