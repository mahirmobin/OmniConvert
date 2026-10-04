"""
Main window using CustomTkinter with drag-and-drop support.
"""

from __future__ import annotations

import os
import threading
from tkinter import messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import TkinterDnD
    _BASE_CLASS = TkinterDnD.Tk
except ImportError:
    import tkinter as tk
    _BASE_CLASS = tk.Tk  # type: ignore[misc]

from ui.file_panel import FilePanel
from ui.options_panel import OptionsPanel
from ui.pdf_panel import PdfStudioPanel
from ui.progress_panel import ProgressPanel


class App(_BASE_CLASS):  # type: ignore[valid-type]
    def __init__(self) -> None:
        super().__init__()
        
        # Setup CustomTkinter aesthetics overall
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("OmniConvert")
        self.geometry("1000x700")
        self.minsize(900, 600)
        
        # Icon
        icon_path = os.path.join(os.path.dirname(__file__), "..", "icon.png")
        if os.path.exists(icon_path):
            try:
                # CustomTkinter hack to use PNG as window icon via PhotoImage
                from PIL import ImageTk, Image
                img = ImageTk.PhotoImage(Image.open(icon_path))
                self.iconphoto(True, img) # type: ignore
            except Exception:
                pass

        self._converting = False
        self._build_ui()

    def _build_ui(self) -> None:
        # Wrap everything in a main CTkFrame to skin the TkinterDnD root
        self.main_container = ctk.CTkFrame(self, fg_color="#181a20", corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        self.main_container.columnconfigure(0, weight=1)
        self.main_container.rowconfigure(0, weight=1)  # Content area
        
        # ==========================================
        # TOP/MAIN CONTENT AREA (Splits into 2 cols)
        # ==========================================
        content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 10))
        content_frame.columnconfigure(0, weight=1) # Left side
        content_frame.columnconfigure(1, weight=0, minsize=320) # Right side Settings
        content_frame.rowconfigure(0, weight=0) # Tabs row
        content_frame.rowconfigure(1, weight=1) # Panels row

        # --- TABS ---
        self.tab_var = ctk.StringVar(value="Image Converter")
        tab_seg = ctk.CTkSegmentedButton(
            content_frame, 
            values=["Image Converter", "PDF Studio"],
            variable=self.tab_var,
            command=self._switch_mode,
            font=("Segoe UI", 13, "bold"),
            selected_color="#2b52ff",
            selected_hover_color="#1e3fc7",
        )
        tab_seg.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))

        # --- LEFT: FILES/PDF STUDIO ---
        self.left_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.left_container.grid(row=1, column=0, sticky="nsew", padx=(0, 20))
        self.left_container.columnconfigure(0, weight=1)
        self.left_container.rowconfigure(0, weight=1)

        self._file_panel = FilePanel(self.left_container)
        self._pdf_panel = PdfStudioPanel(self.left_container)
        
        self._file_panel.grid(row=0, column=0, sticky="nsew") # Default visible

        # --- RIGHT: OPTS & ACTIONS ---
        self.right_container = ctk.CTkFrame(content_frame, fg_color="#21252e", corner_radius=12)
        self.right_container.grid(row=1, column=1, sticky="nsew")
        self.right_container.columnconfigure(0, weight=1)
        self.right_container.rowconfigure(0, weight=1)

        self._options_panel = OptionsPanel(self.right_container)
        self._options_panel.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)


        # ==========================================
        # BOTTOM FIXED BAR (Progress & Buttons)
        # ==========================================
        bottom_bar = ctk.CTkFrame(self.main_container, fg_color="#1e222b", corner_radius=12)
        bottom_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        bottom_bar.columnconfigure(0, weight=1)
        bottom_bar.rowconfigure(0, weight=0) # Progress bar + log
        bottom_bar.rowconfigure(1, weight=0) # Buttons

        self._progress_panel = ProgressPanel(bottom_bar)
        self._progress_panel.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=15, pady=(10, 0))

        # Buttons wrapper inside bottom bar (align right)
        buttons_wrapper = ctk.CTkFrame(bottom_bar, fg_color="transparent")
        buttons_wrapper.grid(row=1, column=1, sticky="e", padx=15, pady=(5, 10))

        self._cancel_btn = ctk.CTkButton(
            buttons_wrapper, text="Cancel", command=self._on_cancel,
            fg_color="#374151", hover_color="#4b5563",
            text_color="white", font=("Segoe UI", 13, "bold"),
            width=100, height=36, state="disabled"
        )
        self._cancel_btn.pack(side="left", padx=(0, 10))

        self._convert_btn = ctk.CTkButton(
            buttons_wrapper, text="⚡ Convert", command=self._on_convert,
            fg_color="#2b52ff", hover_color="#1e3fc7",
            text_color="white", font=("Segoe UI", 13, "bold"),
            width=120, height=36
        )
        self._convert_btn.pack(side="left")

    def _switch_mode(self, mode_name: str) -> None:
        if mode_name == "PDF Studio":
            self._file_panel.grid_forget()
            self._pdf_panel.grid(row=0, column=0, sticky="nsew")
            self._options_panel.set_mode("pdf")
        else:
            self._pdf_panel.grid_forget()
            self._file_panel.grid(row=0, column=0, sticky="nsew")
            self._options_panel.set_mode("image")

    # ------------------------------------------------------------------
    # Conversion Logic
    # ------------------------------------------------------------------
    def _on_convert(self) -> None:
        if self._converting: return

        mode = self.tab_var.get()
        if mode == "Image Converter":
            files = self._file_panel.get_files()
        else:
            files = self._pdf_panel.get_files()

        if not files:
            messagebox.showwarning("No Files", "Please add at least one file.", parent=self) # type: ignore
            return

        options = self._options_panel.get_options(mode)
        if options is None:
            messagebox.showerror("Invalid Settings", self._options_panel.validation_error, parent=self) # type: ignore
            return

        self._converting = True
        self._cancelled = False
        self._convert_btn.configure(state="disabled", text="Working...")
        self._cancel_btn.configure(state="normal")
        self._progress_panel.reset()

        threading.Thread(target=self._run_conversion, args=(files, options, mode), daemon=True).start()

    def _on_cancel(self) -> None:
        self._cancelled = True
        self._progress_panel.log("Cancellation requested...", "warning")

    def _run_conversion(self, files: list[str], options: dict, mode: str) -> None:
        success_count = 0
        error_count = 0
        total = len(files)

        try:
            if mode == "PDF Studio":
                from core.pdf_studio import merge_to_pdf
                from pathlib import Path
                
                output_dir = options.get("output_dir") or str(Path(files[0]).parent)
                output_pdf = str(Path(output_dir) / "Studio_Output.pdf")
                
                self._progress_panel.update(50, 100, f"Merging {len(files)} files into PDF...")
                
                merge_to_pdf(files, output_pdf)
                self._progress_panel.update(100, 100, f"Saved -> {output_pdf}", "success")
                success_count = len(files)

            else:
                from core.converter import convert_image
                from pathlib import Path

                for i, path in enumerate(files, start=1):
                    if self._cancelled:
                        self._progress_panel.log("Cancelled by user.", "warning")
                        break
                    
                    self._progress_panel.update(i-1, total, f"Processing {Path(path).name}...", "info")
                    
                    out_dir = options.get("output_dir") or str(Path(path).parent)
                    res = convert_image(
                        src=path,
                        dest_format=options["format"],
                        output_dir=out_dir,
                        quality=options["quality"],
                        width=options["width"],
                        height=options["height"],
                        maintain_aspect=options["maintain_aspect"],
                        dpi=options["dpi"]
                    )

                    level = "success" if res.success else "error"
                    self._progress_panel.update(i, total, res.message, level)
                    if res.success: success_count += 1
                    else: error_count += 1

        except Exception as e:
            self._progress_panel.log(f"Error: {e}", "error")
            error_count += 1
        finally:
            self.after(0, self._finish_conversion, success_count, error_count)

    def _finish_conversion(self, sc: int, ec: int) -> None:
        self._converting = False
        self._convert_btn.configure(state="normal", text="⚡ Convert")
        self._cancel_btn.configure(state="disabled")
        if ec == 0 and sc > 0:
            self._progress_panel.log("All tasks completed successfully!", "success")
