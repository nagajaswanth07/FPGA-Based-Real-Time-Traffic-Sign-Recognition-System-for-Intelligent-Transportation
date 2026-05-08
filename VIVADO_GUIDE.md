# How to Generate the Bitstream — PYNQ-Z2
## Step-by-Step Vivado Guide

---

## 📁 Files Required (all in `PYNQ_Z2\HW\`)

| File | Purpose |
|---|---|
| `build_hardware.tcl` | **Main script** — creates project, runs synthesis + bitstream |
| `pynq_z2_camera.xdc` | **Camera pin constraints** — OV5640 via Arduino header |
| `PYNQ-Z2 v1.0.xdc` | Reference only — all pins commented, do NOT use as primary XDC |

---

## Method 1 — Vivado Tcl Console *(Recommended)*

### Open Vivado
1. Launch **Vivado 2020.x** (or newer)
2. On the start screen click **"Tcl Console"** at the bottom

### Run the Script
```tcl
cd {d:/Antigravity/HARDWARE/PYNQ_Z2/HW}
source build_hardware.tcl
```

> ⏱️ This will run **automatically** through Synthesis → Implementation → Bitstream (~15–30 min)

---

## Method 2 — Vivado Batch Mode *(Headless)*

Open a **Vivado Shell** (`Settings64.bat`) and run:

```powershell
cd "d:\Antigravity\HARDWARE\PYNQ_Z2\HW"
vivado -mode batch -source build_hardware.tcl
```

---

## Method 3 — GUI Only (Manual Steps)

If you prefer clicking through the Vivado GUI:

### Step 1 — Create Project
- File → Project → New
- **Project Name:** `PYNQ_TSR_Project`
- **Part:** `xc7z020clg400-1`

### Step 2 — Create Block Design
- Flow Navigator → IP Integrator → **Create Block Design** → name: `design_1`

### Step 3 — Add IPs (in Block Design canvas)
Click the **+** button and add:

| IP Name | Key Settings |
|---|---|
| `Zynq7 Processing System` | Apply board preset, enable HP0, I2C0 EMIO, FCLK0=100MHz |
| `AXI Video Direct Memory Access` | Disable MM2S (write-only / S2MM only) |
| `Video In to AXI4-Stream` | 8-bit, 1 pixel/clock |

### Step 4 — Wire the Design
- Connect `v_vid_in_axi4s_0/video_out` → `axi_vdma_0/S_AXIS_S2MM`
- Run **Designer Assistance** for AXI connections
- Make `vid_io_in` external

### Step 5 — Add XDC Constraints
- Sources tab → Add Sources → Constraints
- Add: `pynq_z2_camera.xdc` ✅
- Do **NOT** add the generic `PYNQ-Z2 v1.0.xdc` as it has everything commented

### Step 6 — Generate Bitstream
- Flow Navigator → **Generate Bitstream**
- Click OK through synthesis/implementation prompts

---

## 📤 After Bitstream Generation

### Find the Output Files

| File | Location |
|---|---|
| **Bitstream** | `PYNQ_TSR_Project\PYNQ_TSR_Project.runs\impl_1\design_1_wrapper.bit` |
| **HW Handoff** | `PYNQ_TSR_Project\PYNQ_TSR_Project.gen\sources_1\bd\design_1\hw_handoff\design_1.hwh` |

> ⚠️ **Rename** `design_1_wrapper.bit` → **`design_1.bit`**  
> Both `.bit` and `.hwh` **must have the same base name** for PYNQ to load them.

### Upload to PYNQ-Z2

**Option A — Jupyter File Manager:**
1. Open `http://192.168.2.99` in browser (password: `xilinx`)
2. Upload into `/home/xilinx/`:
   - `design_1.bit`
   - `design_1.hwh`
   - `gtsrb_quantized.tflite`
   - `pynq_app.py`

**Option B — SCP:**
```powershell
$IP = "192.168.2.99"
scp "...\impl_1\design_1_wrapper.bit"  xilinx@${IP}:/home/xilinx/design_1.bit
scp "...\hw_handoff\design_1.hwh"      xilinx@${IP}:/home/xilinx/design_1.hwh
scp "gtsrb_quantized.tflite"           xilinx@${IP}:/home/xilinx/
scp "pynq_app.py"                      xilinx@${IP}:/home/xilinx/
```

---

## ▶️ Run on PYNQ-Z2

```bash
ssh xilinx@192.168.2.99
cd /home/xilinx
sudo python3 pynq_app.py
```

Or open `tsr_demo.ipynb` in the Jupyter browser at `http://192.168.2.99`

---

## 🔌 Camera Wiring (OV5640 → PYNQ-Z2 Arduino Header)

| OV5640 Pin | PYNQ-Z2 Header | FPGA Pin | XDC Port |
|---|---|---|---|
| D0 | ar[0] | T14 | `vid_io_in_0_data[0]` |
| D1 | ar[1] | U12 | `vid_io_in_0_data[1]` |
| D2 | ar[2] | U13 | `vid_io_in_0_data[2]` |
| D3 | ar[3] | V13 | `vid_io_in_0_data[3]` |
| D4 | ar[4] | V15 | `vid_io_in_0_data[4]` |
| D5 | ar[5] | T15 | `vid_io_in_0_data[5]` |
| D6 | ar[6] | R16 | `vid_io_in_0_data[6]` |
| D7 | ar[7] | U17 | `vid_io_in_0_data[7]` |
| HREF | ar[8] | V17 | `vid_io_in_0_active_video` |
| VSYNC | ar[9] | V18 | `vid_io_in_0_vsync` |
| PCLK | ar[10] | T16 | `vid_io_in_0_pclk` |
| XCLK | ar[11] | R17 | `cmos_xclk` |
| RESET | ar[12] | P18 | `cmos_rst_n` |
| PWDN | ar[13] | N17 | `cmos_pwdn` |
| SDA/SCL | EMIO via PS7 | — | Handled internally |
| GND | GND | — | — |
| 3.3V | 3.3V | — | — |

---

*PYNQ-Z2 TSR Project | April 2026*
