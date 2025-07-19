# menu_editor.py

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from widgets import SteppedSpinbox
from menu_manager import load_menu, save_menu
from PIL import Image, ImageTk
import os
import io
import requests
import colors
from style_helper import apply_default_style


class ScrollableFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel scrolling when cursor is over the scrollable_frame area
        self._bind_mousewheel()

    def _bind_mousewheel(self):
        # Windows and MacOS bindings
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        # Linux bindings
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class MenuEditorWindow:
    def __init__(self, root, establishment, on_save_callback=None):
        self.on_save_callback = on_save_callback
        self.root = root
        self.establishment = establishment
        self.menu = load_menu(establishment)
        self.image_path = self.menu.get("menu_image_path", None)

        # Apply styling and theme
        self.style = ttk.Style(root)
        self.setup_styles()
        root.configure(bg=colors.BG_COLOR)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.notebook = ttk.Notebook(root, style="Custom.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tab_sections = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_sections, text="Sections & Items")
        self.create_sections_items_tab()

        self.tab_prices = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_prices, text="Item Prices")
        self.create_prices_tab()

        self.tab_combos = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_combos, text="Combo Specials")
        self.create_combos_tab()

        self.tab_discounts = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_discounts, text="Discounts")
        self.create_discounts_tab()

        self.tab_image = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.tab_image, text="Menu Image")
        self.create_image_tab()

        self.load_sections()
        self.load_prices()
        self.load_combos()
        self.load_discounts()
        self.load_image_tab()

    def setup_styles(self):
        # Custom notebook style for visible focus and theme colors
        self.style.theme_use("clam")

        # Style for notebook tabs to be more visible and thematic
        self.style.configure(
            "Custom.TNotebook", background=colors.BG_COLOR, borderwidth=0, tabposition='n'
        )
        self.style.configure(
            "Custom.TNotebook.Tab",
            background=colors.PANEL_BG,
            foreground=colors.FG_COLOR,
            padding=(10, 5),
            font=("Segoe UI", 10, "bold")
        )
        self.style.map(
            "Custom.TNotebook.Tab",
            background=[("selected", colors.ACCENT_COLOR), ("active", colors.BUTTON_HOVER_BG)],
            foreground=[("selected", "white")]
        )
        # Style for frames inside tabs
        self.style.configure("TFrame", background=colors.BG_COLOR)

    # ============ Sections & Items Tab =============
    def create_sections_items_tab(self):
        frame = self.tab_sections
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)

        sec_frame = ttk.LabelFrame(frame, text="Sections")
        sec_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)

        self.lb_sections = tk.Listbox(sec_frame, height=20, exportselection=False,
                                     bg=colors.SUBPANEL_BG, fg=colors.FG_COLOR,
                                     selectbackground=colors.ACCENT_COLOR, selectforeground="white")
        self.lb_sections.pack(fill=tk.Y, expand=True)
        self.lb_sections.bind("<<ListboxSelect>>", self.on_section_select)

        self.entry_section = tk.Entry(sec_frame)
        self.entry_section.pack(fill=tk.X, padx=5, pady=2)
        btn_sec_add = tk.Button(sec_frame, text="Add Section", command=self.add_section)
        btn_sec_add.pack(fill=tk.X, padx=5)
        btn_sec_rm = tk.Button(sec_frame, text="Remove Section", command=self.remove_section)
        btn_sec_rm.pack(fill=tk.X, padx=5, pady=(0, 5))

        subsec_frame = ttk.LabelFrame(frame, text="Sub-Sections")
        subsec_frame.grid(row=0, column=1, sticky="ns", padx=5, pady=5)

        self.lb_subsections = tk.Listbox(subsec_frame, height=10, exportselection=False,
                                        bg=colors.SUBPANEL_BG, fg=colors.FG_COLOR,
                                        selectbackground=colors.ACCENT_COLOR, selectforeground="white")
        self.lb_subsections.pack(fill=tk.Y, expand=True)
        self.lb_subsections.bind("<<ListboxSelect>>", self.on_subsection_select)

        self.entry_subsection = tk.Entry(subsec_frame)
        self.entry_subsection.pack(fill=tk.X, padx=5, pady=2)
        btn_subsec_add = tk.Button(subsec_frame, text="Add Sub-Section", command=self.add_subsection)
        btn_subsec_add.pack(fill=tk.X, padx=5)
        btn_subsec_rm = tk.Button(subsec_frame, text="Remove Sub-Section", command=self.remove_subsection)
        btn_subsec_rm.pack(fill=tk.X, padx=5, pady=(0, 5))

        item_frame = ttk.LabelFrame(frame, text="Items")
        item_frame.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)

        self.scrollable_items_frame = ScrollableFrame(item_frame)
        self.scrollable_items_frame.pack(fill=tk.BOTH, expand=True)

        self.lb_items = tk.Listbox(self.scrollable_items_frame.scrollable_frame, height=15, exportselection=False,
                                   bg=colors.SUBPANEL_BG, fg=colors.FG_COLOR,
                                   selectbackground=colors.ACCENT_COLOR, selectforeground="white")
        self.lb_items.pack(fill=tk.BOTH, expand=True)
        self.lb_items.bind("<<ListboxSelect>>", self.on_item_select)

        self.entry_item = tk.Entry(item_frame)
        self.entry_item.pack(fill=tk.X, padx=5, pady=2)

        btn_item_add = tk.Button(item_frame, text="Add Item", command=self.add_item)
        btn_item_add.pack(fill=tk.X, padx=5)
        btn_item_rm = tk.Button(item_frame, text="Remove Item", command=self.remove_item)
        btn_item_rm.pack(fill=tk.X, padx=5, pady=(0, 5))

        limit_frame = ttk.Frame(item_frame)
        limit_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(limit_frame, text="Item Limit (0 = no limit):", bg=colors.BG_COLOR, fg=colors.FG_COLOR).pack(anchor=tk.W)
        self.entry_item_limit = tk.Entry(limit_frame)
        self.entry_item_limit.pack(fill=tk.X)

        btn_limit_set = tk.Button(limit_frame, text="Set Item Limit", command=self.set_item_limit)
        btn_limit_set.pack(fill=tk.X, pady=3)

    # Helpers for case-insensitive lookups to preserve original names
    def _get_section_real_name(self, lookup):
        sections = self.menu.get("sections", {})
        for sec in sections:
            if sec.lower() == lookup.lower():
                return sec
        return None

    def _get_subsection_real_name(self, section, lookup):
        sections = self.menu.get("sections", {})
        real_section = self._get_section_real_name(section)
        if not real_section:
            return None
        val = sections.get(real_section)
        if isinstance(val, dict):
            for subsec in val:
                if subsec.lower() == lookup.lower():
                    return subsec
        return None

    def on_section_select(self, event):
        sel = self.lb_sections.curselection()
        if not sel:
            self.lb_subsections.delete(0, tk.END)
            self.lb_items.delete(0, tk.END)
            self.entry_item_limit.delete(0, tk.END)
            return
        lookup = self.lb_sections.get(sel[0])
        real_section = self._get_section_real_name(lookup)
        if not real_section:
            self.lb_subsections.delete(0, tk.END)
            self.lb_items.delete(0, tk.END)
            self.entry_item_limit.delete(0, tk.END)
            return
        val = self.menu["sections"].get(real_section, {})
        self.lb_subsections.delete(0, tk.END)
        self.lb_items.delete(0, tk.END)
        if isinstance(val, dict):
            for subsec in val:
                self.lb_subsections.insert(tk.END, subsec)
            if val:
                self.lb_subsections.selection_set(0)
                self.lb_subsections.event_generate("<<ListboxSelect>>")
        elif isinstance(val, list):
            for item in val:
                self.lb_items.insert(tk.END, item)
        else:
            if real_section.lower() == "combos" and isinstance(val, dict):
                for combo in val.keys():
                    self.lb_items.insert(tk.END, combo)

    def on_subsection_select(self, event):
        sel_section = self.lb_sections.curselection()
        sel_subsec = self.lb_subsections.curselection()
        if not sel_section or not sel_subsec:
            self.lb_items.delete(0, tk.END)
            self.entry_item_limit.delete(0, tk.END)
            return
        section_lookup = self.lb_sections.get(sel_section[0])
        subsection_lookup = self.lb_subsections.get(sel_subsec[0])
        real_section = self._get_section_real_name(section_lookup)
        real_subsection = self._get_subsection_real_name(real_section, subsection_lookup)
        if not real_section or not real_subsection:
            self.lb_items.delete(0, tk.END)
            self.entry_item_limit.delete(0, tk.END)
            return
        val = self.menu["sections"][real_section].get(real_subsection, [])
        self.lb_items.delete(0, tk.END)
        for item in val:
            self.lb_items.insert(tk.END, item)
        if val:
            self.lb_items.selection_set(0)
            self.lb_items.event_generate("<<ListboxSelect>>")

    def on_item_select(self, event):
        sel = self.lb_items.curselection()
        if not sel:
            self.entry_item_limit.delete(0, tk.END)
            return
        item = self.lb_items.get(sel[0])
        limit = self.menu.get("item_limits", {}).get(item, 0)
        self.entry_item_limit.delete(0, tk.END)
        self.entry_item_limit.insert(0, str(limit))

    def add_section(self):
        name = self.entry_section.get().strip()
        if not name:
            messagebox.showwarning("Input needed", "Please enter a section name")
            return
        secs = self.menu.setdefault("sections", {})
        if any(s.lower() == name.lower() for s in secs):
            messagebox.showwarning("Exists", "Section already exists")
            return
        secs[name] = []
        self.entry_section.delete(0, tk.END)
        self.load_sections()
        self.save_menu()
        idx = list(secs.keys()).index(name)
        self.lb_sections.selection_clear(0, tk.END)
        self.lb_sections.selection_set(idx)
        self.lb_sections.event_generate("<<ListboxSelect>>")

    def remove_section(self):
        sel = self.lb_sections.curselection()
        if not sel:
            messagebox.showwarning("Select", "Select a section first")
            return
        lookup = self.lb_sections.get(sel[0])
        real_sec = self._get_section_real_name(lookup)
        if not real_sec:
            messagebox.showerror("Error", "Section not found")
            return
        if messagebox.askyesno("Confirm", f"Remove section '{real_sec}'?"):
            self.menu["sections"].pop(real_sec, None)
            self.load_sections()
            self.save_menu()
            secs = self.menu.get("sections", {})
            if secs:
                first = sorted(secs.keys())[0]
                idx = list(secs.keys()).index(first)
                self.lb_sections.selection_clear(0, tk.END)
                self.lb_sections.selection_set(idx)
                self.lb_sections.event_generate("<<ListboxSelect>>")
            else:
                self.lb_sections.selection_clear(0, tk.END)
                self.lb_subsections.delete(0, tk.END)
                self.lb_items.delete(0, tk.END)
                self.entry_item_limit.delete(0, tk.END)

    def add_subsection(self):
        sel_section = self.lb_sections.curselection()
        if not sel_section:
            messagebox.showwarning("Select", "Select a section first")
            return
        sec_lookup = self.lb_sections.get(sel_section[0])
        real_sec = self._get_section_real_name(sec_lookup)
        secs = self.menu.setdefault("sections", {})
        val = secs.get(real_sec, [])
        if isinstance(val, list):
            secs[real_sec] = {"default": val}
            val = secs[real_sec]
        name = self.entry_subsection.get().strip()
        if not name:
            messagebox.showwarning("Input needed", "Enter sub-section name")
            return
        if any(s.lower() == name.lower() for s in val):
            messagebox.showwarning("Exists", "Sub-section already exists")
            return
        val[name] = []
        self.entry_subsection.delete(0, tk.END)
        self.load_sections()
        idx = list(secs.keys()).index(real_sec)
        self.lb_sections.selection_clear(0, tk.END)
        self.lb_sections.selection_set(idx)
        self.lb_sections.event_generate("<<ListboxSelect>>")

        idx_sub = list(val.keys()).index(name)
        self.lb_subsections.selection_clear(0, tk.END)
        self.lb_subsections.selection_set(idx_sub)
        self.lb_subsections.event_generate("<<ListboxSelect>>")
        self.save_menu()

    def remove_subsection(self):
        sel_section = self.lb_sections.curselection()
        sel_subsection = self.lb_subsections.curselection()
        if not sel_section or not sel_subsection:
            messagebox.showwarning("Select", "Select section and sub-section")
            return
        sec_lookup = self.lb_sections.get(sel_section[0])
        subsec_lookup = self.lb_subsections.get(sel_subsection[0])
        real_sec = self._get_section_real_name(sec_lookup)
        real_subsec = self._get_subsection_real_name(real_sec, subsec_lookup)
        if not real_sec or not real_subsec:
            messagebox.showerror("Error", "Invalid selection")
            return
        if messagebox.askyesno("Confirm", f"Remove sub-section '{real_subsec}'?"):
            self.menu["sections"][real_sec].pop(real_subsec, None)
            self.load_sections()
            idx = list(self.menu["sections"].keys()).index(real_sec)
            self.lb_sections.selection_clear(0, tk.END)
            self.lb_sections.selection_set(idx)
            self.lb_sections.event_generate("<<ListboxSelect>>")
            self.save_menu()
            val = self.menu["sections"].get(real_sec, {})
            if isinstance(val, dict) and val:
                first = sorted(val.keys())[0]
                idx_sub = list(val.keys()).index(first)
                self.lb_subsections.selection_clear(0, tk.END)
                self.lb_subsections.selection_set(idx_sub)
                self.lb_subsections.event_generate("<<ListboxSelect>>")
            else:
                self.lb_subsections.selection_clear(0, tk.END)
                self.lb_items.delete(0, tk.END)
                self.entry_item_limit.delete(0, tk.END)

    def add_item(self):
        sel_section = self.lb_sections.curselection()
        if not sel_section:
            messagebox.showwarning("Select", "Select a section")
            return
        sec_lookup = self.lb_sections.get(sel_section[0])
        real_sec = self._get_section_real_name(sec_lookup)
        if not real_sec:
            messagebox.showerror("Error", "Section not found")
            return
        secs = self.menu.setdefault("sections", {})
        val = secs.get(real_sec)

        new_item = self.entry_item.get().strip()
        if not new_item:
            messagebox.showwarning("Input needed", "Enter item name")
            return

        if real_sec.lower() == "drinks":
            if isinstance(val, list):
                if new_item in val:
                    messagebox.showwarning("Exists", "Item already exists")
                    return
                val.append(new_item)
            elif isinstance(val, dict):
                sel_subsec = self.lb_subsections.curselection()
                subsec = None
                if sel_subsec:
                    subsec_lookup = self.lb_subsections.get(sel_subsec[0])
                    subsec = self._get_subsection_real_name(real_sec, subsec_lookup)
                if subsec is None:
                    if "default" not in val:
                        val["default"] = []
                        self.load_sections()
                        idx = list(secs.keys()).index(real_sec)
                        self.lb_sections.selection_clear(0, tk.END)
                        self.lb_sections.selection_set(idx)
                        self.lb_sections.event_generate("<<ListboxSelect>>")
                        idx_sub = list(val.keys()).index("default")
                        self.lb_subsections.selection_clear(0, tk.END)
                        self.lb_subsections.selection_set(idx_sub)
                        self.lb_subsections.event_generate("<<ListboxSelect>>")
                    subsec = "default"
                if new_item in val.get(subsec, []):
                    messagebox.showwarning("Exists", "Item already exists")
                    return
                val[subsec].append(new_item)
        else:
            if isinstance(val, dict):
                sel_subsec = self.lb_subsections.curselection()
                if not sel_subsec:
                    messagebox.showwarning("Select", "Select a sub-section")
                    return
                subsec_lookup = self.lb_subsections.get(sel_subsec[0])
                subsec = self._get_subsection_real_name(real_sec, subsec_lookup)
                if not subsec:
                    messagebox.showerror("Error", "Sub-section not found")
                    return
                if new_item in val.get(subsec, []):
                    messagebox.showwarning("Exists", "Item already exists")
                    return
                val[subsec].append(new_item)
            elif isinstance(val, list):
                if new_item in val:
                    messagebox.showwarning("Exists", "Item already exists")
                    return
                val.append(new_item)
            else:
                messagebox.showwarning("Invalid", "Selected section invalid for adding items")
                return

        self.entry_item.delete(0, tk.END)
        self.load_sections()

        idx = list(secs.keys()).index(real_sec)
        self.lb_sections.selection_clear(0, tk.END)
        self.lb_sections.selection_set(idx)
        self.lb_sections.event_generate("<<ListboxSelect>>")

        val_new = secs.get(real_sec)
        if isinstance(val_new, dict):
            sel_subsec = self.lb_subsections.curselection()
            if sel_subsec:
                sel_subsec_lookup = self.lb_subsections.get(sel_subsec[0])
                sel_subsec_real = self._get_subsection_real_name(real_sec, sel_subsec_lookup)
                idx_sub = list(val_new.keys()).index(sel_subsec_real)
                self.lb_subsections.selection_clear(0, tk.END)
                self.lb_subsections.selection_set(idx_sub)
                self.lb_subsections.event_generate("<<ListboxSelect>>")
                items = val_new.get(sel_subsec_real, [])
                if new_item in items:
                    idx_item = items.index(new_item)
                    self.lb_items.selection_clear(0, tk.END)
                    self.lb_items.selection_set(idx_item)
                    self.lb_items.event_generate("<<ListboxSelect>>")
        else:
            items = val_new
            if new_item in items:
                idx_item = items.index(new_item)
                self.lb_items.selection_clear(0, tk.END)
                self.lb_items.selection_set(idx_item)
                self.lb_items.event_generate("<<ListboxSelect>>")

        self.save_menu()
        self.load_prices()

    def remove_item(self):
        sel_section = self.lb_sections.curselection()
        sel_item = self.lb_items.curselection()
        if not sel_section or not sel_item:
            messagebox.showwarning("Select", "Select section and item")
            return
        sec_lookup = self.lb_sections.get(sel_section[0])
        item = self.lb_items.get(sel_item[0])
        real_sec = self._get_section_real_name(sec_lookup)
        if not real_sec:
            messagebox.showerror("Error", "Section not found")
            return
        secs = self.menu.setdefault("sections", {})
        val = secs.get(real_sec)

        if real_sec.lower() == "drinks":
            if isinstance(val, list):
                if item in val:
                    val.remove(item)
            elif isinstance(val, dict):
                sel_subsec = self.lb_subsections.curselection()
                subsec = None
                if sel_subsec:
                    subsec_lookup = self.lb_subsections.get(sel_subsec[0])
                    subsec = self._get_subsection_real_name(real_sec, subsec_lookup)
                if subsec and item in val.get(subsec, []):
                    val[subsec].remove(item)
        else:
            if isinstance(val, dict):
                sel_subsec = self.lb_subsections.curselection()
                if not sel_subsec:
                    messagebox.showwarning("Select", "Select a sub-section")
                    return
                subsec_lookup = self.lb_subsections.get(sel_subsec[0])
                subsec = self._get_subsection_real_name(real_sec, subsec_lookup)
                if subsec and item in val.get(subsec, []):
                    val[subsec].remove(item)
            elif isinstance(val, list):
                if item in val:
                    val.remove(item)

        self.menu.get("item_limits", {}).pop(item, None)
        self.menu.get("prices", {}).pop(item, None)
        for disc in self.menu.get("discounts", {}).values():
            if "bypass_items" in disc and item in disc["bypass_items"]:
                disc["bypass_items"].remove(item)
        self.load_sections()
        self.save_menu()

        idx = list(secs.keys()).index(real_sec)
        self.lb_sections.selection_clear(0, tk.END)
        self.lb_sections.selection_set(idx)
        self.lb_sections.event_generate("<<ListboxSelect>>")

        self.load_prices()

    def set_item_limit(self):
        sel = self.lb_items.curselection()
        if not sel:
            messagebox.showwarning("Select", "Select an item")
            return
        item = self.lb_items.get(sel[0])
        try:
            limit = int(self.entry_item_limit.get())
            if limit < 0:
                raise ValueError()
        except Exception:
            messagebox.showwarning("Invalid", "Limit must be a non-negative integer")
            return
        if limit == 0:
            self.menu.get("item_limits", {}).pop(item, None)
        else:
            self.menu.setdefault("item_limits", {})[item] = limit
        messagebox.showinfo("Success", f"Set limit for {item} to {limit}")
        self.save_menu()

    def load_sections(self):
        self.lb_sections.delete(0, tk.END)
        for sec in sorted(self.menu.get("sections", {}).keys()):
            self.lb_sections.insert(tk.END, sec)
        self.lb_subsections.delete(0, tk.END)
        self.lb_items.delete(0, tk.END)
        self.entry_item_limit.delete(0, tk.END)

    def create_prices_tab(self):
        frame = self.tab_prices
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.scroll_prices = ScrollableFrame(frame)
        self.scroll_prices.pack(fill=tk.BOTH, expand=True)

        self.price_vars = {}

    def load_prices(self):
        for w in self.scroll_prices.scrollable_frame.winfo_children():
            w.destroy()
        self.price_vars.clear()

        all_items = set()
        for sec, val in self.menu.get("sections", {}).items():
            if sec == "combos":
                continue
            if isinstance(val, dict):
                for sublist in val.values():
                    all_items.update(sublist)
            elif isinstance(val, list):
                all_items.update(val)

        combos = self.menu.get("sections", {}).get("combos", {})
        all_items.update(combos.keys())

        for item in sorted(all_items):
            row = ttk.Frame(self.scroll_prices.scrollable_frame)
            row.pack(fill=tk.X, pady=2, padx=10)

            lbl = ttk.Label(row, text=item, width=25)
            lbl.pack(side=tk.LEFT)

            prices = self.menu.get("prices", {})
            if item in combos:
                price_val = prices.get("combos", {}).get(item, 0)
            else:
                price_val = prices.get(item, "")

            var = tk.StringVar(value=str(price_val))

            def on_price_change(*args, var=var):
                self.save_menu()

            var.trace_add("write", on_price_change)
            ent = ttk.Entry(row, textvariable=var, width=10)
            ent.pack(side=tk.LEFT, padx=10)
            self.price_vars[item] = var

    def save_prices(self):
        prices = self.menu.setdefault("prices", {})
        to_remove = []
        for key in list(prices.keys()):
            if key != "combos" and key not in self.price_vars:
                to_remove.append(key)
        for key in to_remove:
            prices.pop(key, None)
        combos_prices = prices.setdefault("combos", {})
        for item, var in self.price_vars.items():
            val = var.get().strip()
            if val == "":
                if item in combos_prices:
                    combos_prices.pop(item, None)
                if item in prices:
                    prices.pop(item, None)
                continue
            try:
                fval = float(val)
                if fval < 0:
                    raise ValueError
                if item in self.menu.get("sections", {}).get("combos", {}):
                    combos_prices[item] = fval
                else:
                    prices[item] = fval
            except Exception:
                messagebox.showerror("Invalid Value", f"Price '{val}' for item '{item}' is invalid.")
                return False
        return True

    def create_combos_tab(self):
        frame = self.tab_combos

        top_frame = ttk.Frame(frame)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        self.lb_combos = tk.Listbox(top_frame, height=12, exportselection=False)
        self.lb_combos.pack(side=tk.LEFT, fill=tk.Y)
        self.lb_combos.bind("<<ListboxSelect>>", self.on_combo_select)

        combo_ops = ttk.Frame(top_frame)
        combo_ops.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        self.combo_price_var = tk.StringVar()
        ttk.Label(combo_ops, text="Combo Price:").pack(anchor=tk.W)
        self.combo_price_entry = ttk.Entry(combo_ops, textvariable=self.combo_price_var)
        self.combo_price_entry.pack(fill=tk.X, pady=3)

        self.combo_mam_var = tk.IntVar()
        self.mixm_cb = ttk.Checkbutton(combo_ops, text="Mix & Match Combo Items", variable=self.combo_mam_var,
                                       command=self.on_mix_and_match_changed)
        self.mixm_cb.pack(pady=3)

        self.limits_frame = ttk.Frame(combo_ops)
        self.limits_frame.pack(fill=tk.X, pady=5)

        ttk.Label(self.limits_frame, text="Max allowed per section (Mix & Match only):").pack(anchor=tk.W)

        lbl_food = ttk.Label(self.limits_frame, text="Food max:")
        lbl_food.pack(anchor=tk.W, pady=(2, 0))
        self.combo_limit_food_var = tk.IntVar(value=0)
        self.ent_combo_limit_food = ttk.Spinbox(self.limits_frame, from_=0, to=999, textvariable=self.combo_limit_food_var)
        self.ent_combo_limit_food.pack(fill=tk.X, pady=(0, 5))

        lbl_drinks = ttk.Label(self.limits_frame, text="Drinks max:")
        lbl_drinks.pack(anchor=tk.W, pady=(2, 0))
        self.combo_limit_drinks_var = tk.IntVar(value=0)
        self.ent_combo_limit_drinks = ttk.Spinbox(self.limits_frame, from_=0, to=999, textvariable=self.combo_limit_drinks_var)
        self.ent_combo_limit_drinks.pack(fill=tk.X, pady=(0, 5))

        lbl_desserts = ttk.Label(self.limits_frame, text="Desserts max:")
        lbl_desserts.pack(anchor=tk.W, pady=(2, 0))
        self.combo_limit_desserts_var = tk.IntVar(value=0)
        self.ent_combo_limit_desserts = ttk.Spinbox(self.limits_frame, from_=0, to=999, textvariable=self.combo_limit_desserts_var)
        self.ent_combo_limit_desserts.pack(fill=tk.X, pady=(0, 5))

        self.combo_items_container = ttk.Frame(frame)
        self.combo_items_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.combo_dynamic_lbs = {}
        self._fixed_combo_item_spinboxes = {}

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5, padx=10)

        ttk.Button(btn_frame, text="Add Combo", command=self.add_combo_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove Combo", command=self.remove_combo).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update Combo", command=self.update_combo).pack(side=tk.LEFT, padx=5)

        self.load_combos()

    def add_combo_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("Add Combo Special")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.transient(self.root)

        ttk.Label(dlg, text="Combo Name:").pack(anchor=tk.W, padx=10, pady=5)
        entry_name = ttk.Entry(dlg)
        entry_name.pack(fill=tk.X, padx=10)
        ttk.Label(dlg, text="Combo Price:").pack(anchor=tk.W, padx=10, pady=5)
        entry_price = ttk.Entry(dlg)
        entry_price.pack(fill=tk.X, padx=10)

        mixm_var = tk.IntVar()
        mixm_cb = ttk.Checkbutton(dlg, text="Mix & Match Combo Items", variable=mixm_var)
        mixm_cb.pack(anchor=tk.W, padx=10, pady=5)

        def on_confirm():
            name = entry_name.get().strip()
            if not name:
                messagebox.showwarning("Name Required", "Please enter a combo name", parent=dlg)
                return
            price_str = entry_price.get().strip()
            try:
                price = float(price_str)
                if price < 0:
                    raise ValueError()
            except Exception:
                messagebox.showwarning("Invalid Price", "Please enter a valid positive price", parent=dlg)
                return

            combos = self.menu.setdefault("sections", {}).setdefault("combos", {})
            if name in combos:
                messagebox.showwarning("Exists", "Combo name already exists", parent=dlg)
                return

            combos[name] = {
                "price": price,
                "mix_and_match": bool(mixm_var.get()),
                "combo_items": { "food": [], "drinks": [], "desserts": [] } if mixm_var.get() else { "food": {}, "drinks": {}, "desserts": {} },
                "limits": { "food": 0, "drinks": 0, "desserts": 0 }
            }

            prices_combos = self.menu.setdefault("prices", {}).setdefault("combos", {})
            prices_combos[name] = price

            self.load_combos()
            idx = list(combos.keys()).index(name)
            self.lb_combos.selection_clear(0, tk.END)
            self.lb_combos.selection_set(idx)
            self.lb_combos.event_generate("<<ListboxSelect>>")
            self.save_menu()
            messagebox.showinfo("Combo Added", f"Combo '{name}' added successfully", parent=dlg)
            dlg.destroy()

        btn_confirm = ttk.Button(dlg, text="Confirm", command=on_confirm)
        btn_confirm.pack(pady=10)

        dlg.bind("<Return>", lambda e: on_confirm())

    def on_mix_and_match_changed(self):
        state = "normal"
        self.mixm_cb.config(state=state)
        sel = self.lb_combos.curselection()
        if not sel:
            return
        self.on_combo_select()

    def load_combos(self):
        self.lb_combos.delete(0, tk.END)
        combos = self.menu.get("sections", {}).get("combos", {})
        for combo_name in sorted(combos.keys()):
            self.lb_combos.insert(tk.END, combo_name)
        self.clear_combo_details()

    def clear_combo_details(self):
        self.combo_price_var.set("")
        self.combo_mam_var.set(0)
        self.combo_limit_food_var.set(0)
        self.combo_limit_drinks_var.set(0)
        self.combo_limit_desserts_var.set(0)
        for widget in self.combo_items_container.winfo_children():
            widget.destroy()
        self.combo_dynamic_lbs.clear()
        self._fixed_combo_item_spinboxes.clear()

    def on_combo_select(self, event=None):
        sel = self.lb_combos.curselection()
        if not sel:
            self.clear_combo_details()
            return
        combo_name = self.lb_combos.get(sel[0])
        combo = self.menu["sections"]["combos"].get(combo_name, {})
        if not combo:
            self.clear_combo_details()
            return

        self.combo_price_var.set(str(combo.get("price", 0)))
        self.combo_mam_var.set(1 if combo.get("mix_and_match", False) else 0)

        limits = combo.get("limits", { "food": 0, "drinks": 0, "desserts": 0 })
        self.combo_limit_food_var.set(limits.get("food", 0))
        self.combo_limit_drinks_var.set(limits.get("drinks", 0))
        self.combo_limit_desserts_var.set(limits.get("desserts", 0))

        self.mixm_cb.config(state="normal")

        if self.combo_mam_var.get():
            self.limits_frame.pack(fill=tk.X, pady=5)
            combo_items = combo.get("combo_items", { "food": [], "drinks": [], "desserts": [] })
            self._populate_combo_allowed_items_selection(combo_items)
        else:
            self.limits_frame.pack_forget()
            combo_items = combo.get("combo_items", { "food": {}, "drinks": {}, "desserts": {} })
            self._populate_combo_fixed_quantity_edit(combo_items)

    def _populate_combo_allowed_items_selection(self, combo_items):
        for widget in self.combo_items_container.winfo_children():
            widget.destroy()
        self.combo_dynamic_lbs.clear()

        sections = self.menu.get("sections", {})
        categories = [sec for sec in sections if sec != "combos"]

        for cat in categories:
            val = sections.get(cat)
            items_set = set()
            if isinstance(val, dict):
                for sublist in val.values():
                    items_set.update(sublist)
            elif isinstance(val, list):
                items_set.update(val)
            else:
                continue
            items = sorted(items_set)

            frame = ttk.LabelFrame(self.combo_items_container, text=f"{cat.capitalize()} Items (Allowed)")
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            lb = tk.Listbox(frame, selectmode=tk.MULTIPLE, exportselection=False)
            lb.pack(fill=tk.BOTH, expand=True)
            self.combo_dynamic_lbs[cat] = lb

            sel_items = combo_items.get(cat, [])
            for i, item in enumerate(items):
                lb.insert(tk.END, item)
                if item in sel_items:
                    lb.selection_set(i)

    def _populate_combo_fixed_quantity_edit(self, combo_items):
        for widget in self.combo_items_container.winfo_children():
            widget.destroy()
        self._fixed_combo_item_spinboxes.clear()

        sections = self.menu.get("sections", {})
        categories = [sec for sec in sections if sec != "combos"]

        for cat in categories:
            val = sections.get(cat)
            items_set = set()
            if isinstance(val, dict):
                for sublist in val.values():
                    items_set.update(sublist)
            elif isinstance(val, list):
                items_set.update(val)
            else:
                continue
            items = sorted(items_set)

            frame = ttk.LabelFrame(self.combo_items_container, text=f"{cat.capitalize()} Items (Fixed Qty)")
            frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

            for item in items:
                item_frame = ttk.Frame(frame)
                item_frame.pack(fill=tk.X, pady=1)

                lbl = ttk.Label(item_frame, text=item)
                lbl.pack(side=tk.LEFT)

                spin = SteppedSpinbox(item_frame, min_val=0, max_val=999)
                spin.pack(side=tk.RIGHT)
                spin_val = 0
                if cat in combo_items:
                    if isinstance(combo_items[cat], dict):
                        spin_val = combo_items[cat].get(item, 0)
                spin.set(spin_val)

                self._fixed_combo_item_spinboxes[item] = spin

                spin.var.trace_add("write", lambda *a: self._fixed_combo_item_spinboxes_changed())

    def _fixed_combo_item_spinboxes_changed(self):
        sel = self.lb_combos.curselection()
        if not sel:
            return
        combo_name = self.lb_combos.get(sel[0])
        combo_data = self.menu["sections"]["combos"].get(combo_name, {})
        if not combo_data:
            return

        new_combo_items = {"food": {}, "drinks": {}, "desserts": {}}

        sections = self.menu.get("sections", {})
        item_to_cat = {}
        for cat in ["food", "drinks", "desserts"]:
            val = sections.get(cat)
            if isinstance(val, dict):
                for sublist in val.values():
                    for item in sublist:
                        item_to_cat[item] = cat
            elif isinstance(val, list):
                for item in val:
                    item_to_cat[item] = cat

        for item_name, spin in self._fixed_combo_item_spinboxes.items():
            qty = spin.get()
            if qty > 0:
                cat = item_to_cat.get(item_name)
                if cat:
                    new_combo_items.setdefault(cat, {})[item_name] = qty

        combo_data["combo_items"] = new_combo_items
        self.save_menu()

    def update_combo(self):
        sel = self.lb_combos.curselection()
        if not sel:
            messagebox.showwarning("Select Combo", "Select a combo to update")
            return
        idx = sel[0]
        combo_name = self.lb_combos.get(idx)
        combos = self.menu.setdefault("sections", {}).setdefault("combos", {})
        if combo_name not in combos:
            return

        try:
            price = float(self.combo_price_var.get())
            if price < 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Invalid", "Enter valid positive combo price")
            return

        combo_data = combos[combo_name]
        prices_combos = self.menu.setdefault("prices", {}).setdefault("combos", {})
        prices_combos[combo_name] = price

        combo_data["price"] = price
        combo_data["mix_and_match"] = bool(self.combo_mam_var.get())

        if combo_data["mix_and_match"]:
            selected_items_by_cat = {}
            if hasattr(self, "combo_dynamic_lbs") and isinstance(self.combo_dynamic_lbs, dict):
                for cat, lb in self.combo_dynamic_lbs.items():
                    selected_items = [lb.get(i) for i in lb.curselection()]
                    selected_items_by_cat[cat] = selected_items
            else:
                selected_items_by_cat = {"food": [], "drinks": [], "desserts": []}
            combo_data["combo_items"] = selected_items_by_cat

            try:
                limit_food = self.combo_limit_food_var.get()
                limit_drinks = self.combo_limit_drinks_var.get()
                limit_desserts = self.combo_limit_desserts_var.get()
                if limit_food < 0 or limit_drinks < 0 or limit_desserts < 0:
                    raise ValueError()
            except Exception:
                messagebox.showerror("Invalid", "Combo section limits must be non-negative integers")
                return
            combo_data["limits"] = {
                "food": limit_food,
                "drinks": limit_drinks,
                "desserts": limit_desserts
            }
        else:
            combo_data["limits"] = {"food": 0, "drinks": 0, "desserts": 0}

        self.load_combos()
        idx = list(combos.keys()).index(combo_name)
        self.lb_combos.selection_clear(0, tk.END)
        self.lb_combos.selection_set(idx)
        self.lb_combos.event_generate("<<ListboxSelect>>")
        messagebox.showinfo("Success", "Combo updated")
        self.save_menu()

    def remove_combo(self):
        sel = self.lb_combos.curselection()
        if not sel:
            messagebox.showwarning("Select Combo", "Select a combo to remove")
            return
        idx = sel[0]
        combo_name = self.lb_combos.get(idx)
        if messagebox.askyesno("Confirm", f"Remove combo '{combo_name}'?"):
            self.menu["sections"]["combos"].pop(combo_name, None)
            self.menu.get("prices", {}).get("combos", {}).pop(combo_name, None)
            self.load_combos()
            self.save_menu()

    # ============ Discounts Tab =============

    def create_discounts_tab(self):
        frame = self.tab_discounts

        top_frame = ttk.Frame(frame, style="TFrame")
        top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left frame for discount listbox
        left_frame = ttk.Frame(top_frame, style="TFrame")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.lb_discounts = tk.Listbox(
            left_frame,
            width=28,
            height=20,
            exportselection=False,
            bg=colors.SUBPANEL_BG,
            fg=colors.FG_COLOR,
            selectbackground=colors.ACCENT_COLOR,
            selectforeground="white",
            activestyle="none",
            highlightbackground=colors.ACCENT_COLOR,
            relief=tk.FLAT,
            borderwidth=1,
        )
        self.lb_discounts.pack(fill=tk.Y, expand=True)
        self.lb_discounts.bind("<<ListboxSelect>>", self.on_discount_select)

        # Right frame for discount details and bypass items
        right_frame = ttk.Frame(top_frame, style="TFrame")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Discount Name Label and Entry
        lbl_name = ttk.Label(right_frame, text="Discount Name:", background=colors.BG_COLOR, foreground=colors.FG_COLOR, font=colors.FONT_ITEM)
        lbl_name.pack(anchor=tk.W)
        self.entry_disc_name = ttk.Entry(right_frame)
        self.entry_disc_name.pack(fill=tk.X, pady=(0, 10))

        # Discount Percent Label and Entry
        lbl_percent = ttk.Label(right_frame, text="Discount Percent (0-100):", background=colors.BG_COLOR, foreground=colors.FG_COLOR, font=colors.FONT_ITEM)
        lbl_percent.pack(anchor=tk.W)
        self.entry_disc_percent = ttk.Entry(right_frame)
        self.entry_disc_percent.pack(fill=tk.X, pady=(0, 10))

        # Bypass Items listbox label
        lbl_bypass = ttk.Label(right_frame, text="Bypass Items (multi-select):", background=colors.BG_COLOR, foreground=colors.FG_COLOR, font=colors.FONT_ITEM)
        lbl_bypass.pack(anchor=tk.W, pady=(0, 3))

        self.lb_disc_bypass = tk.Listbox(
            right_frame,
            selectmode=tk.MULTIPLE,
            height=12,
            bg=colors.SUBPANEL_BG,
            fg=colors.FG_COLOR,
            selectbackground=colors.ACCENT_COLOR,
            selectforeground="white",
            activestyle="none",
            relief=tk.FLAT,
            borderwidth=1,
        )
        self.lb_disc_bypass.pack(fill=tk.BOTH, expand=True)

        # Buttons frame
        btn_frame = ttk.Frame(right_frame, style="TFrame")
        btn_frame.pack(fill=tk.X, pady=10)

        self.btn_add_discount = ttk.Button(btn_frame, text="Add Discount", command=self.add_discount_popup)
        self.btn_add_discount.pack(side=tk.LEFT, padx=5)

        self.btn_remove_discount = ttk.Button(btn_frame, text="Remove Discount", command=self.remove_discount)
        self.btn_remove_discount.pack(side=tk.LEFT, padx=5)

        self.btn_update_discount = ttk.Button(btn_frame, text="Update Discount", command=self.update_discount)
        self.btn_update_discount.pack(side=tk.LEFT, padx=5)

    def add_discount_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add Discount")
        popup.geometry("350x160")
        popup.configure(bg=colors.BG_COLOR)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Discount Name:", fg=colors.FG_COLOR, bg=colors.BG_COLOR, font=colors.FONT_ITEM).pack(anchor=tk.W, padx=10, pady=(10, 2))
        entry_name = ttk.Entry(popup)
        entry_name.pack(fill=tk.X, padx=10)

        tk.Label(popup, text="Discount Percent (0-100):", fg=colors.FG_COLOR, bg=colors.BG_COLOR, font=colors.FONT_ITEM).pack(anchor=tk.W, padx=10, pady=(10, 2))
        entry_percent = ttk.Entry(popup)
        entry_percent.pack(fill=tk.X, padx=10)

        def confirm_add():
            name = entry_name.get().strip()
            percent_str = entry_percent.get().strip()
            if not name:
                messagebox.showwarning("Name Required", "Please enter a discount name.", parent=popup)
                return
            try:
                percent = int(percent_str)
                if not (0 <= percent <= 100):
                    raise ValueError()
            except Exception:
                messagebox.showwarning("Invalid Percent", "Percent must be an integer between 0 and 100.", parent=popup)
                return

            discounts = self.menu.setdefault("discounts", {})
            if name in discounts:
                messagebox.showwarning("Exists", "Discount with this name already exists.", parent=popup)
                return
            discounts[name] = {"percent": percent, "bypass_items": []}
            self.load_discounts()
            self.save_menu()
            popup.destroy()
            messagebox.showinfo("Discount Added", f"Discount '{name}' added.", parent=self.root)

        btn_confirm = ttk.Button(popup, text="Add Discount", command=confirm_add)
        btn_confirm.pack(pady=15)

        popup.bind("<Return>", lambda e: confirm_add())

    def load_discounts(self):
        self.lb_discounts.delete(0, tk.END)
        discounts = self.menu.get("discounts", {})
        for dname in sorted(discounts.keys()):
            self.lb_discounts.insert(tk.END, dname)
        self.load_discount_bypass_items()
        self.clear_discount_fields()

    def load_discount_bypass_items(self):
        items = set()
        for section, val in self.menu.get("sections", {}).items():
            if section == "combos":
                continue
            if isinstance(val, dict):
                for lst in val.values():
                    items.update(lst)
            elif isinstance(val, list):
                items.update(val)
        combos = self.menu.get("sections", {}).get("combos", {})
        items.update(combos.keys())
        items = sorted(items)
        self.lb_disc_bypass.delete(0, tk.END)
        for i in items:
            self.lb_disc_bypass.insert(tk.END, i)

    def clear_discount_fields(self):
        self.entry_disc_name.delete(0, tk.END)
        self.entry_disc_percent.delete(0, tk.END)
        self.lb_disc_bypass.selection_clear(0, tk.END)

    def on_discount_select(self, event=None):
        sel = self.lb_discounts.curselection()
        if not sel:
            self.clear_discount_fields()
            return
        dname = self.lb_discounts.get(sel[0])
        discount = self.menu.get("discounts", {}).get(dname, {})
        self.entry_disc_name.delete(0, tk.END)
        self.entry_disc_name.insert(0, dname)
        self.entry_disc_percent.delete(0, tk.END)
        self.entry_disc_percent.insert(0, str(discount.get("percent", 0)))

        bypass = discount.get("bypass_items", [])
        self.lb_disc_bypass.selection_clear(0, tk.END)
        for i, item in enumerate(self.lb_disc_bypass.get(0, tk.END)):
            if item in bypass:
                self.lb_disc_bypass.selection_set(i)

    def add_discount(self):
        dname = self.entry_disc_name.get().strip()
        if not dname:
            messagebox.showwarning("Name Required", "Enter discount name")
            return
        discounts = self.menu.setdefault("discounts", {})
        if dname in discounts:
            messagebox.showwarning("Exists", "Discount already exists")
            return
        discounts[dname] = { "percent": 0, "bypass_items": [] }
        self.load_discounts()
        self.save_menu()

    def remove_discount(self):
        sel = self.lb_discounts.curselection()
        if not sel:
            messagebox.showwarning("Select Discount", "Select discount to remove")
            return
        dname = self.lb_discounts.get(sel[0])
        if messagebox.askyesno("Confirm", f"Remove discount '{dname}'?"):
            self.menu.get("discounts", {}).pop(dname, None)
            self.load_discounts()
            self.clear_discount_fields()
            self.save_menu()

    def update_discount(self):
        sel = self.lb_discounts.curselection()
        if not sel:
            messagebox.showwarning("Select Discount", "Select discount to update")
            return
        old_name = self.lb_discounts.get(sel[0])
        new_name = self.entry_disc_name.get().strip()
        if not new_name:
            messagebox.showwarning("Name Required", "Discount name cannot be empty")
            return
        try:
            percent = int(self.entry_disc_percent.get())
            if not (0 <= percent <= 100):
                raise ValueError()
        except Exception:
            messagebox.showerror("Invalid", "Percent must be integer between 0 and 100")
            return
        bypass = [self.lb_disc_bypass.get(i) for i in self.lb_disc_bypass.curselection()]
        discounts = self.menu.setdefault("discounts", {})
        if new_name != old_name:
            if new_name in discounts:
                messagebox.showwarning("Exists", "Discount with that name already exists")
                return
            discounts.pop(old_name, None)
        discounts[new_name] = {"percent": percent, "bypass_items": bypass}
        self.load_discounts()
        idx = list(discounts.keys()).index(new_name)
        self.lb_discounts.selection_clear(0, tk.END)
        self.lb_discounts.selection_set(idx)
        self.lb_discounts.event_generate("<<ListboxSelect>>")
        messagebox.showinfo("Success", "Discount updated")
        self.save_menu()

    # ============ Menu Image Tab =============

    def create_image_tab(self):
        frame = self.tab_image
        # No background config on ttk.Frame

        self.img_display_lbl = ttk.Label(frame, text="No image selected", anchor="center",
                                         background=colors.BG_COLOR, foreground=colors.FG_COLOR)
        self.img_display_lbl.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Load Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load Image from URL", command=self.load_image_from_url).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Image", command=self.clear_image).pack(side=tk.LEFT, padx=5)

        self.image_tk = None

    def load_image_from_url(self):
        url = simpledialog.askstring("Load Image URL", "Enter URL for menu image:", parent=self.root)
        if not url:
            return
        self.image_path = url
        self.menu["menu_image_path"] = url
        self.save_menu()
        self._load_and_show_image(url)
        messagebox.showinfo("Image Loaded", "Menu image URL loaded and saved.")

    def load_image(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")]
        filepath = filedialog.askopenfilename(title="Select menu image", filetypes=filetypes)
        if not filepath:
            return
        self.image_path = filepath
        self.menu["menu_image_path"] = filepath
        self.save_menu()
        self._load_and_show_image(filepath)
        messagebox.showinfo("Image Loaded", "Menu image loaded and saved.")

    def _load_and_show_image(self, path_or_url):
        try:
            if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
                response = requests.get(path_or_url)
                response.raise_for_status()
                pil_img = Image.open(io.BytesIO(response.content))
            else:
                pil_img = Image.open(path_or_url)
            pil_img.thumbnail((400, 300), Image.LANCZOS)
            self.image_tk = ImageTk.PhotoImage(pil_img)
            self.img_display_lbl.config(image=self.image_tk, text="")
            self.img_display_lbl.bind("<Button-1>", self.show_full_image)
        except Exception as e:
            self.img_display_lbl.config(text=f"Failed to load image: {e}", image="")
            self.image_tk = None
            self.img_display_lbl.unbind("<Button-1>")

    def clear_image(self):
        if "menu_image_path" in self.menu:
            self.menu.pop("menu_image_path", None)
        self.image_path = None
        self.save_menu()
        self.img_display_lbl.config(text="No image selected", image="")
        self.img_display_lbl.unbind("<Button-1>")
        messagebox.showinfo("Image Cleared", "Menu image cleared.")

    def show_full_image(self, event=None):
        if not self.image_path or (not self.image_path.startswith("http") and not os.path.isfile(self.image_path)):
            messagebox.showwarning("No image", "No valid image to display.")
            return
        top = tk.Toplevel(self.root)
        top.title("Menu Image Preview")
        try:
            if self.image_path.startswith("http://") or self.image_path.startswith("https://"):
                response = requests.get(self.image_path)
                response.raise_for_status()
                pil_img = Image.open(io.BytesIO(response.content))
            else:
                pil_img = Image.open(self.image_path)
            w, h = pil_img.size
            max_w, max_h = 800, 600
            scale = min(max_w / w, max_h / h, 1)
            pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(pil_img)
            lbl = ttk.Label(top, image=img_tk)
            lbl.image = img_tk  # keep ref
            lbl.pack()
            top.geometry(f"{lbl.image.width()}x{lbl.image.height()}")
            # Remove grab_set and transient to allow interacting with other windows while open
            # top.transient(self.root)
            # top.grab_set()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load full image: {e}")
            top.destroy()
            self.img_display_lbl.config(text="No image selected", image="")

    def load_image_tab(self):
        if self.image_path and (self.image_path.startswith("http") or os.path.isfile(self.image_path)):
            self._load_and_show_image(self.image_path)
        else:
            self.img_display_lbl.config(text="No image selected", image="")

    # ============ Save and close ============

    def save_menu(self):
        if not self.save_prices():
            return
        save_menu(self.menu, self.establishment)
        if self.on_save_callback:
            self.on_save_callback()

    def on_close(self):
        self.root.destroy()