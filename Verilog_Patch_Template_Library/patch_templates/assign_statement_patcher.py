#!/usr/bin/env python3
"""
Assign statement patcher.
Normalizes and repairs multi-line or malformed assign statements.
"""

import re
from typing import List, Set, Dict, Tuple


class AssignStatementPatcher:
    """Patcher for Verilog assign statements."""

    def __init__(self):
        self.fixed_count = 0
        self.merged_count = 0

    def fix_assign_statements(self, rtl_lines: List[str]) -> List[str]:
        """
        Repair assign statement syntax.

        Strategy:
        1. Merge multi-line assign statements.
        2. Complete incomplete assign statements.
        3. Repair broken ternary (?:) fragments.
        4. Add missing semicolons.
        5. Split mixed assign statements on the same line.
        6. Fix accidental double equals.
        """
        self.fixed_count = 0
        self.merged_count = 0
        fixed_lines: List[str] = []

        i = 0
        while i < len(rtl_lines):
            line = rtl_lines[i]
            line_clean = line.strip()

            # assign statement start
            if self._is_assign_start(line_clean):
                # collect full (possibly multi-line) assign
                complete_assign, lines_consumed = self._collect_complete_assign(rtl_lines, i)

                if lines_consumed > 1:
                    self.merged_count += 1
                    print(f"   merged multi-line assign ({lines_consumed} lines -> 1 line)")

                # check if there are multiple assigns on this merged line
                multiple_assigns = self._split_multiple_assigns(complete_assign)
                if len(multiple_assigns) > 1:
                    self.fixed_count += 1
                    print(
                        f"   split multiple assign statements on one line "
                        f"({len(multiple_assigns)} statements)"
                    )
                    for assign_stmt in multiple_assigns:
                        fixed_assign = self._fix_assign_statement(assign_stmt)
                        if fixed_assign.strip():
                            fixed_lines.append(fixed_assign)
                else:
                    fixed_assign = self._fix_assign_statement(complete_assign)
                    if fixed_assign != complete_assign:
                        self.fixed_count += 1
                        print("   fixed assign statement syntax")

                    if fixed_assign.strip():
                        fixed_lines.append(fixed_assign)

                i += lines_consumed

            # orphan ternary part on its own line
            elif self._is_orphan_ternary_part(line_clean):
                if fixed_lines and self._can_merge_with_previous(fixed_lines[-1], line):
                    merged_line = self._merge_ternary_lines(fixed_lines[-1], line)
                    fixed_lines[-1] = merged_line
                    self.fixed_count += 1
                    print("   merged orphan ternary/operator line")
                else:
                    fixed_lines.append(line)
                i += 1

            # incomplete assignment (e.g. line ends with '=')
            elif self._is_incomplete_assignment(line_clean):
                fixed_line = self._fix_incomplete_assignment(line)
                fixed_lines.append(fixed_line)
                if fixed_line != line:
                    self.fixed_count += 1
                    print("   fixed incomplete assignment")
                i += 1

            else:
                fixed_lines.append(line)
                i += 1

        if self.fixed_count > 0 or self.merged_count > 0:
            print(
                f"   Assign patch: fixed {self.fixed_count} issues, "
                f"merged {self.merged_count} multi-line assigns"
            )

        return fixed_lines

    def _is_assign_start(self, line_clean: str) -> bool:
        """Detect the start of an assign statement."""
        return line_clean.startswith('assign ') and '=' in line_clean

    def _collect_complete_assign(self, rtl_lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Collect a full assign statement that may span multiple lines."""
        lines_consumed = 1
        assign_parts = [rtl_lines[start_idx].strip()]

        first_line = assign_parts[0]
        needs_continuation = (
            not first_line.endswith(';')
            or first_line.endswith(('|', '&', '^', '+', '-', '?', ':', '='))
        )

        if needs_continuation:
            i = start_idx + 1
            while i < len(rtl_lines):
                next_line = rtl_lines[i].strip()

                # skip empty lines and comments as part of the multi-line construct
                if not next_line or next_line.startswith('//'):
                    i += 1
                    lines_consumed += 1
                    continue

                # stop if a new statement starts and the line is not a continuation
                if self._is_new_statement_start(next_line) and not self._is_continuation_line(next_line):
                    break

                assign_parts.append(next_line)
                lines_consumed += 1

                if next_line.endswith(';'):
                    break

                i += 1

        complete_assign = ' '.join(assign_parts)
        return complete_assign, lines_consumed

    def _is_new_statement_start(self, line_clean: str) -> bool:
        """Detect the beginning of a new statement."""
        new_statement_keywords = [
            'assign ', 'always', 'wire ', 'reg ', 'input ', 'output ',
            'module ', 'endmodule', 'begin', 'end', 'if ', 'case ',
        ]
        return any(line_clean.startswith(keyword) for keyword in new_statement_keywords)

    def _split_multiple_assigns(self, line: str) -> List[str]:
        """
        Split multiple assign statements that were merged into a single line.
        For example: 'assign a = b assign c = d;'
        """
        parts: List[str] = []
        current = line.strip()

        pattern = r'(assign\s+[^=]+=\s*[^;]+?)\s+(assign\s+.*)'
        match = re.search(pattern, current)
        if match:
            first_assign = match.group(1).strip()
            rest = match.group(2).strip()

            if not first_assign.endswith(';'):
                first_assign += ';'

            parts.append(first_assign)
            parts.append(rest)
            return parts

        return [line]

    def _fix_assign_statement(self, assign_line: str) -> str:
        """Fix syntax issues inside a single assign statement."""
        if not assign_line.strip():
            return assign_line

        fixed_line = assign_line

        fixed_line = self._fix_complex_ternary(fixed_line)

        # '< =' -> '<='
        fixed_line = re.sub(r'<\s*=', '<=', fixed_line)

        # first ensure ternary operator structure is complete on the expression
        fixed_line = self._fix_ternary_operator(fixed_line)

        # then add semicolon if missing, so we do not append ternary pieces after ';'
        if not fixed_line.strip().endswith(';'):
            fixed_line = fixed_line.rstrip() + ';'

        # normalize whitespace
        fixed_line = re.sub(r'\s+', ' ', fixed_line)
        fixed_line = re.sub(r'\s*=\s*', ' = ', fixed_line)
        fixed_line = re.sub(r'\s*\?\s*', ' ? ', fixed_line)
        fixed_line = re.sub(r'\s*:\s*', ' : ', fixed_line)

        # fix ' =  =' -> '=='
        fixed_line = re.sub(r'=\s+=', '==', fixed_line)

        return fixed_line

    def _fix_complex_ternary(self, line: str) -> str:
        """Handle complex or malformed ternary expressions."""
        pattern = r'\?\s*else\s+if\s*\([^)]+\)\s*[^;:]+;\s*:'
        if re.search(pattern, line):
            line = re.sub(
                r'\?\s*else\s+if\s*\([^)]+\)\s*[^;:]+;\s*:',
                " ? 1'b0 :",
                line,
            )
        return line

    def _fix_ternary_operator(self, line: str) -> str:
        """Ensure each '?' has a matching ':' by appending a default branch."""
        question_count = line.count('?')
        colon_count = line.count(':')

        if question_count > colon_count:
            for _ in range(question_count - colon_count):
                line += " : 1'b0"

        return line

    def _is_orphan_ternary_part(self, line_clean: str) -> bool:
        """Detect a line that only contains part of a ternary or operator chain."""
        ternary_patterns = [
            r'^\s*\?\s*',
            r'^\s*:\s*',
            r'^\s*\|\s*',
            r'^\s*&\s*',
            r'^\s*\^\s*',
        ]
        return any(re.match(pattern, line_clean) for pattern in ternary_patterns)

    def _can_merge_with_previous(self, prev_line: str, curr_line: str) -> bool:
        """Decide whether current line can be merged with previous line."""
        prev_clean = prev_line.strip()
        curr_clean = curr_line.strip()

        if (
            prev_clean.endswith(('?', '&', '|', '^', '+', '-'))
            or curr_clean.startswith(('?', ':', '&', '|', '^', '+', '-'))
        ):
            return True

        if prev_clean.startswith('assign ') and not prev_clean.endswith(';'):
            return True

        return False

    def _merge_ternary_lines(self, prev_line: str, curr_line: str) -> str:
        """Merge two consecutive lines that belong to a single ternary expression."""
        return prev_line.rstrip() + ' ' + curr_line.strip()

    def _is_incomplete_assignment(self, line_clean: str) -> bool:
        """Detect assignments that end with an operator and miss the right-hand side."""
        incomplete_patterns = [
            r'=\s*$',
            r'<=\s*$',
            r'\?\s*$',
            r':\s*$',
        ]
        return any(re.search(pattern, line_clean) for pattern in incomplete_patterns)

    def _fix_incomplete_assignment(self, line: str) -> str:
        """Patch incomplete assignments with a default literal."""
        line_clean = line.strip()

        if line_clean.endswith('='):
            return line.rstrip() + " 1'b0;"
        if line_clean.endswith('<='):
            return line.rstrip() + " 1'b0;"
        if line_clean.endswith('?'):
            return line.rstrip() + " 1'b1 : 1'b0;"
        if line_clean.endswith(':'):
            return line.rstrip() + " 1'b0;"

        return line

    def _is_continuation_line(self, line_clean: str) -> bool:
        """Detect continuation lines that belong to a previous statement."""
        continuation_patterns = [
            r'^\s*\|\s*',
            r'^\s*&\s*',
            r'^\s*\^\s*',
            r'^\s*\+\s*',
            r'^\s*-\s*',
            r'^\s*\?\s*',
            r'^\s*:\s*',
            r'^\s*==\s*',
            r'^\s*!=\s*',
        ]
        return any(re.match(pattern, line_clean) for pattern in continuation_patterns)

    def get_summary(self) -> str:
        """Return a human-readable summary of performed fixes."""
        if self.fixed_count > 0 or self.merged_count > 0:
            return (
                f"Assign patch: fixed {self.fixed_count} issues, "
                f"merged {self.merged_count} multi-line assigns"
            )
        return "Assign patch: no changes needed"



