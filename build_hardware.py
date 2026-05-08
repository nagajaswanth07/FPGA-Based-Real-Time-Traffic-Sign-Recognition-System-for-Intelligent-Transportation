"""
build_hardware.py
=================
Python equivalent of build_hardware.tcl for the PYNQ-Z2 Traffic Sign
Recognition project.

Usage (from a Vivado-sourced environment or any shell with Vivado on PATH):
  python build_hardware.py

What it does:
  - Generates all required Vivado Tcl commands in-memory (no .tcl file needed).
  - Launches Vivado in non-interactive batch mode and pipes the commands in.
  - No manual TCL scripting required.
  - Targets XC7Z020 (PYNQ-Z2) instead of XC7Z010 (Edge Z7-10).
  - Produces design_1.bit + design_1.hwh for use as a PYNQ overlay.

Requirements:
  - Vivado must be installed and accessible on your PATH
    (run from the Vivado shell, or add Vivado/bin to PATH first).
  - 'PYNQ-Z2 v1.0.xdc' must be present in the same directory as this script.
"""

import subprocess
import sys
import textwrap
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration – edit here instead of inside TCL
# ---------------------------------------------------------------------------
PROJECT_NAME   = "PYNQ_TSR_Project"
FPGA_PART      = "xc7z020clg400-1"       # PYNQ-Z2 chip (larger than Z7-10)
BD_DESIGN_NAME = "design_1"
XDC_FILE       = "PYNQ-Z2 v1.0.xdc"      # must be in the same folder

