#!/usr/bin/env python3
"""
Case statement patcher (refactored version).
Provides:
  1) Removal of structurally empty case blocks.
  2) Completion of missing endcase tokens.
"""

import re
from typing import List, Dict, Tuple


class CaseStatementPatcher:
    """Patcher for Verilog case statements."""

    def __init__(self):
        # stack for nested case blocks
        self.case_stack: List[Dict] = []
        self.fixed_count = 0
        self.removed_count = 0

    def fix_case_statements(self, rtl_lines: List[str]) -> List[str]:
        """
        Repair case statement syntax.

        Strategy:
        1. Identify all case...endcase regions.
        2. Remove case regions that contain no executable content.
        3. Insert missing endcase tokens where indentation suggests termination.
        """
        self.fixed_count = 0
        self.removed_count = 0

        cleaned = self._remove_empty_case_blocks(rtl_lines)
        fixed = self._fix_missing_endcase(cleaned)

        if self.removed_count > 0:
            print(f"   Case patch: removed {self.removed_count} empty case blocks")
        if self.fixed_count > 0:
            print(f"   Case patch: inserted {self.fixed_count} missing 'endcase'")

        return fixed

    def _remove_empty_case_blocks(self, rtl_lines: List[str]) -> List[str]:
        """Remove case blocks that only contain labels, comments, or blank lines."""
        case_structures = self._identify_case_structures(rtl_lines)

        empty_case_ranges: List[Tuple[int, int]] = []
        for case_struct in case_structures:
            if self._is_empty_case_structure(rtl_lines, case_struct):
                empty_case_ranges.append((case_struct["start"], case_struct["end"]))
                self.removed_count += 1
                print(
                    "   mark empty case block for removal: "
                    f"lines {case_struct['start']}-{case_struct['end']}"
                )

        if not empty_case_ranges:
            return rtl_lines

        empty_case_ranges.sort(key=lambda x: x[0], reverse=True)
        filtered = list(rtl_lines)

        for start_idx, end_idx in empty_case_ranges:
            del filtered[start_idx : end_idx + 1]

        return filtered

    def _identify_case_structures(self, rtl_lines: List[str]) -> List[Dict[str, int]]:
        """Locate all case...endcase regions."""
        case_structures: List[Dict[str, int]] = []
        i = 0

        while i < len(rtl_lines):
            line = rtl_lines[i].strip()

            if re.search(r"\bcase\s*\(", line):
                case_start = i
                j = i + 1
                case_end = None
                while j < len(rtl_lines):
                    check_line = rtl_lines[j].strip()
                    if check_line == "endcase" or check_line.startswith("endcase"):
                        case_end = j
                        break
                    j += 1

                if case_end is not None:
                    case_structures.append({"start": case_start, "end": case_end})
                    i = case_end

            i += 1

        return case_structures

    def _is_empty_case_structure(self, rtl_lines: List[str], case_struct: Dict[str, int]) -> bool:
        """Decide whether a case block has no executable statements."""
        start_idx = case_struct["start"]
        end_idx = case_struct["end"]

        for i in range(start_idx + 1, end_idx):
            if i >= len(rtl_lines):
                continue

            line = rtl_lines[i].strip()

            if not line or line.startswith("//"):
                continue

            if line.startswith("default:") or re.match(r"\s*\{[^}]+\}\s*:\s*$", line):
                continue

            if "=" in line or any(keyword in line for keyword in ["begin", "if", "for", "while"]):
                return False

        return True

    def _fix_missing_endcase(self, rtl_lines: List[str]) -> List[str]:
        """Insert endcase tokens where case blocks appear to terminate."""
        self.case_stack = []
        fixed_lines: List[str] = []

        i = 0
        while i < len(rtl_lines):
            line = rtl_lines[i]
            line_clean = line.strip()

            if re.search(r"\bcase\s*\(", line_clean):
                fixed_lines.append(line)
                self.case_stack.append(
                    {
                        "line_num": i,
                        "indent": self._get_indent(line),
                        "found_endcase": False,
                    }
                )

            elif line_clean == "endcase" or line_clean.startswith("endcase"):
                fixed_lines.append(line)
                if self.case_stack:
                    self.case_stack[-1]["found_endcase"] = True
                    self.case_stack.pop()

            elif self._should_check_for_missing_endcase(line_clean) and self.case_stack:
                missing_endcases = self._check_missing_endcases(line)
                for endcase_indent in missing_endcases:
                    fixed_lines.append(f"{endcase_indent}endcase")
                    self.fixed_count += 1
                    print("   inserted missing 'endcase'")

                fixed_lines.append(line)

            else:
                fixed_lines.append(line)

            i += 1

        while self.case_stack:
            case_info = self.case_stack.pop()
            if not case_info["found_endcase"]:
                fixed_lines.append(f"{case_info['indent']}endcase")
                self.fixed_count += 1
                print("   inserted missing 'endcase' at end of file")

        return fixed_lines

    def _should_check_for_missing_endcase(self, line_clean: str) -> bool:
        """Heuristic: lines that likely mark the end of a case block."""
        check_keywords = [
            "always",
            "assign",
            "wire ",
            "reg ",
            "input ",
            "output ",
            "module ",
            "endmodule",
            "begin",
            "end",
            "if ",
            "else",
        ]
        return any(line_clean.startswith(keyword) for keyword in check_keywords)

    def _check_missing_endcases(self, line: str) -> List[str]:
        """Determine how many endcase tokens to insert and with which indentation."""
        missing_endcases: List[str] = []
        line_indent = self._get_indent(line)

        while self.case_stack:
            case_info = self.case_stack[-1]
            if not case_info["found_endcase"]:
                if len(line_indent) <= len(case_info["indent"]):
                    missing_endcases.append(case_info["indent"])
                    case_info["found_endcase"] = True
                    self.case_stack.pop()
                else:
                    break
            else:
                break

        return missing_endcases

    def _get_indent(self, line: str) -> str:
        """Return indentation prefix of a line."""
        indent = ""
        for ch in line:
            if ch in (" ", "\t"):
                indent += ch
            else:
                break
        return indent

    def get_summary(self) -> str:
        """Return a human-readable summary of performed fixes."""
        summary_parts: List[str] = []
        if self.removed_count > 0:
            summary_parts.append(f"removed {self.removed_count} empty case blocks")
        if self.fixed_count > 0:
            summary_parts.append(f"inserted {self.fixed_count} missing 'endcase'")

        if summary_parts:
            return "Case patch: " + ", ".join(summary_parts)
        return "Case patch: no changes needed"



