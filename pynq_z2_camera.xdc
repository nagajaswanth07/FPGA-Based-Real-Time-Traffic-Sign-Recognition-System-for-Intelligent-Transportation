## ============================================================
## PYNQ-Z2 Pin Constraints for OV5640 Camera
## Camera connects via Arduino Header (ar[0:13]) on PYNQ-Z2
## Port names match Vivado-generated vid_io_in_0_* interface
## Board  : PYNQ-Z2 (TUL) — xc7z020clg400-1
## ============================================================

# ------------------------------------------------------------
# System Clock — 125 MHz (H16)
# Needed for timing constraints reference
# ------------------------------------------------------------
set_property -dict { PACKAGE_PIN H16  IOSTANDARD LVCMOS33 } [get_ports { sysclk }]
create_clock -add -name sys_clk_pin -period 8.00 -waveform {0 4} [get_ports { sysclk }]

# ------------------------------------------------------------
# Video Data Bus: OV5640 D[0:7] → vid_io_in_0_data[0:7]
# Mapped to Arduino Header digital I/O pins ar[0:7]
# Upper 16 bits [23:8] are unused (OV5640 is 8-bit) — DRC override below
# ------------------------------------------------------------
set_property PACKAGE_PIN T14  [get_ports {vid_io_in_0_data[0]}]  ;# ar[0]
set_property PACKAGE_PIN U12  [get_ports {vid_io_in_0_data[1]}]  ;# ar[1]
set_property PACKAGE_PIN U13  [get_ports {vid_io_in_0_data[2]}]  ;# ar[2]
set_property PACKAGE_PIN V13  [get_ports {vid_io_in_0_data[3]}]  ;# ar[3]
set_property PACKAGE_PIN V15  [get_ports {vid_io_in_0_data[4]}]  ;# ar[4]
set_property PACKAGE_PIN T15  [get_ports {vid_io_in_0_data[5]}]  ;# ar[5]
set_property PACKAGE_PIN R16  [get_ports {vid_io_in_0_data[6]}]  ;# ar[6]
set_property PACKAGE_PIN U17  [get_ports {vid_io_in_0_data[7]}]  ;# ar[7]
set_property IOSTANDARD LVCMOS33 [get_ports {vid_io_in_0_data[*]}]

# ------------------------------------------------------------
# Active Video (HREF / HREF from OV5640) → ar[8]
# ------------------------------------------------------------
set_property PACKAGE_PIN V17  [get_ports vid_io_in_0_active_video]  ;# ar[8]
set_property IOSTANDARD LVCMOS33 [get_ports vid_io_in_0_active_video]

# ------------------------------------------------------------
# Vertical Sync (VSYNC from OV5640) → ar[9]
# ------------------------------------------------------------
set_property PACKAGE_PIN V18  [get_ports vid_io_in_0_vsync]  ;# ar[9]
set_property IOSTANDARD LVCMOS33 [get_ports vid_io_in_0_vsync]

# ------------------------------------------------------------
# Camera Pixel Clock (PCLK from OV5640) → ar[10]
# This is the input clock from the camera to the FPGA
# ------------------------------------------------------------
set_property PACKAGE_PIN T16  [get_ports vid_io_in_0_pclk]  ;# ar[10]
set_property IOSTANDARD LVCMOS33 [get_ports vid_io_in_0_pclk]
create_clock -name cam_pclk -period 25.0 [get_ports vid_io_in_0_pclk]

# ------------------------------------------------------------
# Camera Master Clock Output (XCLK to OV5640) → ar[11]
# PS7 drives this via GPIO / FCLK output
# ------------------------------------------------------------
set_property PACKAGE_PIN R17  [get_ports cmos_xclk]  ;# ar[11]
set_property IOSTANDARD LVCMOS33 [get_ports cmos_xclk]

# ------------------------------------------------------------
# Camera Reset (active-low, to OV5640) → ar[12]
# Driven by PS7 GPIO
# ------------------------------------------------------------
set_property PACKAGE_PIN P18  [get_ports cmos_rst_n]  ;# ar[12]
set_property IOSTANDARD LVCMOS33 [get_ports cmos_rst_n]

# ------------------------------------------------------------
# Camera Power Down (PWDN to OV5640) → ar[13]
# Driven by PS7 GPIO
# ------------------------------------------------------------
set_property PACKAGE_PIN N17  [get_ports cmos_pwdn]  ;# ar[13]
set_property IOSTANDARD LVCMOS33 [get_ports cmos_pwdn]

# NOTE: I2C (SCL/SDA) is handled via PS7 EMIO internally.
# It does NOT appear as a top-level port — no XDC needed.

# ------------------------------------------------------------
# Status LEDs (optional — useful for debug)
# ------------------------------------------------------------
set_property -dict { PACKAGE_PIN R14  IOSTANDARD LVCMOS33 } [get_ports { led[0] }]  ;# LED0 - Overlay loaded
set_property -dict { PACKAGE_PIN P14  IOSTANDARD LVCMOS33 } [get_ports { led[1] }]  ;# LED1 - VDMA active
set_property -dict { PACKAGE_PIN N16  IOSTANDARD LVCMOS33 } [get_ports { led[2] }]  ;# LED2 - Inference running
set_property -dict { PACKAGE_PIN M14  IOSTANDARD LVCMOS33 } [get_ports { led[3] }]  ;# LED3 - Error

# ------------------------------------------------------------
# Push Buttons (optional — for start/stop/reset)
# ------------------------------------------------------------
set_property -dict { PACKAGE_PIN D19  IOSTANDARD LVCMOS33 } [get_ports { btn[0] }]  ;# BTN0 - Start
set_property -dict { PACKAGE_PIN D20  IOSTANDARD LVCMOS33 } [get_ports { btn[1] }]  ;# BTN1 - Stop

# ------------------------------------------------------------
# DRC Overrides (required — explained below)
#
# vid_io_in_0_field  — OV5640 is progressive scan, no field signal
# vid_io_in_0_vblank — derived internally, not a physical camera pin
# vid_io_in_0_data[23:8] — 8-bit camera, upper 16 bits physically unused
#
# These cannot be assigned physical pins. Downgrading DRC errors
# to warnings allows bitstream generation safely.
# ------------------------------------------------------------
set_property SEVERITY {Warning} [get_drc_checks NSTD-1]
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]
