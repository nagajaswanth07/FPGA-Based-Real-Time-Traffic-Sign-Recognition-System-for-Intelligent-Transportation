# ==============================================================
# PYNQ-Z2 Traffic Sign Recognition — Complete Vivado TCL Script
# ==============================================================
# Board  : PYNQ-Z2 (TUL)
# FPGA   : xc7z020clg400-1
# Camera : OV5640 (8-bit parallel) via Arduino Header
# Output : design_1.bit + design_1.hwh  (PYNQ overlay pair)
#
# HOW TO RUN IN VIVADO:
#   Method 1 — Tcl Console:
#     cd {d:/Antigravity/HARDWARE/PYNQ_Z2/HW}
#     source build_hardware.tcl
#
#   Method 2 — Vivado Batch:
#     vivado -mode batch -source build_hardware.tcl
#
# AFTER RUNNING:
#   Copy from PYNQ_TSR_Project/PYNQ_TSR_Project.runs/impl_1/
#     → design_1_wrapper.bit   (RENAME to design_1.bit)
#     → design_1.hwh           (from .gen/sources_1/bd/design_1/hw_handoff/)
#   Upload both to PYNQ-Z2 board via Jupyter file manager
# ==============================================================

# --- Set working directory to this script's location ---
set script_dir [file dirname [file normalize [info script]]]
cd $script_dir

# ==============================================================
# 1. Create Project
# ==============================================================
set project_name "PYNQ_TSR_Project"
set fpga_part    "xc7z020clg400-1"

create_project $project_name ${script_dir}/${project_name} \
    -part $fpga_part -force

set_property target_language VHDL [current_project]

puts "INFO: Project '$project_name' created for part $fpga_part"

# ==============================================================
# 2. Create Block Design
# ==============================================================
set bd_name "design_1"
create_bd_design $bd_name
current_bd_design $bd_name

puts "INFO: Block design '$bd_name' created"

# ==============================================================
# 3. Zynq-7020 Processing System
# ==============================================================
create_bd_cell -type ip \
    -vlnv xilinx.com:ip:processing_system7:5.5 \
    processing_system7_0

# Apply board preset (auto-connects DDR, FIXED_IO)
apply_bd_automation \
    -rule xilinx.com:bd_rule:processing_system7 \
    -config { make_external "FIXED_IO, DDR" apply_board_connection "1" } \
    [get_bd_cells processing_system7_0]

# Configure PS for PYNQ-Z2:
#   HP0  → VDMA write (S2MM): camera → DDR
#   I2C0 → EMIO: OV5640 configuration bus
#   FCLK0 → 100 MHz pixel / AXI clock
#   FCLK1 → 200 MHz  (optional, for IDELAY REFCLK)
set_property -dict [list \
    CONFIG.PCW_USE_S_AXI_HP0              {1}    \
    CONFIG.PCW_I2C0_PERIPHERAL_ENABLE     {1}    \
    CONFIG.PCW_I2C0_I2C0_IO              {EMIO}  \
    CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ  {100}   \
    CONFIG.PCW_FPGA1_PERIPHERAL_FREQMHZ  {200}   \
    CONFIG.PCW_USE_FABRIC_INTERRUPT       {1}    \
    CONFIG.PCW_IRQ_F2P_INTR               {1}    \
] [get_bd_cells processing_system7_0]

puts "INFO: PS7 configured (HP0=ON, I2C0=EMIO, FCLK0=100MHz)"

# ==============================================================
# 4. AXI VDMA — Write-only (S2MM): camera frames → DDR
# ==============================================================
create_bd_cell -type ip \
    -vlnv xilinx.com:ip:axi_vdma:6.3 \
    axi_vdma_0

set_property -dict [list \
    CONFIG.c_include_mm2s        {0}   \
    CONFIG.c_s2mm_linebuffer_depth {2048} \
    CONFIG.c_addr_width          {32}  \
] [get_bd_cells axi_vdma_0]

puts "INFO: AXI VDMA configured (S2MM write-only)"

# ==============================================================
# 5. Video In to AXI4-Stream — parallel CMOS → AXI stream
# ==============================================================
create_bd_cell -type ip \
    -vlnv xilinx.com:ip:v_vid_in_axi4s:4.0 \
    v_vid_in_axi4s_0

# OV5640 is 8-bit, progressive scan
set_property -dict [list \
    CONFIG.C_PIXELS_PER_CLOCK {1} \
    CONFIG.C_M_AXIS_VIDEO_DATA_WIDTH {8} \
] [get_bd_cells v_vid_in_axi4s_0]

puts "INFO: v_vid_in_axi4s configured (8-bit, 1 pixel/clk)"

# ==============================================================
# 6. AXI Interconnects — auto-connect AXI buses
# ==============================================================
# 6a. PS GP0 Master → VDMA S_AXI_LITE (control)
apply_bd_automation \
    -rule xilinx.com:bd_rule:axi4 \
    -config { \
        Master           "/processing_system7_0/M_AXI_GP0" \
        intc_ip          "New AXI Interconnect"             \
        Clk_xbar         "/processing_system7_0/FCLK_CLK0 (100 MHz)" \
        Clk_master       "/processing_system7_0/FCLK_CLK0 (100 MHz)" \
        Clk_slave        "/processing_system7_0/FCLK_CLK0 (100 MHz)" \
    } \
    [get_bd_intf_pins axi_vdma_0/S_AXI_LITE]

