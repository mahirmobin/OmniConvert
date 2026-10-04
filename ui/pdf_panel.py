"""
PdfStudioPanel — Visual sequence builder for merging PDFs/Images.
"""

from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog
import customtkinter as ctk

try:
    from tkinterdnd2 import DND_FILES
    _DND_AVAILABLE = True
except ImportError:
    _DND_AVAILABLE = False


class PdfStudioPanel(ctk.CTkFrame):
    """
    Shows thumbnails of imported PDFs/images. 
    Allows basic drag/reorder controls or Up/Down buttons per row to keep it robust.
    """

    def __init__(self, master: ctk.CTkFrame, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._items: list[str] = []  # Paths of added files in order
        self._row_widgets: dict[str, ctk.CTkFrame] = {} # Path -> Frame
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Drop Zone
        self._drop_zone = ctk.CTkButton(
            self,
            text="⬇ Drop PDFs or Images here to Combine",
            fg_color="#2b2d35", hover_color="#3a3d46",
            text_color="#8b949e", font=("Segoe UI", 16, "bold"),
            height=100, corner_radius=12,
            command=self._browse
        )
        self._drop_zone.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        if _DND_AVAILABLE:
            try:
                self._drop_zone._canvas.drop_target_register(DND_FILES)
                self._drop_zone._canvas.dnd_bind("<<Drop>>", self._on_drop)
            except Exception:
                pass

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
            toolbar, text="🗑 Clear", command=self.clear,
            fg_color="transparent", hover_color="#374151", border_width=1, border_color="#374151",
            text_color="#9ca3af", font=("Segoe UI", 12), width=100, height=32
        ).pack(side="left", padx=10)

        self._count_label = ctk.CTkLabel(toolbar, text="0 items", text_color="#6b7280", font=("Segoe UI", 12))
        self._count_label.pack(side="right")

    def _browse(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select PDFs or Images",
            filetypes=(("Valid files", "*.pdf *.jpg *.jpeg *.png *.webp"), ("All files", "*.*"))
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
        for p in paths:
            p = p.strip()
            if p and os.path.isfile(p) and p not in self._items:
                self._items.append(p)
        self._refresh_list()

    def _refresh_list(self) -> None:
        # Clear UI without clearing actual items list
        for w in self._scroll_frame.winfo_children():
            w.destroy()
        self._row_widgets.clear()

        # Re-render in order
        for idx, path in enumerate(self._items):
            self._render_row(path, idx)
        
        self._count_label.configure(text=f"{len(self._items)} items")

    def _render_row(self, path: str, index: int) -> None:
        row = ctk.CTkFrame(self._scroll_frame, fg_color="#21252e", corner_radius=6)
        row.pack(fill="x", padx=4, pady=4)
        self._row_widgets[path] = row

        # Thumb loading (can be slow, but this is simple synchronous for now)
        try:
            from core.pdf_studio import render_pdf_preview
            from PIL import ImageTk
            thumb = render_pdf_preview(path, size=(40, 50))
            ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(40, 50))
            img_lbl = ctk.CTkLabel(row, image=ctk_img, text="", width=40)
            img_lbl.image = ctk_img # Keep ref
            img_lbl.pack(side="left", padx=10, pady=5)
        except Exception:
            # Fallback icon
            ctk.CTkLabel(row, text="📄", font=("Arial", 24)).pack(side="left", padx=15)
        
        name = Path(path).name
        ctk.CTkLabel(row, text=name, text_color="#e2e8f0", font=("Segoe UI", 13), anchor="w").pack(side="left", fill="x", expand=True, padx=5)
        
        # Ordering buttons
        ctk.CTkButton(
            row, text="▲", width=30, height=30, fg_color="#374151", hover_color="#4b5563",
            command=lambda p=path: self._move_item(p, -1)
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            row, text="▼", width=30, height=30, fg_color="#374151", hover_color="#4b5563",
            command=lambda p=path: self._move_item(p, 1)
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            row, text="✕", width=30, height=30, fg_color="transparent", hover_color="#4b5563", text_color="#ef4444",
            command=lambda p=path: self._remove_file(p)
        ).pack(side="right", padx=10)

    def _move_item(self, path: str, direction: int) -> None:
        idx = self._items.index(path)
        new_idx = idx + direction
        if 0 <= new_idx < len(self._items):
            # Swap
            self._items[idx], self._items[new_idx] = self._items[new_idx], self._items[idx]
            self._refresh_list()

    def _remove_file(self, path: str) -> None:
        self._items.remove(path)
        self._refresh_list()

    def get_files(self) -> list[str]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
        self._refresh_list()