# ---------------------------------------------------------------------------
# Build the Vivado commands as a Python list (no .tcl file written to disk)
# ---------------------------------------------------------------------------
def build_commands(script_dir: str) -> list[str]:
    """Return an ordered list of Vivado Tcl commands for PYNQ-Z2."""
    # Use forward slashes – Vivado/Tcl requires them even on Windows
    base = Path(script_dir).as_posix()
    xdc  = (Path(script_dir) / XDC_FILE).as_posix()

    cmds: list[str] = []

    # 1. Project Setup
    cmds += [
        f'create_project {PROJECT_NAME} {base}/{PROJECT_NAME} '
        f'-part {FPGA_PART} -force',
    ]

    # 2. Block Design
    cmds += [
        f'create_bd_design "{BD_DESIGN_NAME}"',
    ]

    # 3. Zynq Processing System
    cmds += [
        'create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 '
        'processing_system7_0',
        'apply_bd_automation -rule xilinx.com:bd_rule:processing_system7 '
        '-config {make_external "FIXED_IO, DDR" apply_board_connection "1"} '
        '[get_bd_cells processing_system7_0]',
        # PYNQ-Z2: Enable HP0 (VDMA write), HP2 (optional HDMI read),
        #          I2C0 on EMIO (camera DDC), FCLK0 @ 100 MHz
        'set_property -dict [list '
        'CONFIG.PCW_USE_S_AXI_HP0          {1} '
        'CONFIG.PCW_USE_S_AXI_HP2          {1} '
        'CONFIG.PCW_I2C0_PERIPHERAL_ENABLE {1} '
        'CONFIG.PCW_I2C0_I2C0_IO           {EMIO} '
        'CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ {100}] '
        '[get_bd_cells processing_system7_0]',
    ]

    # 4. AXI VDMA (write-only: camera → DDR)
    cmds += [
        'create_bd_cell -type ip -vlnv xilinx.com:ip:axi_vdma:6.3 axi_vdma_0',
        'set_property -dict [list CONFIG.c_include_mm2s {0}] '
        '[get_bd_cells axi_vdma_0]',
    ]

    # 5. Video In to AXI4-Stream (CMOS interface)
    cmds += [
        'create_bd_cell -type ip -vlnv xilinx.com:ip:v_vid_in_axi4s:4.0 '
        'v_vid_in_axi4s_0',
    ]

    # 6. AXI Interconnects & Automation
    cmds += [
        'apply_bd_automation -rule xilinx.com:bd_rule:axi4 '
        '-config { Master "/processing_system7_0/M_AXI_GP0" '
        'intc_ip "New AXI Interconnect" Intc "0" } '
        '[get_bd_intf_pins axi_vdma_0/S_AXI_LITE]',

        'apply_bd_automation -rule xilinx.com:bd_rule:axi4 '
        '-config { Master "/axi_vdma_0/M_AXI_S2MM" '
        'intc_ip "New AXI Interconnect" Intc "0" } '
        '[get_bd_intf_pins processing_system7_0/S_AXI_HP0]',
    ]

    # 7. Video pipeline connection: vid_in → VDMA S2MM
    cmds += [
        'connect_bd_intf_net '
        '[get_bd_intf_pins v_vid_in_axi4s_0/video_out] '
        '[get_bd_intf_pins axi_vdma_0/S_AXIS_S2MM]',
    ]

    # 8. Export camera interface pins to top-level ports
    cmds += [
        'make_bd_intf_pins_external '
        '[get_bd_intf_pins v_vid_in_axi4s_0/vid_io_in]',
    ]

    # 8a. Connect FCLK_CLK0 (100 MHz) to VDMA and Video In stream clocks
    cmds += [
        'connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] [get_bd_pins axi_vdma_0/s_axis_s2mm_aclk]',
        'connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] [get_bd_pins v_vid_in_axi4s_0/aclk]',
    ]

    # 9. Save & close BD *before* generate_target (Vivado requirement)
    cmds += [
        'validate_bd_design',
        f'save_bd_design',
        f'close_bd_design [get_bd_designs {BD_DESIGN_NAME}]',
    ]

    # 10. Generate HDL wrapper
    cmds += [
        f'set bd_file [get_files *{BD_DESIGN_NAME}.bd]',
        'generate_target all $bd_file',
        'set wrapper_path [make_wrapper -files $bd_file -top]',
        'add_files -norecurse $wrapper_path',
        'update_compile_order -fileset sources_1',
        f'set_property top {BD_DESIGN_NAME}_wrapper [current_fileset]',
        'update_compile_order -fileset sources_1',
    ]

    # 11. Add XDC constraints (PYNQ-Z2 specific)
    cmds += [
        f'add_files    -fileset constrs_1 -norecurse {{{xdc}}}',
        f'import_files -fileset constrs_1 {{{xdc}}}',
    ]

    # 12. Save project & print completion banner
    cmds += [
        'puts "=================================================="',
        f'puts " Vivado Project \'{PROJECT_NAME}\' is now ready!  "',
        'puts " After bitstream: copy .bit + .hwh to HW folder  "',
        'puts " Then run: python pynq_app.py                     "',
        'puts " Or open:  tsr_notebook.ipynb in Jupyter          "',
        'puts "=================================================="',
    ]

    return cmds


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
def run_vivado_batch(cmds: list[str]) -> int:
    """
    Launch Vivado in batch/non-interactive mode, feed it the commands via
    stdin, and stream its output to the user's console in real time.

    Returns the Vivado process exit code.
    """
    vivado_cmd = [
        "vivado",
        "-mode", "batch",
        "-nolog",
        "-nojournal",
        "-source", "/dev/stdin",
    ]

    # Windows: Vivado doesn't support /dev/stdin; use tcl mode instead
    if sys.platform.startswith("win"):
        vivado_cmd = [
            "vivado",
            "-mode", "tcl",
            "-nolog",
            "-nojournal",
        ]

    tcl_script = "\n".join(cmds) + "\nexit\n"

    print("=" * 60)
    print("  Launching Vivado batch build for PYNQ-Z2 (no TCL file needed)")
    print("=" * 60)
    print(f"  Project : {PROJECT_NAME}")
    print(f"  Part    : {FPGA_PART}")
    print(f"  XDC     : {XDC_FILE}")
    print("=" * 60)

    try:
        proc = subprocess.Popen(
            vivado_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        print("\n[ERROR] 'vivado' was not found on PATH.")
        print("  → Open a Vivado shell (Settings64.bat) and re-run this script.")
        return 1

    try:
        stdout, _ = proc.communicate(input=tcl_script, timeout=600)
        print(stdout)
    except subprocess.TimeoutExpired:
        proc.kill()
        print("[ERROR] Vivado timed out after 10 minutes.")
        return 1

    return proc.returncode


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    script_dir = Path(__file__).parent.resolve()

    # Sanity-check: XDC file must exist
    xdc_path = script_dir / XDC_FILE
    if not xdc_path.exists():
        print(f"[ERROR] Constraint file not found: {xdc_path}")
        print(f"  → Make sure '{XDC_FILE}' is in the same folder.")
        sys.exit(1)

    cmds = build_commands(str(script_dir))
    rc   = run_vivado_batch(cmds)

    if rc == 0:
        print("\n✅  Build completed successfully.")
        print(f"   Project at: {script_dir / PROJECT_NAME}")
        print("\n📌  Next steps:")
        print("   1. Open Vivado GUI → Generate Bitstream")
        print(f"   2. Copy design_1.bit + design_1.hwh → {script_dir}")
        print("   3. Transfer files to PYNQ-Z2 via Jupyter file manager")
        print("   4. Run: python pynq_app.py  OR  open tsr_notebook.ipynb")
    else:
        print(f"\n❌  Vivado exited with code {rc}. Check the output above.")

    sys.exit(rc)
