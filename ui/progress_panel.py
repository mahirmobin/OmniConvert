"""
ProgressPanel — CTkProgressbar with thread-safe live logging.
"""

from __future__ import annotations

import customtkinter as ctk

class ProgressPanel(ctk.CTkFrame):
    
    _COLORS = {
        "info": "#9ca3af",    # Gray
        "success": "#34d399", # Green
        "error": "#f87171",   # Red
        "warning": "#fbbf24", # Yellow
    }

    def __init__(self, master: ctk.CTkFrame, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        # Find the root Tk context for `after` callbacks
        self._main_window = self.winfo_toplevel()
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)

        # Title & Progress row
        top = ctk.CTkFrame(self, fg_color="transparent", height=30)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1) # bar

        self._status_label = ctk.CTkLabel(top, text="Ready", text_color="#a8b2d1", font=("Segoe UI", 12))
        self._status_label.pack(side="left", padx=(0, 15))

        self._progress = ctk.CTkProgressBar(top, progress_color="#2b52ff", border_color="#374151")
        self._progress.pack(side="left", fill="x", expand=True)
        self._progress.set(0) # start at 0

        # Log Text Box
        self._log = ctk.CTkTextbox(
            self, state="disabled", height=60,
            fg_color="#181a20", text_color="#9ca3af", font=("Consolas", 11),
            corner_radius=8, border_width=1, border_color="#374151"
        )
        self._log.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        # We must use Tkinter tags for custom text colors inside CTkTextbox
        for level, color in self._COLORS.items():
            self._log.tag_config(level, foreground=color)

    # ------------------
    # Internal Handlers
    # ------------------
    def _set_progress(self, current: int, total: int) -> None:
        val = 0.0 if total == 0 else min(1.0, current / total)
        self._progress.set(val)

    def _update_status(self, text: str) -> None:
        self._status_label.configure(text=text)

    def _append_log(self, text: str, level: str) -> None:
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n", level)
        self._log.see("end")
        self._log.configure(state="disabled")

    # ------------------
    # Public Thread-Safe API
    # ------------------
    def update(self, current: int, total: int, message: str, level: str = "info") -> None:
        self._main_window.after(0, self._set_progress, current, total)
        self._main_window.after(0, self._update_status, message)
        self._main_window.after(0, self._append_log, message, level)

    def reset(self) -> None:
        self._main_window.after(0, self._set_progress, 0, 1)
        self._main_window.after(0, self._update_status, "Ready")
        
        def _clear_log():
            self._log.configure(state="normal")
            self._log.delete("1.0", "end")
            self._log.configure(state="disabled")
        self._main_window.after(0, _clear_log)

    def log(self, message: str, level: str = "info") -> None:
        self._main_window.after(0, self._append_log, message, level)

