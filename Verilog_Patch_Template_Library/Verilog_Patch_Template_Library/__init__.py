"""
Verilog Patch Template Library

Canonical patchers for repairing trimmed Verilog RTL into
syntactically well-formed assign / if-else / case / always / generate
constructs.

This top-level __init__ defines the public API of the whole library.
Users are expected to import patchers directly from this package, e.g.:
    from Verilog_Patch_Template_Library import SyntaxErrorPatcher
"""

from .patch_templates.assign_statement_patcher import AssignStatementPatcher
from .patch_templates.if_else_patcher import IfElsePatcher
from .patch_templates.case_statement_patcher import CaseStatementPatcher
from .patch_templates.always_block_patcher import AlwaysBlockPatcher
from .patch_templates.generate_block_patcher import GenerateBlockPatcher
from .patch_templates.syntax_error_patcher import SyntaxErrorPatcher

__all__ = [
    "AssignStatementPatcher",
    "IfElsePatcher",
    "CaseStatementPatcher",
    "AlwaysBlockPatcher",
    "GenerateBlockPatcher",
    "SyntaxErrorPatcher",
]



