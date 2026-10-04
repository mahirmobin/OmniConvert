"""
OptionsPanel — CustomTkinter settings cards for Image/PDF modes.
"""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog
from core.utils import SUPPORTED_FORMATS


class OptionsPanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self.validation_error: str = ""
        self._mode = "image"
        self._build_ui()

    def _section(self, parent: ctk.CTkFrame, title: str) -> ctk.CTkFrame:
        # Glass card wrapper
        card = ctk.CTkFrame(parent, fg_color="#181a20", corner_radius=8)
        card.pack(fill="x", pady=5)
        
        lbl = ctk.CTkLabel(card, text=title, font=("Segoe UI", 12, "bold"), text_color="#a8b2d1")
        lbl.pack(anchor="w", padx=12, pady=(10, 5))
        return card

    def _build_ui(self) -> None:
        # Wrapper to hold everything
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(fill="both", expand=True, padx=10, pady=10)

        # ====== Output Format Card ======
        self.fmt_card = self._section(self.inner, "Output Format")
        self._format_var = ctk.StringVar(value="JPEG")
        # Remove PDF from direct image formats since we have a dedicated PDF Studio now
        image_formats = [f for f in SUPPORTED_FORMATS if f != "PDF"]
        self.fmt_combo = ctk.CTkOptionMenu(
            self.fmt_card, variable=self._format_var, values=image_formats,
            fg_color="#21252e", button_color="#2b52ff", button_hover_color="#1e3fc7",
            font=("Segoe UI", 13)
        )
        self.fmt_combo.pack(anchor="w", padx=12, pady=(0, 12))

        # ====== Resize Card ======
        self.res_card = self._section(self.inner, "Resize (leave blank to skip)")
        row_res = ctk.CTkFrame(self.res_card, fg_color="transparent")
        row_res.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(row_res, text="W:", font=("Segoe UI", 12), text_color="#8b949e").pack(side="left")
        self._width_var = ctk.StringVar()
        ctk.CTkEntry(row_res, textvariable=self._width_var, width=60, border_color="#374151", fg_color="#21252e").pack(side="left", padx=(5, 10))

        ctk.CTkLabel(row_res, text="H:", font=("Segoe UI", 12), text_color="#8b949e").pack(side="left")
        self._height_var = ctk.StringVar()
        ctk.CTkEntry(row_res, textvariable=self._height_var, width=60, border_color="#374151", fg_color="#21252e").pack(side="left", padx=(5, 5))

        self._aspect_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self.res_card, text="Maintain aspect ratio", variable=self._aspect_var,
            font=("Segoe UI", 12), text_color="#9ca3af",
            border_color="#374151", hover_color="#2b52ff", fg_color="#2b52ff"
        ).pack(anchor="w", padx=12, pady=(0, 12))

        # ====== Options / DPI ======
        self.dpi_card = self._section(self.inner, "DPI & Quality")
        
        row_dpi = ctk.CTkFrame(self.dpi_card, fg_color="transparent")
        row_dpi.pack(fill="x", padx=12, pady=(0, 8))
        ctk.CTkLabel(row_dpi, text="DPI:", font=("Segoe UI", 12), width=50, anchor="w", text_color="#8b949e").pack(side="left")
        self._dpi_var = ctk.StringVar()
        ctk.CTkEntry(row_dpi, textvariable=self._dpi_var, width=60, border_color="#374151", fg_color="#21252e").pack(side="left")
        ctk.CTkLabel(row_dpi, text="(blank = keep org)", font=("Segoe UI", 11), text_color="#6b7280").pack(side="left", padx=10)

        # Quality
        row_q = ctk.CTkFrame(self.dpi_card, fg_color="transparent")
        row_q.pack(fill="x", padx=12, pady=(5, 12))
        ctk.CTkLabel(row_q, text="Quality:", font=("Segoe UI", 12), width=50, anchor="w", text_color="#8b949e").pack(side="left")
        self._quality_var = ctk.IntVar(value=85)
        self.q_lbl = ctk.CTkLabel(row_q, text="85", font=("Segoe UI", 12, "bold"), text_color="#ffffff", width=25)
        self.q_lbl.pack(side="right")
        self.q_slider = ctk.CTkSlider(
            row_q, from_=1, to=95, variable=self._quality_var,
            button_color="#2b52ff", button_hover_color="#1e3fc7",
            command=lambda v: self.q_lbl.configure(text=str(int(float(v))))
        )
        self.q_slider.pack(side="left", fill="x", expand=True, padx=10)

        # ====== Output Directory ======
        self.dir_card = self._section(self.inner, "Output Directory")
        self._output_dir_var = ctk.StringVar(value="Same as source")
        
        dir_row = ctk.CTkFrame(self.dir_card, fg_color="transparent")
        dir_row.pack(fill="x", padx=12, pady=(0, 12))
        
        ctk.CTkEntry(
            dir_row, textvariable=self._output_dir_var,
            border_color="#374151", fg_color="#21252e", state="disabled"
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            dir_row, text="Browse", width=60,
            fg_color="#374151", hover_color="#4b5563", font=("Segoe UI", 12),
            command=self._browse_output_dir
        ).pack(side="right", padx=(10, 0))

    def _browse_output_dir(self) -> None:
        directory = filedialog.askdirectory(title="Choose output directory")
        if directory:
            # Re-enable briefly just to set
            for w in self.dir_card.winfo_children():
                if isinstance(w, ctk.CTkFrame):
                    for iw in w.winfo_children():
                        if isinstance(iw, ctk.CTkEntry):
                            iw.configure(state="normal")
                            self._output_dir_var.set(directory)
                            iw.configure(state="disabled")

    def set_mode(self, mode: str) -> None:
        """Switch visibility based on mode."""
        self._mode = mode
        if mode == "pdf":
            # PDF mode ignores formatting, resizing and quality for existing docs (only for images).
            # To keep UI calm, just hide the Image formatting choices.
            self.fmt_card.pack_forget()
            self.res_card.pack_forget()
            self.dpi_card.pack_forget()
        else:
            # Re-pack if hidden
            self.fmt_card.pack(fill="x", pady=5, before=self.res_card if self.res_card.winfo_manager() else None)
            self.res_card.pack(fill="x", pady=5, before=self.dpi_card if self.dpi_card.winfo_manager() else None)
            self.dpi_card.pack(fill="x", pady=5, before=self.dir_card)

    def _parse_int(self, raw: str, field: str) -> tuple[int | None, str]:
        raw = raw.strip()
        if not raw: return None, ""
        try:
            val = int(raw)
            if val <= 0: return None, f"{field} must be a positive integer."
            return val, ""
        except ValueError:
            return None, f"{field} must be a whole number."

    def get_options(self, active_mode: str) -> dict | None:
        self.validation_error = ""

        if active_mode == "PDF Studio":
            raw_dir = self._output_dir_var.get().strip()
            return {
                "output_dir": "" if raw_dir == "Same as source" else raw_dir
            }

        dest_format = self._format_var.get()

        w, err = self._parse_int(self._width_var.get(), "Width")
        if err: self.validation_error = err; return None

        h, err = self._parse_int(self._height_var.get(), "Height")
        if err: self.validation_error = err; return None

        dpi, err = self._parse_int(self._dpi_var.get(), "DPI")
        if err: self.validation_error = err; return None

        raw_dir = self._output_dir_var.get().strip()

        return {
            "format": dest_format,
            "quality": self._quality_var.get(),
            "width": w,
            "height": h,
            "maintain_aspect": self._aspect_var.get(),
            "dpi": dpi,
            "output_dir": "" if raw_dir == "Same as source" else raw_dir,
        }
