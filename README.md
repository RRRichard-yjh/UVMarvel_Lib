# Ⅰ Bus_Protocol_Library

Key Components

1. Protocol skeletons (UVM / SystemVerilog)
   - AHB and APB protocol skeletons for:
     - interface (`*_if.sv`)
     - transaction item (`*_trans.sv`)
     - driver (`*_driver.sv`)
     - monitor (`*_monitor.sv`)
     - sequencer (`*_sequencer.sv`)
     - agent (`*_agent.sv`)
   - Each skeleton encodes stable protocol semantics:
     - request/response structure
     - handshake behaviour
     - basic timing rules
   - Only designated regions (names, widths, config fields, address ranges) are intended to be edited or generated.

2. Generator scripts (LLM-facing skeletons)
   - `generate_ahb_agent.py` and `generate_apb_agent.py`:
     - read a requirements/specification file and a protocol template
     - construct an LLM prompt to reconcile template vs. spec (e.g. interface signals)
     - call a stubbed `get_request(...)` function that users must implement
     - post-process the LLM output into:
       - a combined `*_agent_file.sv`
       - per-class `*.sv` files for interface, driver, monitor, sequencer, agent
   - API details are intentionally omitted:
     - `get_request(...)` raises `NotImplementedError`
     - environment variables use placeholders (`"api base"`, `"api key"`)

3. Directory structure helpers and examples
   - `__init__.py`:
     - exposes helpers such as `get_skeleton_dir("ahb")` and `get_skeleton_dir("apb")`
     - makes it easy for tools to locate protocol skeletons on disk
   - `examples/demo_bus_skeletons.py`:
     - prints available skeleton files per protocol
     - shows the first few lines of the driver skeletons
     - performs no network or API calls

 Directory Structure

- `Bus_Protocol_Library/`
  - `__init__.py`
  - `ahb/`
    - `ahb_if.sv`
    - `ahb_trans.sv`
    - `ahb_driver.sv`
    - `ahb_monitor.sv`
    - `ahb_sequencer.sv`
    - `ahb_agent.sv`
  - `apb/`
    - `apb_if.sv`
    - `apb_trans.sv`
    - `apb_driver.sv`
    - `apb_monitor.sv`
    - `apb_sequencer.sv`
    - `apb_agent.sv`
  - `examples/`
    - `demo_bus_skeletons.py`
  - `generate_ahb_agent.py`
  - `generate_apb_agent.py`

 Getting Started

1. Configure LLM API (optional)
   - Implement `get_request(prompt, ...)` in the generator scripts to call your own LLM endpoint.
   - Set any required environment variables in your own environment (the repository only uses placeholders).

2. Prepare inputs
   - Requirements/specification file (e.g. interface definition and protocol section).
   - Protocol template or skeleton file for AHB/APB.
   - Optional interface description file if you want the LLM to match a concrete virtual interface type.

3. Run the generator skeletons (example)
   - AHB:

     ```bash
     python Bus_Protocol_Library/generate_ahb_agent.py \
       -req ./PATH_TO_REQ_FILE.md \
       -temp ./PATH_TO_AHB_TEMPLATE.sv \
       -interface ./PATH_TO_INTERFACE_FILE.sv
     ```

   - APB:

     ```bash
     python Bus_Protocol_Library/generate_apb_agent.py \
       -req ./PATH_TO_REQ_FILE.md \
       -temp ./PATH_TO_APB_TEMPLATE.sv \
       -interface ./PATH_TO_INTERFACE_FILE.sv
     ```

   - Inspect the generated combined agent file and the split `*.sv` components under your chosen output paths.

4. Use skeletons directly (no LLM)
   - Copy the skeleton `.sv` files under `ahb/` and `apb/` into your UVM environment.
   - Adapt:
     - signal names and widths
     - address ranges and configuration fields
   - Keep the handshake and control-flow structure unchanged to preserve protocol semantics.

---

Ⅱ Verilog_Patch_Template_Library

Key Components

1. Template-based patchers
   - Library of canonical templates for:
     - continuous assignments
     - `if` / `else` chains
     - `case` / `endcase` blocks
     - `always` blocks
     - generate blocks and simple module shells
   - Each template restores minimal syntax while preserving original user logic.

2. High-level patcher API
   - Top-level package exports:
     - `SyntaxErrorPatcher`
     - `AssignStatementPatcher`
     - `IfElsePatcher`
     - `CaseStatementPatcher`
     - `AlwaysBlockPatcher`
     - `GenerateBlockPatcher`
   - Designed to be called on lists of RTL lines collected from larger designs.

3. Example script
   - `examples/patch_demo_basic.py`:
     - demonstrates how to:
       - construct a patcher
       - feed in broken RTL fragments
       - inspect “before” and “after” outputs
     - uses small in-memory examples only; no external dependencies beyond Python and this package.

 Typical Workflow

1. Collect RTL fragments
   - Use your own analysis (for example, coverage or signal tracking) to extract:
     - statements and signals related to a coverage point
     - minimal context needed to identify the originating construct (case block, always block, module, and so on)
   - These fragments may be syntactically incomplete after extraction.

2. Patch with canonical templates
   - Instantiate `SyntaxErrorPatcher` or specific patchers you need.
   - For each fragment or group of fragments:
     - determine which construct they came from
     - select the appropriate template (assign, if/else, case, always, generate)
     - apply the patcher to rebuild headers, trailers, and other missing structure

3. Build a “filtered DUT”
   - Stitch patched fragments together into a filtered version of the DUT:
     - contains only logic needed for the current task
     - is syntactically valid Verilog/SystemVerilog
   - Use this filtered DUT as input to:
     - LLM-based refinement
     - additional RTL analysis or transformation tools

 Getting Started

1. Install and import

   - Add the repository to your `PYTHONPATH`, or install it as a package if you package it yourself.
   - Import from the top-level package:

     ```python
     from Verilog_Patch_Template_Library import SyntaxErrorPatcher
     ```

2. Run the example demo

   ```bash
   python -m Verilog_Patch_Template_Library.examples.patch_demo_basic
   ```

   - Observe the printed “before” and “after” RTL fragments for each supported construct.

3. Integrate into your flow
   - After you have collected coverage-related RTL fragments, call the patcher to:
     - repair and wrap them into canonical constructs
     - produce a filtered, syntactically correct view of the DUT
   - Feed the filtered DUT to your downstream tools or LLMs.
