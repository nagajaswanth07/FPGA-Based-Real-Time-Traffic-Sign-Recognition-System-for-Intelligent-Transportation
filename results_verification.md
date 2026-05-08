# Results Verification Guide
## PYNQ-Z2 Traffic Sign Recognition (TSR) Project

---

## ✅ Pre-Verification Checklist

| Item | Status |
|---|---|
| `design_1.bit` — Bitstream generated from Vivado | 🔲 Check |
| `design_1.hwh` — Hardware handoff file (auto-generated alongside .bit) | 🔲 Check |
| `gtsrb_quantized.tflite` — Model quantized | ✅ Done |
| `pynq_app.py` — Inference application ready | ✅ Done |
| PYNQ-Z2 board powered via 12V barrel jack | 🔲 Check |
| PYNQ-Z2 connected via USB or Ethernet | 🔲 Check |

---

## Step 1 — Find the Bitstream + HWH Files

After Vivado completes, the bitstream and hardware handoff file are located at:

```
PYNQ_TSR_Project\PYNQ_TSR_Project.runs\impl_1\design_1_wrapper.bit
PYNQ_TSR_Project\PYNQ_TSR_Project.gen\sources_1\bd\design_1\hw_handoff\design_1.hwh
```

> ⚠️ **PYNQ requires BOTH files renamed and placed together:**
> - Rename `design_1_wrapper.bit` → `design_1.bit`
> - Keep `design_1.hwh` as-is
> - Both must have the **same base name** (`design_1`)

To confirm bitstream path in Vivado Tcl Console:
```tcl
set bit [get_files -of_objects [get_runs impl_1] *.bit]
puts $bit
```

---

## Step 2 — Access the PYNQ-Z2 Jupyter Interface

The PYNQ-Z2 runs a Jupyter notebook server. Connect via:

| Connection | URL |
|---|---|
| **USB** (plug PC ↔ board USB port) | `http://192.168.2.99` |
| **Ethernet** (direct cable to PC) | `http://192.168.2.99` |
| **Ethernet** (via router/DHCP) | Check your router for assigned IP |

> Default password: **`xilinx`**

---

## Step 3 — Transfer Files to the PYNQ-Z2 Board

### Option A — Jupyter File Manager (Easiest)
1. Open `http://192.168.2.99` in your browser
2. Click the **Upload** button (top right)
3. Upload all files listed below to `/home/xilinx/`

### Option B — SCP from PowerShell
```powershell
# Set your PYNQ-Z2 IP
$IP = "192.168.2.99"

# 1. Copy bitstream (RENAMED)
scp "PYNQ_TSR_Project\PYNQ_TSR_Project.runs\impl_1\design_1_wrapper.bit" `
    xilinx@${IP}:/home/xilinx/design_1.bit

# 2. Copy hardware handoff file
scp "PYNQ_TSR_Project\PYNQ_TSR_Project.gen\sources_1\bd\design_1\hw_handoff\design_1.hwh" `
    xilinx@${IP}:/home/xilinx/design_1.hwh

# 3. Copy quantized model
scp "d:\Antigravity\HARDWARE\PYNQ_Z2\HW\gtsrb_quantized.tflite" `
    xilinx@${IP}:/home/xilinx/

# 4. Copy inference app
scp "d:\Antigravity\HARDWARE\PYNQ_Z2\HW\pynq_app.py" `
    xilinx@${IP}:/home/xilinx/
```

> Default credentials — **user:** `xilinx` | **password:** `xilinx`

---

## Step 4 — SSH into the Board

```bash
ssh xilinx@192.168.2.99
cd /home/xilinx
ls -lh
```

Confirm these files exist on the board:
```
design_1.bit        ← bitstream
design_1.hwh        ← hardware handoff (PYNQ-Z2 requirement)
gtsrb_quantized.tflite
pynq_app.py
```

---

## Step 5 — Quick Hardware Sanity Check

Before running the full app, verify the overlay loads:

```bash
sudo python3
```

```python
from pynq import Overlay

ol = Overlay("design_1.bit")
print("✅ Hardware loaded:", list(ol.ip_dict.keys()))
```

