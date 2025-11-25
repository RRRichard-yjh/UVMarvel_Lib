#!/usr/bin/env python3
"""
Generate-block patcher.
Wraps orphaned labeled begin blocks into proper generate/endgenerate regions.
"""

import re
from typing import List, Dict


class GenerateBlockPatcher:
    """Patcher for Verilog generate blocks."""

    def __init__(self):
        self.fixes_made = 0
        self.orphan_blocks_fixed = 0
        self.missing_genvar_added = 0

    def fix_generate_blocks(self, rtl_lines: List[str]) -> List[str]:
        """Repair generate-related syntax around labeled begin blocks."""
        fixed_lines: List[str] = []
        i = 0

        while i < len(rtl_lines):
            line = rtl_lines[i]
            line_clean = line.strip()

            if self._is_orphan_generate_block(line_clean):
                blocks_info = self._collect_orphan_blocks(rtl_lines, i)

                if blocks_info["blocks"]:
                    wrapped_lines = self._wrap_with_generate(blocks_info, rtl_lines)
                    fixed_lines.extend(wrapped_lines)

                    i = blocks_info["end_idx"] + 1
                    self.orphan_blocks_fixed += len(blocks_info["blocks"])
                    print(
                        f"   wrapped {len(blocks_info['blocks'])} "
                        f"orphan begin blocks into a generate region"
                    )
                else:
                    fixed_lines.append(line)
                    i += 1
            else:
                fixed_lines.append(line)
                i += 1

        return fixed_lines

    def _is_orphan_generate_block(self, line_clean: str) -> bool:
        """Detect lines of the form 'begin: label' that are not clearly inside generate."""
        return re.match(r"^\s*begin\s*:\s*\w+\s*$", line_clean) is not None

    def _collect_orphan_blocks(self, rtl_lines: List[str], start_idx: int) -> Dict:
        """Collect consecutive labeled begin blocks that should be wrapped in generate."""
        blocks: List[Dict] = []
        current_idx = start_idx
        genvar_needed = False

        while current_idx < len(rtl_lines):
            line = rtl_lines[current_idx]
            line_clean = line.strip()

            if self._is_orphan_generate_block(line_clean):
                block_info = self._collect_single_block(rtl_lines, current_idx)
                if block_info:
                    blocks.append(block_info)
                    current_idx = block_info["end_idx"] + 1

                    if not genvar_needed and self._block_needs_genvar(block_info, rtl_lines):
                        genvar_needed = True
                else:
                    break
            else:
                break

        return {
            "blocks": blocks,
            "start_idx": start_idx,
            "end_idx": current_idx - 1 if blocks else start_idx,
            "needs_genvar": genvar_needed,
        }

    def _collect_single_block(self, rtl_lines: List[str], start_idx: int) -> Dict:
        """Collect a single labeled begin block [begin:label ...]."""
        if start_idx >= len(rtl_lines):
            return None

        start_line = rtl_lines[start_idx].strip()
        label_match = re.match(r"^\s*begin\s*:\s*(\w+)\s*$", start_line)
        if not label_match:
            return None

        label = label_match.group(1)
        current_idx = start_idx + 1

        while current_idx < len(rtl_lines):
            line = rtl_lines[current_idx]
            line_clean = line.strip()

            if self._is_orphan_generate_block(line_clean):
                break

            if line_clean.startswith(("endmodule", "module ", "always", "assign")) or re.match(
                r"^\s*end\s*;?\s*$", line_clean
            ):
                break

            current_idx += 1

        return {
            "label": label,
            "start_idx": start_idx,
            "end_idx": current_idx - 1,
            "content_lines": rtl_lines[start_idx:current_idx],
        }

    def _block_needs_genvar(self, block_info: Dict, rtl_lines: List[str]) -> bool:
        """Heuristic: does this block appear to use an index variable like [I] or [i]?"""
        for i in range(block_info["start_idx"], block_info["end_idx"] + 1):
            if i < len(rtl_lines):
                line = rtl_lines[i]
                if re.search(r"\[[IiJjKk]\]|\[idx\]|\[index\]", line):
                    return True
        return False

    def _wrap_with_generate(self, blocks_info: Dict, rtl_lines: List[str]) -> List[str]:
        """Wrap collected orphan blocks into a generate/endgenerate region."""
        wrapped_lines: List[str] = []
        base_indent = self._get_indent(rtl_lines[blocks_info["start_idx"]])

        if blocks_info["needs_genvar"]:
            wrapped_lines.append(f"{base_indent}genvar I;\n")
            self.missing_genvar_added += 1

        wrapped_lines.append(f"{base_indent}generate\n")

        if blocks_info["needs_genvar"]:
            loop_range = self._infer_generate_loop_range(blocks_info, rtl_lines)
            wrapped_lines.append(
                f"{base_indent}  for (I = 0; I < {loop_range}; I = I + 1) begin\n"
            )

        for block in blocks_info["blocks"]:
            for i in range(block["start_idx"], block["end_idx"] + 1):
                if i < len(rtl_lines):
                    original_line = rtl_lines[i]
                    indented_line = f"  {original_line}"
                    wrapped_lines.append(indented_line)

        if blocks_info["needs_genvar"]:
            wrapped_lines.append(f"{base_indent}  end\n")

        wrapped_lines.append(f"{base_indent}endgenerate\n")

        return wrapped_lines

    def _infer_generate_loop_range(self, blocks_info: Dict, rtl_lines: List[str]) -> str:
        """Infer a loop bound for generate from parameter declarations, if any."""
        for line in rtl_lines[:100]:
            line_clean = line.strip()
            param_match = re.search(r"parameter\s+(\w+)\s*=\s*(\d+)", line_clean)
            if param_match:
                param_name = param_match.group(1)
                if any(
                    keyword in param_name.lower()
                    for keyword in ["width", "size", "num", "count"]
                ):
                    return param_name

        return "8"

    def _get_indent(self, line: str) -> str:
        """Return indentation prefix."""
        return line[: len(line) - len(line.lstrip())]

    def get_summary(self) -> str:
        """Return a human-readable summary of performed fixes."""
        summary_parts: List[str] = []
        if self.orphan_blocks_fixed > 0:
            summary_parts.append(f"wrapped {self.orphan_blocks_fixed} orphan blocks")
        if self.missing_genvar_added > 0:
            summary_parts.append(f"added {self.missing_genvar_added} genvar declarations")

        if summary_parts:
            return "Generate patch: " + ", ".join(summary_parts)
        return "Generate patch: no changes needed"



