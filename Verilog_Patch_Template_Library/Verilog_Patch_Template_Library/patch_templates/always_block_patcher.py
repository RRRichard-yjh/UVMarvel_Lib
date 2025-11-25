#!/usr/bin/env python3
"""
Always-block patcher.
Repairs obviously incomplete always headers (missing sensitivity lists, etc.).
"""

import re
import os
from typing import List, Dict, Optional


class AlwaysBlockPatcher:
    """Patcher for Verilog always blocks."""

    def __init__(self, source_file_path: Optional[str] = None):
        self.source_file_path = source_file_path
        self.source_lines: List[str] = []
        self.source_always_blocks: Dict[str, List[Dict]] = {}
        self.fixes_made = 0
        self.incomplete_blocks_fixed = 0
        self.orphan_begin_blocks_fixed = 0

        if source_file_path and os.path.exists(source_file_path):
            self._load_source_file()
            self._extract_source_always_blocks()

    def _load_source_file(self) -> None:
        """Load original RTL file for optional structural hints."""
        try:
            with open(self.source_file_path, "r", encoding="utf-8") as f:
                self.source_lines = f.readlines()
            print(
                f"   loaded source file: "
                f"{self.source_file_path} ({len(self.source_lines)} lines)"
            )
        except Exception as e:
            print(f"   failed to load source file: {e}")

    def _extract_source_always_blocks(self) -> None:
        """Extract always-block metadata from the source file (grouped by module)."""
        current_module: Optional[str] = None
        i = 0

        while i < len(self.source_lines):
            line = self.source_lines[i].strip()

            if line.startswith("module "):
                match = re.match(r"module\s+(\w+)", line)
                if match:
                    current_module = match.group(1)
                    self.source_always_blocks[current_module] = []

            if line.startswith("always") and current_module:
                always_decl = line

                begin_idx = -1
                for j in range(i + 1, min(i + 5, len(self.source_lines))):
                    if "begin" in self.source_lines[j]:
                        begin_idx = j
                        break

                if begin_idx != -1:
                    signature_lines: List[str] = []
                    for k in range(begin_idx + 1, min(begin_idx + 10, len(self.source_lines))):
                        sig_line = self.source_lines[k].strip()
                        if sig_line and not sig_line.startswith("//") and sig_line != "begin":
                            signature_lines.append(sig_line)
                            if len(signature_lines) >= 3:
                                break

                    self.source_always_blocks[current_module].append(
                        {
                            "always_decl": always_decl,
                            "signature": signature_lines,
                            "line_num": i,
                        }
                    )

            i += 1

        total_blocks = sum(len(blocks) for blocks in self.source_always_blocks.values())
        print(
            f"   extracted {total_blocks} always blocks "
            f"from {len(self.source_always_blocks)} modules in source"
        )

    def fix_always_blocks(self, rtl_lines: List[str]) -> List[str]:
        """
        Repair always-block headers.

        Only obviously incomplete headers are changed (e.g. 'always', 'always@').
        Body lines are preserved.
        """
        fixed_lines: List[str] = []
        i = 0

        while i < len(rtl_lines):
            line = rtl_lines[i]
            line_clean = line.strip()

            if self._is_incomplete_always_block(line_clean):
                fixed_line = self._fix_incomplete_always_block(line, rtl_lines, i)
                fixed_lines.append(fixed_line)
                self.incomplete_blocks_fixed += 1
                print(f"   fixed incomplete always header (line {i+1})")
            else:
                fixed_lines.append(line)

            i += 1

        return fixed_lines

    def _is_incomplete_always_block(self, line_clean: str) -> bool:
        """Detect obviously incomplete always headers."""
        patterns = [
            r"\balways\s*$",
            r"\balways\s*\(\s*\)$",
            r"\balways\s*@\s*$",
            r"\balways\s*@\s*\(\s*\)$",
        ]
        return any(re.search(pattern, line_clean) for pattern in patterns)

    def _fix_incomplete_always_block(
        self,
        line: str,
        rtl_lines: List[str],
        line_idx: int,
    ) -> str:
        """Patch incomplete always headers with a reasonable sensitivity list."""
        line_clean = line.strip()
        indent = self._get_indent(line)

        clock_signal = self._detect_clock_signal(rtl_lines)
        has_seq = self._has_sequential_logic_nearby(rtl_lines, line_idx)

        # Prefer a sequential-style header when we can detect a clock and
        # see non-blocking assignments in the nearby body.
        if re.search(r"\balways\s*$", line_clean):
            if has_seq and clock_signal:
                return f"{indent}always @(posedge {clock_signal}) begin\n"
            return f"{indent}always @(*) begin\n"

        if re.search(r"\balways\s*\(\s*\)$", line_clean):
            return line.replace("always ()", "always @(*)")

        if re.search(r"\balways\s*@\s*$", line_clean):
            if has_seq and clock_signal:
                return f"{indent}always @(posedge {clock_signal}) begin\n"
            return f"{indent}always @(*) begin\n"

        if re.search(r"\balways\s*@\s*\(\s*\)$", line_clean):
            return line.replace("always @()", "always @(*)")

        if has_seq and clock_signal:
            return f"{indent}always @(posedge {clock_signal}) begin\n"

        return line

    def _detect_clock_signal(self, rtl_lines: List[str]) -> str:
        """Heuristic clock signal detection from module header or body."""
        for line in rtl_lines[:50]:
            line_clean = line.strip().lower()
            if "input" in line_clean and ("clk" in line_clean or "clock" in line_clean):
                match = re.search(r"input.*?(\w*clk\w*)", line_clean)
                if match:
                    return match.group(1)

        common_clocks = ["clk", "clock", "aclk", "pclk"]
        for clock in common_clocks:
            for line in rtl_lines[:100]:
                if f"posedge {clock}" in line or f"negedge {clock}" in line:
                    return clock

        return "clk"

    def _has_sequential_logic_nearby(self, rtl_lines: List[str], line_idx: int) -> bool:
        """Check nearby lines for non-blocking assignments as a hint of sequential logic."""
        start = max(0, line_idx - 5)
        end = min(len(rtl_lines), line_idx + 5)

        for i in range(start, end):
            if "<=" in rtl_lines[i] and not rtl_lines[i].strip().startswith("//"):
                return True
        return False

    def _get_indent(self, line: str) -> str:
        """Return indentation prefix."""
        return line[: len(line) - len(line.lstrip())]

    def get_summary(self) -> str:
        """Return a human-readable summary of performed fixes."""
        if self.incomplete_blocks_fixed > 0:
            return f"Always patch: fixed {self.incomplete_blocks_fixed} incomplete always blocks"
        return "Always patch: no changes needed"



