#!/usr/bin/env python3
"""
Syntax error patcher.
Coordinates the individual patchers for assign, case, if-else, always, and generate.
"""

from typing import List

from .case_statement_patcher import CaseStatementPatcher
from .if_else_patcher import IfElsePatcher
from .always_block_patcher import AlwaysBlockPatcher
from .assign_statement_patcher import AssignStatementPatcher
from .generate_block_patcher import GenerateBlockPatcher


class SyntaxErrorPatcher:
    """High-level orchestrator that applies all patchers in a fixed order."""

    def __init__(self):
        self.case_patcher = CaseStatementPatcher()
        self.if_else_patcher = IfElsePatcher()
        self.always_patcher = AlwaysBlockPatcher()
        self.assign_patcher = AssignStatementPatcher()
        self.generate_patcher = GenerateBlockPatcher()
        self.total_fixes = 0

    def fix_all_syntax_errors(self, rtl_lines: List[str]) -> List[str]:
        """
        Run all patchers in sequence on the given RTL lines.

        Order:
          1) Assign statement normalization and repair.
          2) Case statement repair (empty-case pruning and endcase completion).
          3) If-else repair (dangling else-if / else).
          4) Always-block header repair.
          5) Generate-block wrapping.
          6) Final cleanup of obviously broken operator-only lines.
        """
        print(f"Starting syntax patching, original lines: {len(rtl_lines)}")

        print("   Step 1: patch assign statements")
        rtl_lines = self.assign_patcher.fix_assign_statements(rtl_lines)
        self._update_stats(self.assign_patcher.get_summary())

        print("   Step 2: patch case statements")
        rtl_lines = self.case_patcher.fix_case_statements(rtl_lines)
        self._update_stats(self.case_patcher.get_summary())

        print("   Step 3: patch if-else statements")
        rtl_lines = self.if_else_patcher.fix_if_else_statements(rtl_lines)
        self._update_stats(self.if_else_patcher.get_summary())

        print("   Step 4: patch always blocks")
        rtl_lines = self.always_patcher.fix_always_blocks(rtl_lines)
        self._update_stats(self.always_patcher.get_summary())

        print("   Step 5: patch generate blocks")
        rtl_lines = self.generate_patcher.fix_generate_blocks(rtl_lines)
        self._update_stats(self.generate_patcher.get_summary())

        print("   Step 6: final cleanup")
        rtl_lines = self._conservative_cleanup(rtl_lines)

        print(f"Syntax patching finished, final lines: {len(rtl_lines)}")
        return rtl_lines

    def _update_stats(self, summary: str) -> None:
        """Accumulate statistics from sub-patchers by parsing their summaries."""
        if summary and "fixed" in summary:
            print(f"   {summary}")
            import re

            match = re.search(r"fixed\s*(\d+)", summary)
            if match:
                self.total_fixes += int(match.group(1))

    def _conservative_cleanup(self, rtl_lines: List[str]) -> List[str]:
        """
        Final cleanup pass:
        - remove lines that are clearly just stray operators.
        - inject missing genvar declarations when needed.
        """
        cleaned_lines: List[str] = []
        cleanup_count = 0

        for i, line in enumerate(rtl_lines):
            line_clean = line.strip()

            if self._is_obvious_orphan_operator(line_clean):
                cleanup_count += 1
                print(f"   removed orphan operator (line {i+1}): {line_clean[:20]}...")
                continue

            if self._needs_genvar_declaration(line_clean, cleaned_lines):
                genvar_line = self._create_genvar_declaration(line)
                cleaned_lines.append(genvar_line)
                cleanup_count += 1
                print(f"   inserted genvar declaration (line {len(cleaned_lines)})")

            cleaned_lines.append(line)

        if cleanup_count > 0:
            print(f"   Final cleanup: processed {cleanup_count} issues")

        return cleaned_lines

    def _is_obvious_orphan_operator(self, line_clean: str) -> bool:
        """Detect lines that contain only a single operator token."""
        if not line_clean:
            return False

        orphan_patterns = [
            r"^\s*[&|^~]\s*$",
            r"^\s*[+\-*/]\s*$",
            r"^\s*[<>=!]\s*$",
            r"^\s*[{}]\s*$",
            r"^\s*:\s*$",
            r"^\s*\?\s*$",
        ]

        import re as _re

        return any(_re.match(pattern, line_clean) for pattern in orphan_patterns)

    def _needs_genvar_declaration(self, line_clean: str, previous_lines: List[str]) -> bool:
        """Detect places where a missing 'genvar' declaration should be injected."""
        if "genvar" in line_clean and "generate" not in line_clean:
            for prev_line in previous_lines[-20:]:
                if "genvar" in prev_line.strip():
                    return False
            return True
        return False

    def _create_genvar_declaration(self, line: str) -> str:
        """Create a genvar declaration line aligned with the given context."""
        indent = self._get_indent(line)
        return f"{indent}genvar i;\n"

    def _get_indent(self, line: str) -> str:
        """Return indentation prefix of a line."""
        return line[: len(line) - len(line.lstrip())]

    def get_total_summary(self) -> str:
        """Return an aggregate summary across all patchers."""
        return f"Syntax patch: fixed {self.total_fixes} issues"