**Expected output:**
```
✅ Hardware loaded: ['axi_vdma_0', 'processing_system7_0', ...]
```
> If `axi_vdma_0` appears — the hardware design is working correctly.

---

## Step 6 — Run the Inference Application

```bash
sudo python3 pynq_app.py
```

**Expected output:**
```
Overlay loaded successfully on PYNQ-Z2!
Model Loaded. Input shape: [1, 100, 100, 3]
Starting Traffic Sign Recognition on PYNQ-Z2...
Press Ctrl+C to stop.

Detected: Speed limit (50km/h)               | Confidence: 94.21% | Latency:  11.30ms
Detected: Stop                               | Confidence: 98.76% | Latency:  10.90ms
Detected: No entry                           | Confidence: 91.33% | Latency:  11.52ms
```

Press `Ctrl+C` to stop.

---

## Step 7 — (Optional) Run via Jupyter Notebook

You can also run interactively inside Jupyter without SSH:

1. Open `http://192.168.2.99` in browser
2. Navigate to `/home/xilinx/`
3. Create a new notebook → paste and run:

```python
from pynq import Overlay
import tflite_runtime.interpreter as tflite
import numpy as np, cv2, time

ol = Overlay("design_1.bit")
vdma = ol.axi_vdma_0

interpreter = tflite.Interpreter(model_path="gtsrb_quantized.tflite")
interpreter.allocate_tensors()
in_det  = interpreter.get_input_details()
out_det = interpreter.get_output_details()

frame = vdma.readchannel.readframe()
img   = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), (100, 100))
data  = np.expand_dims(img, 0).astype(np.uint8)

interpreter.set_tensor(in_det[0]['index'], data)
interpreter.invoke()

pred  = np.argmax(interpreter.get_tensor(out_det[0]['index'])[0])
print(f"Predicted class: {pred}")
```

---

## Step 8 — Results Verification Table

| Metric | Expected Value | How to Verify |
|---|---|---|
| Overlay Load | No errors | Check terminal output |
| `design_1.hwh` present | Yes | `ls -lh /home/xilinx/` |
| Model Input Shape | `[1, 100, 100, 3]` | Printed on startup |
| Detected Class | One of 43 GTSRB classes | Printed per frame |
| Confidence | > 85% for clear signs | Printed per frame |
| Inference Latency | < 30ms per frame | Printed per frame (Z2 is faster than Z7-10) |
| Frame Rate | ~30–40 FPS | `1000 / latency_ms` |

---

## Step 9 — Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `FileNotFoundError: design_1.bit` | Wrong filename | Rename `design_1_wrapper.bit` → `design_1.bit` |
| `RuntimeError: No .hwh file found` | Missing handoff file | Copy `design_1.hwh` alongside `.bit` |
| `Overlay load failed` | Bitstream mismatch | Rebuild bitstream targeting `xc7z020clg400-1` |
| `VDMA timeout` | Camera not connected | Check OV5640 / HDMI Rx cable |
| `ModuleNotFoundError: pynq` | Wrong Python env | Use `sudo python3`, not `python3` |
| Low confidence (< 50%) | Poor lighting / camera angle | Improve lighting, hold sign steady |
| `tflite_runtime` not found | Missing package | `pip3 install tflite-runtime` |
| Can't reach `192.168.2.99` | Boot mode wrong | Set jumper to SD card boot mode |

---

## Step 10 — Project Completion Summary

| Component | Details |
|---|---|
| **FPGA Board** | PYNQ-Z2 (xc7z020clg400-1) |
| **Camera** | OV5640 or HDMI Rx input |
| **Dataset** | GTSRB — 43 traffic sign classes |
| **Model** | MobileNet-based, quantized INT8 TFLite |
| **Model Size** | ~900 KB (gtsrb_quantized.tflite) |
| **Hardware** | Zynq PS7 + AXI VDMA + Video In IP |
| **Overlay Files** | `design_1.bit` + `design_1.hwh` |
| **Interface** | PYNQ Python API + Jupyter Notebook |
| **Target Latency** | < 30ms per inference |

---

*Generated: April 15, 2026 | PYNQ-Z2 TSR Project*
