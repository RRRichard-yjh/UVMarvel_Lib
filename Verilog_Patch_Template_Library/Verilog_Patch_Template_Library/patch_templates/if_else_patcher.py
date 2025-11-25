#!/usr/bin/env python3
"""
If-else patcher.
Repairs dangling else/else-if constructs while preserving nesting.
"""

import re
from typing import List, Dict, Optional


class IfElsePatcher:
    """Patcher for Verilog if/else control structures."""

    def __init__(self):
        self.fixed_count = 0

    def fix_if_else_statements(self, rtl_lines: List[str]) -> List[str]:
        """
        Repair if/else syntax.

        Strategy:
        1. Analyze if/else pairing by indentation and block ranges.
        2. Convert truly dangling `else if` into standalone `if`.
        3. Drop truly dangling bare `else` that has no matching `if`.
        """
        self.fixed_count = 0

        pairs = self._analyze_if_else_pairing(rtl_lines)

        fixed_lines: List[str] = []
        for i, line in enumerate(rtl_lines):
            line_clean = line.strip()

            if self._is_else_statement(line_clean) or self._is_else_if_statement(line_clean):
                if i in pairs and pairs[i]["has_matching_if"]:
                    fixed_lines.append(line)
                else:
                    if self._is_else_if_statement(line_clean):
                        fixed_line = self._convert_else_if_to_if(line)
                        fixed_lines.append(fixed_line)
                        self.fixed_count += 1
                        print(f"   converted dangling 'else if' to 'if' (line {i+1})")
                    else:
                        print(f"   skipped dangling 'else' (line {i+1})")
                        continue
            else:
                fixed_lines.append(line)

        if self.fixed_count > 0:
            print(f"   If-else patch: fixed {self.fixed_count} statements")

        return fixed_lines

    def _analyze_if_else_pairing(self, rtl_lines: List[str]) -> Dict[int, Dict]:
        """
        Analyze if/else pairing.

        Returns a map:
            line_idx -> {'has_matching_if': bool, 'if_line': Optional[int]}
        """
        pairs: Dict[int, Dict] = {}
        active_ifs: List[Dict] = []

        i = 0
        while i < len(rtl_lines):
            line = rtl_lines[i]
            line_clean = line.strip()
            indent = len(self._get_indent(line))

            if not line_clean or line_clean.startswith("//"):
                i += 1
                continue

            if self._is_if_statement(line_clean):
                block_end = self._find_if_block_end(rtl_lines, i)
                active_ifs.append(
                    {
                        "line": i,
                        "indent": indent,
                        "block_end": block_end,
                        "has_else": False,
                    }
                )
                i += 1
                continue

            if self._is_else_if_statement(line_clean):
                matching_if = self._find_matching_if_for_else(active_ifs, indent, i)

                if matching_if is not None:
                    pairs[i] = {"has_matching_if": True, "if_line": matching_if["line"]}
                    matching_if["has_else"] = True

                    block_end = self._find_if_block_end(rtl_lines, i)
                    active_ifs.append(
                        {
                            "line": i,
                            "indent": indent,
                            "block_end": block_end,
                            "has_else": False,
                        }
                    )
                else:
                    pairs[i] = {"has_matching_if": False, "if_line": None}

                i += 1
                continue

            if self._is_else_statement(line_clean):
                matching_if = self._find_matching_if_for_else(active_ifs, indent, i)

                if matching_if is not None:
                    pairs[i] = {"has_matching_if": True, "if_line": matching_if["line"]}
                    matching_if["has_else"] = True
                else:
                    pairs[i] = {"has_matching_if": False, "if_line": None}

                i += 1
                continue

            active_ifs = [ctx for ctx in active_ifs if ctx["block_end"] >= i]

            i += 1

        return pairs

    def _find_matching_if_for_else(
        self,
        active_ifs: List[Dict],
        else_indent: int,
        else_line: int,
    ) -> Optional[Dict]:
        """
        Find matching if for a given else/else-if using:
        - same indentation,
        - if appears before else,
        - if has not yet consumed an else,
        - else follows shortly after the if block.
        """
        for if_ctx in reversed(active_ifs):
            if if_ctx["indent"] == else_indent:
                if if_ctx["block_end"] < else_line <= if_ctx["block_end"] + 5:
                    if not if_ctx["has_else"]:
                        return if_ctx
        return None

    def _find_if_block_end(self, rtl_lines: List[str], if_idx: int) -> int:
        """
        Find end index of an if block (without the else part).
        If there is a begin, find the matching end; otherwise find
        the next line with a semicolon.
        """
        line = rtl_lines[if_idx].strip()

        has_begin = False
        search_start = if_idx + 1

        for i in range(if_idx + 1, min(if_idx + 5, len(rtl_lines))):
            check_line = rtl_lines[i].strip()
            if check_line == "begin" or check_line.endswith("begin"):
                has_begin = True
                search_start = i
                break
            if check_line and not check_line.startswith("//"):
                break

        if has_begin:
            depth = 1
            for i in range(search_start + 1, len(rtl_lines)):
                check_line = rtl_lines[i].strip()

                if check_line == "begin" or check_line.endswith("begin"):
                    depth += 1
                elif check_line == "end" or check_line.startswith("end"):
                    depth -= 1
                    if depth == 0:
                        return i

            return len(rtl_lines) - 1

        for i in range(if_idx + 1, min(if_idx + 10, len(rtl_lines))):
            if ";" in rtl_lines[i]:
                return i

        return min(if_idx + 3, len(rtl_lines) - 1)

    def _is_if_statement(self, line_clean: str) -> bool:
        """Detect if statements that are not else-if."""
        if_pattern = r"\bif\s*\("
        return bool(re.search(if_pattern, line_clean)) and not line_clean.startswith("else")

    def _is_else_if_statement(self, line_clean: str) -> bool:
        """Detect else-if statements."""
        return bool(re.search(r"\belse\s+if\s*\(", line_clean))

    def _is_else_statement(self, line_clean: str) -> bool:
        """Detect bare else (not else-if)."""
        if "else if" in line_clean:
            return False

        else_patterns = [
            r"\belse\s*$",
            r"\belse\s+begin",
        ]
        return any(re.search(pattern, line_clean) for pattern in else_patterns)

    def _convert_else_if_to_if(self, line: str) -> str:
        """Turn `else if` into a standalone `if`."""
        return re.sub(r"\belse\s+if\s*\(", "if (", line)

    def _get_indent(self, line: str) -> str:
        """Return indentation prefix for a line."""
        indent = ""
        for char in line:
            if char in [" ", "\t"]:
                indent += char
            else:
                break
        return indent

    def get_summary(self) -> str:
        """Return a human-readable summary of performed fixes."""
        if self.fixed_count > 0:
            return f"If-else patch: fixed {self.fixed_count} statements"
        return "If-else patch: no changes needed"