# 6b. VDMA M_AXI_S2MM → PS HP0 (data DMA into DDR)
apply_bd_automation \
    -rule xilinx.com:bd_rule:axi4 \
    -config { \
        Master    "/axi_vdma_0/M_AXI_S2MM" \
        intc_ip   "New AXI Interconnect"   \
    } \
    [get_bd_intf_pins processing_system7_0/S_AXI_HP0]

puts "INFO: AXI interconnects wired"

# ==============================================================
# 7. Video pipeline: vid_in_axi4s → VDMA S2MM stream
# ==============================================================
connect_bd_intf_net \
    [get_bd_intf_pins v_vid_in_axi4s_0/video_out] \
    [get_bd_intf_pins axi_vdma_0/S_AXIS_S2MM]

puts "INFO: Video pipeline connected (vid_in → VDMA)"

# ==============================================================
# 8. Export camera interface as top-level ports
#    These will be constrained in pynq_z2_camera.xdc
# ==============================================================
make_bd_intf_pins_external \
    [get_bd_intf_pins v_vid_in_axi4s_0/vid_io_in]

puts "INFO: vid_io_in exposed as top-level ports"

# ==============================================================
# 8a. Connect FCLK_CLK0 (100 MHz) to all clocks
# ==============================================================
connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
               [get_bd_pins axi_vdma_0/s_axis_s2mm_aclk]

connect_bd_net [get_bd_pins processing_system7_0/FCLK_CLK0] \
               [get_bd_pins v_vid_in_axi4s_0/aclk]

puts "INFO: Clocks connected (100 MHz FCLK0)"

# ==============================================================
# 9. Validate, Save & Close Block Design
# ==============================================================
validate_bd_design
save_bd_design
close_bd_design [get_bd_designs $bd_name]

puts "INFO: Block design validated and saved"

# ==============================================================
# 10. Generate HDL Wrapper
# ==============================================================
set bd_file [get_files *${bd_name}.bd]
generate_target all $bd_file

set wrapper_path [make_wrapper -files $bd_file -top]
add_files -norecurse $wrapper_path

update_compile_order -fileset sources_1
set_property top ${bd_name}_wrapper [current_fileset]
update_compile_order -fileset sources_1

puts "INFO: HDL wrapper '${bd_name}_wrapper' set as top"

# ==============================================================
# 11. Add Constraints
#     Uses project-specific camera XDC (pynq_z2_camera.xdc)
#     NOT the generic 'PYNQ-Z2 v1.0.xdc' (which has all pins commented)
# ==============================================================
set xdc_file "${script_dir}/pynq_z2_camera.xdc"

if { [file exists $xdc_file] } {
    add_files    -fileset constrs_1 -norecurse $xdc_file
    import_files -fileset constrs_1 $xdc_file
    puts "INFO: Constraints added: pynq_z2_camera.xdc"
} else {
    puts "ERROR: pynq_z2_camera.xdc not found at $xdc_file"
    puts "       Make sure both TCL and XDC are in the same folder."
    exit 1
}

# ==============================================================
# 12. Run Synthesis + Implementation + Write Bitstream
# ==============================================================
puts ""
puts "=================================================="
puts "  Starting Synthesis (this takes 5-15 minutes)    "
puts "=================================================="

launch_runs synth_1 -jobs 4
wait_on_run synth_1

if { [get_property PROGRESS [get_runs synth_1]] != "100%" } {
    puts "ERROR: Synthesis failed! Check the Vivado Messages tab."
    exit 1
}
puts "INFO: Synthesis COMPLETE"

puts ""
puts "=================================================="
puts "  Starting Implementation + Bitstream             "
puts "=================================================="

launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

if { [get_property PROGRESS [get_runs impl_1]] != "100%" } {
    puts "ERROR: Implementation failed! Check the Vivado Messages tab."
    exit 1
}
puts "INFO: Implementation + Bitstream COMPLETE"

# ==============================================================
# 13. Export Hardware (generates .hwh for PYNQ)
# ==============================================================
set impl_dir "${script_dir}/${project_name}/${project_name}.runs/impl_1"
set bit_file  "${impl_dir}/design_1_wrapper.bit"
set hwh_file  "${script_dir}/${project_name}/${project_name}.gen/sources_1/bd/${bd_name}/hw_handoff/${bd_name}.hwh"

puts ""
puts "=================================================="
puts "  BITSTREAM GENERATION COMPLETE!"
puts "=================================================="
puts ""
puts "  Files to copy to PYNQ-Z2 board:"
puts "  .bit → $bit_file"
puts "  .hwh → $hwh_file"
puts ""
puts "  STEP 1: Rename design_1_wrapper.bit → design_1.bit"
puts "  STEP 2: Upload design_1.bit + design_1.hwh to PYNQ-Z2"
puts "          via http://192.168.2.99 (Jupyter file manager)"
puts "  STEP 3: Also upload gtsrb_quantized.tflite + pynq_app.py"
puts "  STEP 4: SSH in or open tsr_demo.ipynb and run!"
puts "=================================================="
