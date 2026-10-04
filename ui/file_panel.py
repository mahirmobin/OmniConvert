"""
FilePanel — CustomTkinter adaptation of the drag-and-drop zone + scrollable file list.
"""

from __future__ import annotations
import os
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog

try:
    from tkinterdnd2 import DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False


class FilePanel(ctk.CTkFrame):
    def __init__(self, master: ctk.CTkFrame, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._files: list[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Drop Zone
        self._drop_zone = ctk.CTkButton(
            self,
            text="⬇ Drop images here\nor click Add Files",
            fg_color="#21252e", hover_color="#2a303c",
            text_color="#9ca3af", font=("Segoe UI", 16, "bold"),
            height=100, corner_radius=12,
            command=self._browse
        )
        self._drop_zone.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        if _DND_AVAILABLE:
            # We must register on the widget's underlying tk root/canvas. 
            # CustomTkinter widgets wrap tk.Canvas. We bind carefully.
            try:
                self._drop_zone._canvas.drop_target_register(DND_FILES)
                self._drop_zone._canvas.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass # Graceful fallback if wrapper changes

        # Scrollable Frame
        self._scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#181a20", corner_radius=8)
        self._scroll_frame.grid(row=1, column=0, sticky="nsew")

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        ctk.CTkButton(
            toolbar, text="➕ Add Files", command=self._browse,
            fg_color="#374151", hover_color="#4b5563",
            font=("Segoe UI", 12, "bold"), width=120, height=32
        ).pack(side="left")

        ctk.CTkButton(
            toolbar, text="🗑 Clear All", command=self.clear,
            fg_color="transparent", hover_color="#374151", border_width=1, border_color="#374151",
            text_color="#9ca3af", font=("Segoe UI", 12), width=100, height=32
        ).pack(side="left", padx=10)

        self._count_label = ctk.CTkLabel(toolbar, text="0 files", text_color="#6b7280", font=("Segoe UI", 12))
        self._count_label.pack(side="right")

    def _browse(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif *.gif *.ico"), ("All files", "*.*"))
        )
        self._add_paths(list(paths))

    def _on_drop(self, event) -> None:
        raw: str = event.data
        paths = []
        if raw.startswith("{"):
            raw = raw.strip("{}")
            for part in raw.split("} {"):
                p = part.strip("{} \n")
                if p: paths.append(p)
        else:
            paths = raw.split()
        self._add_paths(paths)

    def _add_paths(self, paths: list[str]) -> None:
        existing = set(self._files)
        for p in paths:
            p = p.strip()
            if p and os.path.isfile(p) and p not in existing:
                self._files.append(p)
                existing.add(p)
                self._add_row(p)
        self._update_count()

    def _add_row(self, path: str) -> None:
        row = ctk.CTkFrame(self._scroll_frame, fg_color="#21252e", corner_radius=6)
        row.pack(fill="x", padx=4, pady=4)
        
        name = Path(path).name
        ctk.CTkLabel(row, text=f" {name}", text_color="#e2e8f0", font=("Segoe UI", 13), anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=6)
        
        ctk.CTkButton(
            row, text="✕", width=30, height=30, fg_color="transparent",
            text_color="#ef4444", hover_color="#374151", font=("Segoe UI", 14, "bold"),
            command=lambda p=path, r=row: self._remove_file(p, r)
        ).pack(side="right", padx=5)

    def _remove_file(self, path: str, row: ctk.CTkFrame) -> None:
        if path in self._files:
            self._files.remove(path)
        row.destroy()
        self._update_count()

    def _update_count(self) -> None:
        self._count_label.configure(text=f"{len(self._files)} files")

    def get_files(self) -> list[str]:
        return list(self._files)

    def clear(self) -> None:
        self._files.clear()
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._update_count()
