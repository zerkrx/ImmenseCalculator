# widgets.py
import tkinter as tk


class SteppedSpinbox(tk.Frame):
    def __init__(self, parent, min_val=0, max_val=999, bg=None, **kwargs):
        super().__init__(parent, bg=bg)
        self.min_val = min_val
        self.max_val = max_val
        self.var = tk.StringVar(value="0")

        entry_kwargs = {}
        if bg:
            entry_kwargs["bg"] = bg

        self.entry = tk.Entry(self, textvariable=self.var, width=4, **entry_kwargs)
        self.entry.pack(side=tk.LEFT)

        button_bg = bg if bg else "#3a3a3a"
        btn_kwargs = {"width": 2, "bg": button_bg, "fg": "white", "activebackground": "#6f42c1", "activeforeground": "white", "relief": "flat", "bd": 0}

        upbtn = tk.Button(self, text="+", command=self.increase, **btn_kwargs)
        upbtn.pack(side=tk.LEFT, padx=(2,0))

        downbtn = tk.Button(self, text="-", command=self.decrease, **btn_kwargs)
        downbtn.pack(side=tk.LEFT, padx=(2,0))

    def get(self):
        try:
            val = int(self.var.get())
            if val < self.min_val:
                return self.min_val
            if val > self.max_val:
                return self.max_val
            return val
        except Exception:
            return 0

    def set(self, val):
        self.var.set(str(val))

    def increase(self):
        val = self.get() + 1
        if val > self.max_val:
            val = self.max_val
        self.set(val)

    def decrease(self):
        val = self.get() - 1
        if val < self.min_val:
            val = self.min_val
        self.set(val)