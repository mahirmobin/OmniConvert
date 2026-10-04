# OmniConvert

A lightweight desktop application for converting, resizing, and processing images — built with Python, Pillow, and Tkinter.

---

## Features

- **Format conversion** — JPEG, PNG, WEBP, BMP, TIFF, GIF, ICO
- **PDF creation** — merge multiple images into a single PDF
- **Batch processing** — convert many files in one click
- **Resize** — by width, height, or both; optional aspect-ratio lock
- **DPI control** — embed custom DPI metadata (72, 150, 300, 600…)
- **Quality slider** — for lossy formats (JPEG, WEBP), 1–95
- **Custom output directory** — or save next to the source files
- **Drag & drop** — drop images directly onto the app window (requires `tkinterdnd2`)
- **Progress log** — colour-coded success / error messages per file

---

## Installation

### 1. Prerequisites

- Python 3.10 or newer
- pip

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
python main.py
```

---

## Project structure

```
OmniConvert/
├── main.py             # Entry point
├── requirements.txt
├── README.md
├── core/
│   ├── converter.py    # Format conversion + PDF generation
│   ├── resizer.py      # Image resize logic
│   ├── dpi.py          # DPI metadata embedding
│   └── utils.py        # Shared helpers & constants
└── ui/
    ├── app.py          # Main Tk window
    ├── file_panel.py   # Drag-and-drop zone + file list
    ├── options_panel.py# Settings (format, resize, DPI, quality, output dir)
    └── progress_panel.py # Progress bar + log messages
```

---

## Packaging into an executable (PyInstaller)

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Build a single-file executable

```bash
pyinstaller --onefile --windowed --name "OmniConvert" main.py
```

The executable will be produced in the `dist/` folder.

### Notes

- `--windowed` suppresses the terminal console on Windows.
- If you use drag & drop (`tkinterdnd2`), add its DLL to the bundle:

```bash
pyinstaller --onefile --windowed \
  --add-binary "path/to/tkdnd2.8;tkdnd2.8" \
  --name "OmniConvert" main.py
```

The path to `tkdnd2.8` is typically inside your Python environment's `site-packages/tkinterdnd2/`.

---

## Notes on DPI

DPI is embedded as **metadata** only — pixel dimensions are not changed. To physically resample pixels at a new DPI, use the resize feature alongside the DPI setting.
