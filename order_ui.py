# order_ui.py

import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import io
import requests
from widgets import SteppedSpinbox
from menu_manager import load_menu
from style_helper import apply_default_style
import colors


class OrderUIWindow:
    def __init__(self, root, establishment):
        self.root = root
        self.establishment = establishment
        self.menu = load_menu(establishment)

        self.lower_to_original_item = {}
        self.lower_to_original_section = {}
        self.lower_to_original_subsection = {}

        self.current_item_spinboxes = {}
        self.global_order_qty = {}

        self.combo_qty_vars = {}
        self.combo_selected_items_per_meal = {}

        self.discount_vars = {}

        self._updating_summary = False

        self.custom_discount_var = tk.BooleanVar()
        self.custom_discount_percent_var = tk.StringVar(value="0")

        apply_default_style(self.root)
        self.root.configure(bg=colors.BG_COLOR)
        self._build_ui()
        self._load_discounts()
        self._populate_section_tree()
        self._load_order_image()
        self.update_order_summary()

    def _build_ui(self):
        self.root.title(f"Order Tab - {self.establishment}")
        self.root.geometry("1100x780")
        self.root.minsize(1100, 780)

        self.top_discount_frame = ttk.LabelFrame(self.root, text="Available Discounts", style="TLabelframe")
        self.top_discount_frame.pack(fill=tk.X, padx=10, pady=5)

        # Add Custom Discount controls in the discount frame
        custom_frame = ttk.Frame(self.top_discount_frame)
        custom_frame.pack(side=tk.RIGHT, padx=10, pady=5)  # Pack to right side of discounts frame

        self.custom_discount_chk = ttk.Checkbutton(
            custom_frame,
            text="Custom Discount",
            variable=self.custom_discount_var,
            style="Discount.TCheckbutton",
            command=self.update_order_summary,
        )
        self.custom_discount_chk.grid(row=0, column=0, sticky="w")

        self.custom_discount_entry = ttk.Entry(
            custom_frame,
            textvariable=self.custom_discount_percent_var,
            width=5,
            font=colors.FONT_SPINBOX,
            state="disabled"
        )
        self.custom_discount_entry.grid(row=0, column=1, padx=(5, 0))

        custom_label = ttk.Label(custom_frame, text="%", font=colors.FONT_ITEM)
        custom_label.grid(row=0, column=2, sticky="w", padx=(2, 0))
        self.custom_discount_entry.bind("<FocusOut>", lambda e: self.update_order_summary())
        self.custom_discount_entry.bind("<Return>", lambda e: self.update_order_summary())

        # Trace changes to toggle entry enable state and update summary
        def on_custom_discount_toggle(*args):
            if self.custom_discount_var.get():
                self.custom_discount_entry.configure(state="normal")
            else:
                self.custom_discount_entry.configure(state="disabled")
                self.custom_discount_percent_var.set("0")
            self.update_order_summary()

        def on_custom_discount_change(*args):
            self.update_order_summary()

        self.custom_discount_var.trace_add("write", on_custom_discount_toggle)
        self.custom_discount_percent_var.trace_add("write", on_custom_discount_change)

        self.paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=0)

        self.left_panel = ttk.Frame(self.paned, style="TLabelframe", width=200)
        self.left_panel.pack_propagate(False)
        self.paned.add(self.left_panel, weight=2)

        ttk.Label(self.left_panel, text="Sections & Subsections", font=colors.FONT_HEADER, foreground=colors.ACCENT_COLOR, background=colors.BG_COLOR).pack(anchor=tk.W, padx=4, pady=(4, 2))

        self.section_tree = ttk.Treeview(self.left_panel, show="tree", selectmode="browse", style="Treeview", height=32, takefocus=True)
        self.section_tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 5))
        self.section_tree.bind("<<TreeviewSelect>>", self.on_section_subsection_selected)

        self._add_tree_scrollbars(self.left_panel, self.section_tree)

        self.middle_panel = ttk.Frame(self.paned, style="TLabelframe")
        self.paned.add(self.middle_panel, weight=5)

        self.section_label_var = tk.StringVar(value="")
        self.section_label = ttk.Label(
            self.middle_panel,
            textvariable=self.section_label_var,
            font=colors.FONT_HEADER,
            background=colors.BG_COLOR,
            foreground=colors.ACCENT_COLOR,
            anchor="w",
        )
        self.section_label.pack(fill=tk.X, padx=10, pady=(10, 2))

        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.middle_panel, textvariable=self.search_var, font=colors.FONT_SPINBOX)
        self.search_entry.pack(fill=tk.X, padx=10, pady=(0, 8))
        self.search_entry.insert(0, "Search...")

        self.search_entry.bind("<FocusIn>", self._search_focus_in)
        self.search_entry.bind("<FocusOut>", self._search_focus_out)
        self.search_var.trace_add("write", self.on_search_change)

        self.item_canvas = tk.Canvas(self.middle_panel, background=colors.PANEL_BG, highlightthickness=0)
        self.item_scrollbar = ttk.Scrollbar(self.middle_panel, orient=tk.VERTICAL, command=self.item_canvas.yview, style="Vertical.TScrollbar")
        self.item_container = ttk.Frame(self.item_canvas, style="TLabelframe")

        self.item_container.bind("<Configure>", lambda e: self.item_canvas.configure(scrollregion=self.item_canvas.bbox("all")))

        self.item_canvas.create_window((0, 0), window=self.item_container, anchor="nw")
        self.item_canvas.configure(yscrollcommand=self.item_scrollbar.set)
        self.item_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=(0, 10))
        self.item_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=(0, 10))

        self._bind_mousewheel(self.item_canvas)

        self.current_item_spinboxes.clear()

        self.right_panel = ttk.Frame(self.paned, style="TLabelframe", width=300)
        self.right_panel.pack_propagate(False)
        self.paned.add(self.right_panel, weight=3)

        lbl_order_summary = ttk.Label(
            self.right_panel,
            text="Order Summary",
            font=colors.FONT_HEADER,
            foreground=colors.ACCENT_COLOR,
            background=colors.BG_COLOR,
            anchor="nw",
        )
        lbl_order_summary.pack(anchor=tk.W, padx=10, pady=(10, 5))

        self.summary_text_wrapper = ttk.Frame(self.right_panel)
        self.summary_text_wrapper.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.summary_text = tk.Text(
            self.summary_text_wrapper,
            height=18,
            state=tk.DISABLED,
            bg=colors.PANEL_BG,
            fg=colors.FG_COLOR,
            relief=tk.FLAT,
            font=colors.FONT_DEFAULT,
            borderwidth=0,
            highlightthickness=0,
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True)

        self.total_label = ttk.Label(
            self.right_panel,
            text="Total: $0.00",
            font=("Segoe UI", 14, "bold"),
            foreground=colors.ACCENT_COLOR,
            background=colors.BG_COLOR,
            anchor="e",
        )
        self.total_label.pack(fill=tk.X, padx=10)

        self.menu_image_frame = ttk.LabelFrame(self.right_panel, text="Menu Image", style="TLabelframe")
        self.menu_image_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)
        self.menu_image_frame.config(height=180)
        self.menu_image_frame.pack_propagate(False)

        self.menu_image_label = ttk.Label(self.menu_image_frame, background=colors.PANEL_BG)
        self.menu_image_label.pack(expand=True, fill=tk.BOTH)
        self.menu_image_label.bind("<Button-1>", self._on_menu_image_click)
        self.menu_image_tk = None

        self.btn_frame = ttk.Frame(self.right_panel, style="TLabelframe")
        self.btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.clear_button = ttk.Button(self.btn_frame, text="Clear Inputs", style="Accent.TButton", command=self.clear_all)
        self.clear_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.confirm_button = ttk.Button(self.btn_frame, text="Confirm Purchase", style="Accent.TButton", command=self.confirm_purchase)
        self.confirm_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def _add_tree_scrollbars(self, parent, treeview):
        vsb = ttk.Scrollbar(parent, orient="vertical", command=treeview.yview, style="Vertical.TScrollbar")
        treeview.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _bind_mousewheel(self, widget):
        widget.bind_all("<MouseWheel>", lambda e: self._on_mousewheel(e, widget))
        widget.bind_all("<Button-4>", lambda e: self._on_mousewheel(e, widget))
        widget.bind_all("<Button-5>", lambda e: self._on_mousewheel(e, widget))

    def _on_mousewheel(self, event, widget):
        if event.num == 4:
            widget.yview_scroll(-1, "units")
        elif event.num == 5:
            widget.yview_scroll(1, "units")
        else:
            widget.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _search_focus_in(self, event):
        if self.search_entry.get() == "Search...":
            self.search_entry.delete(0, tk.END)

    def _search_focus_out(self, event):
        if self.search_entry.get().strip() == "":
            self.search_entry.insert(0, "Search...")

    def on_search_change(self, *args):
        sel = self.section_tree.selection()
        if not sel:
            return
        sel_id = sel[0]
        if "::" in sel_id:
            section, subsection = sel_id.split("::", 1)
        else:
            section, subsection = sel_id, None
        self._populate_items(section, subsection)

    def _filter_items(self, items):
        filter_str = self.search_var.get().lower().strip()
        if filter_str == "" or filter_str == "search...":
            return items
        return [i for i in items if filter_str in i.lower()]

    def _populate_section_tree(self):
        self.section_tree.delete(*self.section_tree.get_children())
        sections = self.menu.get("sections", {})

        self.lower_to_original_section.clear()
        self.lower_to_original_subsection.clear()

        for section_key in sorted(sections.keys()):
            section_key_lower = section_key.lower()
            self.lower_to_original_section[section_key_lower] = section_key
            if section_key_lower == "combos":
                self.section_tree.insert("", "end", iid=section_key, text=section_key.capitalize(), open=True)
            else:
                parent_id = self.section_tree.insert(
                    "", "end", iid=section_key, text=section_key.capitalize(), open=True
                )
                val = sections.get(section_key)
                if isinstance(val, dict):
                    for subsec_key in sorted(val.keys()):
                        subsec_key_lower = subsec_key.lower()
                        self.lower_to_original_subsection[(section_key_lower, subsec_key_lower)] = subsec_key
                        self.section_tree.insert(
                            parent_id, "end", iid=f"{section_key}::{subsec_key}", text=subsec_key.capitalize()
                        )

        children = self.section_tree.get_children()
        if children:
            self.section_tree.selection_set(children[0])
            self.section_tree.focus(children[0])
            self.on_section_subsection_selected()

    def on_section_subsection_selected(self, event=None):
        sel = self.section_tree.selection()
        if not sel:
            return
        sel_id = sel[0]
        if sel_id.lower() == "combos":
            self._populate_combos_ui()
            self.section_label_var.set("Combos")
            return

        if "::" in sel_id:
            section, subsection = sel_id.split("::", 1)
            section_lower = section.lower()
            subsection_lower = subsection.lower()
            section_real = self.lower_to_original_section.get(section_lower, section)
            subsection_real = self.lower_to_original_subsection.get((section_lower, subsection_lower), subsection)
            self._populate_items(section_real, subsection_real)
        else:
            section_lower = sel_id.lower()
            section_real = self.lower_to_original_section.get(section_lower, sel_id)
            self._populate_items(section_real, None)

    def _populate_items(self, section, subsection):
        self._save_current_items_to_global_order()

        for w in self.item_container.winfo_children():
            w.destroy()
        self.current_item_spinboxes.clear()
        self.lower_to_original_item.clear()

        self.section_label_var.set(f"{section.capitalize()}" + (f" - {subsection.capitalize()}" if subsection else ""))

        sections = self.menu.get("sections", {})
        section_data = sections.get(section)

        items = []
        if section_data is None:
            items = []
        elif isinstance(section_data, dict):
            if subsection:
                items = section_data.get(subsection, [])
            else:
                items = []
                for sublst in section_data.values():
                    items.extend(sublst)
        elif isinstance(section_data, list):
            items = section_data
        else:
            items = []

        items = sorted(set(items))
        items = self._filter_items(items)

        if not items and section.lower() != "combos":
            lbl = ttk.Label(
                self.item_container,
                text="No items to display.",
                font=colors.FONT_ITEM,
                foreground=colors.FG_COLOR,
                background=colors.PANEL_BG,
            )
            lbl.pack(pady=20)
            return

        prices_data = self.menu.get("prices", {})
        combos_prices = prices_data.get("combos", {})

        default_prices_raw = {
            "food": prices_data.get("food", 10),
            "drinks": prices_data.get("drinks", 7),
            "desserts": prices_data.get("desserts", 5),
            "animal_treat": prices_data.get("animal_treat", 3),
        }
        default_prices = {k.lower(): v for k, v in default_prices_raw.items()}

        for idx, item_name in enumerate(items):
            item_name_lower = item_name.lower()
            self.lower_to_original_item[item_name_lower] = item_name

            bg_color = colors.ITEM_BG_1 if idx % 2 == 0 else colors.ITEM_BG_2
            frame = tk.Frame(self.item_container, bg=bg_color, padx=5, pady=3)
            frame.pack(fill=tk.X, pady=1)

            lbl_name = tk.Label(frame, text=item_name, font=colors.FONT_ITEM, fg=colors.FG_COLOR, bg=bg_color)
            lbl_name.pack(side=tk.LEFT, padx=3)

            price = None
            if item_name in prices_data:
                price = prices_data[item_name]
            else:
                for k in prices_data.keys():
                    if k.lower() == item_name_lower:
                        price = prices_data[k]
                        break
                if price is None:
                    if section.lower() == "combos" and item_name in combos_prices:
                        price = combos_prices[item_name]
                    else:
                        found_cat = None
                        for cat in default_prices.keys():
                            sec_items = sections.get(cat)
                            if sec_items:
                                if isinstance(sec_items, dict):
                                    for sublst in sec_items.values():
                                        for it in sublst:
                                            if it.lower() == item_name_lower:
                                                found_cat = cat
                                                break
                                elif isinstance(sec_items, list):
                                    for it in sec_items:
                                        if it.lower() == item_name_lower:
                                            found_cat = cat
                                            break
                            if found_cat:
                                break
                        price = default_prices.get(found_cat, 0)
            price = float(price if price is not None else 0)

            lbl_price = tk.Label(
                frame,
                text=f"${price:.2f}",
                font=colors.FONT_PRICE,
                fg="#c1a1ff",
                bg=bg_color,
                width=8,
                anchor="w",
            )
            lbl_price.pack(side=tk.LEFT, padx=(10, 5))

            spin = SteppedSpinbox(frame, min_val=0, max_val=999, bg=colors.SPINBOX_BG)
            spin.entry.configure(font=colors.FONT_SPINBOX, fg="white", bg=colors.SPINBOX_BG, insertbackground="white")
            spin.pack(side=tk.RIGHT, padx=5)

            prev_qty = self.global_order_qty.get(item_name_lower, 0)
            spin.set(prev_qty)

            def on_spin_change(*args, item_lower=item_name_lower, spin_ref=spin):
                try:
                    val = spin_ref.get()
                except Exception:
                    val = 0
                if val == 0:
                    self.global_order_qty.pop(item_lower, None)
                else:
                    self.global_order_qty[item_lower] = val
                if not self._updating_summary:
                    self._updating_summary = True
                    try:
                        self.update_order_summary()
                    finally:
                        self._updating_summary = False

            spin.var.trace_add("write", on_spin_change)

            self.current_item_spinboxes[item_name_lower] = spin

    def _save_current_items_to_global_order(self):
        for item_lower, spinbox in list(self.current_item_spinboxes.items()):
            try:
                qty = spinbox.get()
                if qty > 0:
                    self.global_order_qty[item_lower] = qty
                else:
                    self.global_order_qty.pop(item_lower, None)
            except Exception:
                pass

    def _populate_combos_ui(self):
        self._save_current_items_to_global_order()

        for w in self.item_container.winfo_children():
            w.destroy()
        self.current_item_spinboxes.clear()
        self.combo_qty_vars.clear()
        self.combo_selected_items_per_meal.clear()

        combos = self.menu.get("sections", {}).get("combos", {})
        if not combos:
            lbl = ttk.Label(self.item_container, text="No combos available.", foreground=colors.FG_COLOR, background=colors.PANEL_BG)
            lbl.pack(pady=20)
            return

        for combo_name, combo_data in sorted(combos.items()):
            frame = ttk.Frame(self.item_container, relief=tk.RIDGE, borderwidth=1)
            frame.pack(fill=tk.X, padx=5, pady=4)

            price = float(combo_data.get("price", 0))
            lbl = ttk.Label(frame, text=f"{combo_name}  (${price:.2f})", font=colors.FONT_ITEM, foreground=colors.ACCENT_COLOR)
            lbl.pack(side=tk.LEFT, padx=10, pady=6)

            lower_combo_name = combo_name.lower()
            if combo_data.get("mix_and_match", False):
                btn_select = ttk.Button(frame, text="Select Items", style="Accent.TButton", command=lambda cn=combo_name: self.open_combo_selector(cn))
                btn_select.pack(side=tk.RIGHT, padx=10, pady=6)

                btn_clear = ttk.Button(frame, text="Clear Meal(s)", style="Accent.TButton", command=lambda cn=combo_name: self.clear_combo_meals(cn))
                btn_clear.pack(side=tk.RIGHT, padx=5, pady=6)

                self.combo_qty_vars[combo_name] = None
                self.combo_selected_items_per_meal.setdefault(combo_name, [])
            else:
                spin = SteppedSpinbox(frame, min_val=0, max_val=999, bg=colors.SPINBOX_BG)
                spin.entry.configure(font=colors.FONT_SPINBOX, fg="white", bg=colors.SPINBOX_BG, insertbackground="white")
                spin.pack(side=tk.RIGHT, padx=10, pady=6)

                prev_qty = self.global_order_qty.get(lower_combo_name, 0)
                spin.set(prev_qty)

                def on_spin_change(*args, combo=combo_name, spin_ref=spin):
                    try:
                        val = spin_ref.get()
                    except Exception:
                        val = 0
                    if val == 0:
                        self.global_order_qty.pop(combo.lower(), None)
                    else:
                        self.global_order_qty[combo.lower()] = val
                    if not self._updating_summary:
                        self._updating_summary = True
                        try:
                            self.update_order_summary()
                        finally:
                            self._updating_summary = False

                spin.var.trace_add("write", on_spin_change)
                self.combo_qty_vars[combo_name] = spin

    def open_combo_selector(self, combo_name):
        combo_data = self.menu["sections"]["combos"].get(combo_name)
        if not combo_data or not combo_data.get("mix_and_match", False):
            messagebox.showinfo("Info", f"Combo '{combo_name}' is fixed; no item selection.")
            return

        top = tk.Toplevel(self.root)
        top.title(f"Select Items for Combo: {combo_name}")
        top.geometry("975x650")
        top.transient(self.root)
        top.grab_set()

        limits = combo_data.get("limits", {})
        allowed_items = combo_data.get("combo_items", {})

        selected_meals = self.combo_selected_items_per_meal.setdefault(combo_name, [])
        cur_qty = max(len(selected_meals), 1)

        self._combo_selector_last_qty = cur_qty

        main_container = ttk.Frame(top)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        lbl_qty = ttk.Label(main_container, text="Number of combo meals:", font=colors.FONT_ITEM)
        lbl_qty.grid(row=0, column=0, sticky=tk.W, pady=(5, 10))

        quantity_var = tk.IntVar(value=cur_qty)
        spin_qty = ttk.Spinbox(main_container, from_=0, to=999, textvariable=quantity_var, width=5)
        spin_qty.grid(row=0, column=1, sticky=tk.W, pady=(5, 10))

        container = ttk.Frame(main_container)
        container.grid(row=1, column=0, columnspan=2, sticky="nsew")
        main_container.rowconfigure(1, weight=1)
        main_container.columnconfigure(1, weight=1)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        categories = list(allowed_items.keys())

        def rebuild_meal_selectors():
            for child in scroll_frame.winfo_children():
                child.destroy()

            q = quantity_var.get()
            if q < 0:
                quantity_var.set(0)
                return

            while len(selected_meals) < q:
                selected_meals.append({cat: {} for cat in categories})
            while len(selected_meals) > q:
                selected_meals.pop()

            max_cols = 2
            for i in range(q):
                meal_frame = ttk.LabelFrame(scroll_frame, text=f"Meal #{i + 1}", padding=5)
                row = i // max_cols
                col = i % max_cols
                meal_frame.grid(row=row, column=col, sticky="nwes", padx=5, pady=5)
                scroll_frame.columnconfigure(col, weight=1)

                for cat in categories:
                    cat_items = allowed_items.get(cat, [])
                    if not cat_items:
                        continue
                    cat_frame = ttk.LabelFrame(meal_frame, text=f"{cat.capitalize()} (Limit: {limits.get(cat, 0)})")
                    cat_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5, pady=5)

                    for item in cat_items:
                        item_frame = ttk.Frame(cat_frame)
                        item_frame.pack(fill=tk.X, pady=1)

                        lbl = ttk.Label(item_frame, text=item)
                        lbl.pack(side=tk.LEFT, anchor=tk.W)

                        prev_qty = selected_meals[i].get(cat, {}).get(item, 0)
                        spin = SteppedSpinbox(item_frame, min_val=0, max_val=limits.get(cat, 0))
                        spin.set(prev_qty)
                        spin.pack(side=tk.RIGHT)

                        def on_spin_change(meal_idx=i, category=cat, item_name=item, spin_obj=spin):
                            val = spin_obj.get()
                            sel = selected_meals[meal_idx][category]
                            if val == 0:
                                sel.pop(item_name, None)
                            else:
                                sel[item_name] = val

                            total_q = sum(sel.values())
                            max_limit = limits.get(category, 0)
                            if max_limit > 0 and total_q > max_limit:
                                excess = total_q - max_limit
                                new_val = val - excess
                                if new_val < 0:
                                    new_val = 0
                                spin_obj.set(new_val)
                                if new_val == 0:
                                    sel.pop(item_name, None)
                                messagebox.showwarning(
                                    "Limit Exceeded",
                                    f"Total {category} quantity exceeded max limit ({max_limit}) for Meal #{meal_idx + 1}.",
                                )
                            if not self._updating_summary:
                                self._updating_summary = True
                                try:
                                    self.update_order_summary()
                                finally:
                                    self._updating_summary = False

                        spin.entry.unbind("<FocusOut>")
                        spin.entry.unbind("<Return>")
                        spin.entry.unbind("<KP_Enter>")
                        spin.entry.bind("<FocusOut>", lambda e, cb=on_spin_change: cb())
                        spin.entry.bind("<Return>", lambda e, cb=on_spin_change: cb())
                        spin.entry.bind("<KP_Enter>", lambda e, cb=on_spin_change: cb())
                        spin.var.trace_add("write", lambda *a, cb=on_spin_change: cb())

            if not self._updating_summary:
                self._updating_summary = True
                try:
                    self.update_order_summary()
                finally:
                    self._updating_summary = False

        def on_qty_change(*_):
            try:
                q = int(quantity_var.get())
            except Exception:
                quantity_var.set(self._combo_selector_last_qty)
                return

            if q < 0:
                quantity_var.set(0)
                return
            self._combo_selector_last_qty = q

            rebuild_meal_selectors()

        quantity_var.trace_add("write", lambda *a: on_qty_change())

        rebuild_meal_selectors()

        def save_and_close():
            if combo_name in self.combo_qty_vars and self.combo_qty_vars[combo_name]:
                self.combo_qty_vars[combo_name].set(quantity_var.get())
            self.combo_qty_vars[combo_name] = None
            if not self._updating_summary:
                self._updating_summary = True
                try:
                    self.update_order_summary()
                finally:
                    self._updating_summary = False
            top.destroy()

        btn_save = ttk.Button(top, text="Save Selection and Quantity", command=save_and_close)
        btn_save.pack(pady=10)

    def clear_combo_meals(self, combo_name):
        if combo_name in self.combo_selected_items_per_meal:
            self.combo_selected_items_per_meal[combo_name].clear()
        if combo_name in self.combo_qty_vars and self.combo_qty_vars[combo_name]:
            self.combo_qty_vars[combo_name].set(0)
        if combo_name.lower() in self.global_order_qty:
            self.global_order_qty.pop(combo_name.lower())
        if not self._updating_summary:
            self._updating_summary = True
            try:
                self.update_order_summary()
            finally:
                self._updating_summary = False

    def _load_discounts(self):
        for w in self.top_discount_frame.winfo_children():
            w.destroy()
        self.discount_vars.clear()

        discounts = self.menu.get("discounts", {})
        for dname in sorted(discounts.keys()):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(
                self.top_discount_frame,
                text=dname,
                variable=var,
                style="Discount.TCheckbutton",
                command=self.update_order_summary,
            )
            chk.pack(side=tk.LEFT, padx=10, pady=5)
            self.discount_vars[dname] = var

    def _load_order_image(self):
        menu_img_path = self.menu.get("menu_image_path", None)
        self.menu_image_tk = None
        self.menu_image_label.config(image="", text="No menu image selected")
        self.menu_image_label.unbind("<Button-1>")

        if menu_img_path:
            try:
                if menu_img_path.startswith("http://") or menu_img_path.startswith("https://"):
                    response = requests.get(menu_img_path)
                    response.raise_for_status()
                    pil_img = Image.open(io.BytesIO(response.content))
                elif os.path.isfile(menu_img_path):
                    pil_img = Image.open(menu_img_path)
                else:
                    pil_img = None

                if pil_img:
                    pil_img.thumbnail((280, 180), Image.LANCZOS)
                    self.menu_image_tk = ImageTk.PhotoImage(pil_img)
                    self.menu_image_label.config(image=self.menu_image_tk, text="")
                    self.menu_image_label.bind("<Button-1>", self._on_menu_image_click)
            except Exception:
                self.menu_image_label.config(text="Failed to load image", image="")

    def _on_menu_image_click(self, event=None):
        img_path = self.menu.get("menu_image_path", None)
        if not img_path:
            messagebox.showwarning("No image", "No menu image to display.")
            return
        top = tk.Toplevel(self.root)
        top.title("Menu Image Preview")
        try:
            if img_path.startswith("http://") or img_path.startswith("https://"):
                resp = requests.get(img_path)
                resp.raise_for_status()
                pil_img = Image.open(io.BytesIO(resp.content))
            else:
                pil_img = Image.open(img_path)
            w, h = pil_img.size
            max_w, max_h = 800, 600
            scale = min(max_w / w, max_h / h, 1)
            pil_img = pil_img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(pil_img)
            lbl = ttk.Label(top, image=img_tk)
            lbl.image = img_tk
            lbl.pack()
            top.geometry(f"{lbl.image.width()}x{lbl.image.height()}")
            top.transient(self.root)
            top.grab_set()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load full image: {e}")
            top.destroy()

    def get_current_order(self):
        order = {"combos": {}, "_discounts_applied": []}
        sections = self.menu.get("sections", {})

        item_to_cat = {}
        name_case_map = {}

        combos = sections.get("combos", {})

        for cat, val in sections.items():
            cat_lower = cat.lower()
            if cat_lower == "combos":
                continue
            if isinstance(val, dict):
                for sublist in val.values():
                    for item in sublist:
                        litem = item.lower()
                        if item not in combos:
                            item_to_cat[litem] = cat_lower
                            name_case_map[litem] = item
            elif isinstance(val, list):
                for item in val:
                    if item not in combos:
                        litem = item.lower()
                        item_to_cat[litem] = cat_lower
                        name_case_map[litem] = item

        for cat_lower in set(item_to_cat.values()):
            order[cat_lower] = {}

        for item_lower, qty in self.global_order_qty.items():
            if qty <= 0:
                continue
            if item_lower in (name.lower() for name in combos.keys()):
                continue
            cat_lower = item_to_cat.get(item_lower, "food")
            order.setdefault(cat_lower, {})
            canonical_name = name_case_map.get(item_lower, item_lower)
            order[cat_lower][canonical_name] = qty

        for combo_name, combo_data in combos.items():
            if combo_data.get("mix_and_match", False):
                meals = self.combo_selected_items_per_meal.get(combo_name, [])
                qty = len(meals)
                if qty > 0:
                    order["combos"][combo_name] = {"qty": qty}
            else:
                spin = self.combo_qty_vars.get(combo_name)
                if spin:
                    qty = spin.get()
                    if qty > 0:
                        order["combos"][combo_name] = {"qty": qty}

        applied = [name for name, var in self.discount_vars.items() if var.get()]
        order["_discounts_applied"] = applied
        return order

    def check_limits(self, order):
        limits = self.menu.get("item_limits", {})

        def exceeds_limit(item, qty):
            lim = limits.get(item, 0)
            return lim > 0 and qty > lim

        for cat, items in order.items():
            if cat in ("_discounts_applied", "combos"):
                continue
            for item, qty in items.items():
                if exceeds_limit(item, qty):
                    messagebox.showwarning("Limit Exceeded", f"Limit exceeded for {item}: max {limits[item]}")
                    return False

        for combo_name, combo_data in order.get("combos", {}).items():
            combo_info = self.menu.get("sections", {}).get("combos", {}).get(combo_name, {})
            if not combo_info.get("mix_and_match", False):
                continue
            meals = self.combo_selected_items_per_meal.get(combo_name, [])
            limits_per_cat = {k.lower(): v for k, v in combo_info.get("limits", {}).items()}
            for i, meal in enumerate(meals):
                for cat in ("food", "drinks", "desserts"):
                    cat_lower = cat.lower()
                    total_qty_cat = sum(meal.get(cat, {}).values())
                    max_lim = limits_per_cat.get(cat_lower, 0)
                    if max_lim > 0 and total_qty_cat > max_lim:
                        messagebox.showwarning(
                            "Limit Exceeded",
                            f"Combo '{combo_name}' meal #{i + 1} exceeds {cat} max limit ({max_lim})."
                        )
                        return False
                for cat, items_dict in meal.items():
                    for item, qty in items_dict.items():
                        if exceeds_limit(item, qty):
                            messagebox.showwarning(
                                "Limit Exceeded",
                                f"Limit exceeded for combo item '{item}': max {limits[item]}",
                            )
                            return False
        return True

    def calculate_order_cost(self, order):
        prices = self.menu.get("prices", {})
        total = 0.0

        default_cat_prices_raw = {
            "food": prices.get("food", 10),
            "drinks": prices.get("drinks", 7),
            "desserts": prices.get("desserts", 5),
            "animal_treat": prices.get("animal_treat", 3),
        }
        default_cat_prices = {k.lower(): v for k, v in default_cat_prices_raw.items()}

        for cat, items in order.items():
            if cat in ("_discounts_applied", "combos"):
                continue
            cat_lower = cat.lower()
            dp = default_cat_prices.get(cat_lower, 0)
            for item_name, qty in items.items():
                item_price = prices.get(item_name)
                if item_price is None:
                    for k in prices.keys():
                        if k.lower() == item_name.lower():
                            item_price = prices[k]
                            break
                if item_price is None:
                    item_price = dp
                total += item_price * qty

        combos_prices = prices.get("combos", {})
        for combo_name, combo_info in order.get("combos", {}).items():
            qty = combo_info.get("qty", 0)
            cprice = combos_prices.get(combo_name)
            if cprice is None:
                for k in combos_prices.keys():
                    if k.lower() == combo_name.lower():
                        cprice = combos_prices[k]
                        break
            cprice = cprice if cprice is not None else 0
            total += cprice * qty

        discounts = self.menu.get("discounts", {})
        applied = order.get("_discounts_applied", [])
        for dname in applied:
            disc = discounts.get(dname)
            if not disc:
                continue
            percent = disc.get("percent", 0) / 100.0
            bypass_items = set(disc.get("bypass_items", []))

            total_disc_items_cost = 0.0
            bypass_cost = 0.0

            for cat, items in order.items():
                if cat in ("_discounts_applied", "combos"):
                    continue
                cat_lower = cat.lower()
                dp_cat = default_cat_prices.get(cat_lower, 0)
                for it, qty in items.items():
                    iprice = prices.get(it)
                    if iprice is None:
                        for k in prices.keys():
                            if k.lower() == it.lower():
                                iprice = prices[k]
                                break
                    if iprice is None:
                        iprice = dp_cat
                    cost = iprice * qty
                    total_disc_items_cost += cost
                    if it in bypass_items:
                        bypass_cost += cost

            for combo_name, combo_info in order.get("combos", {}).items():
                q = combo_info.get("qty", 0)
                combo_cost = combos_prices.get(combo_name)
                if combo_cost is None:
                    for k in combos_prices.keys():
                        if k.lower() == combo_name.lower():
                            combo_cost = combos_prices[k]
                            break
                combo_cost = combo_cost if combo_cost is not None else 0
                total_disc_items_cost += combo_cost * q

            total = total - (total_disc_items_cost - bypass_cost) * percent

        try:
            if self.custom_discount_var.get():
                pct_str = self.custom_discount_percent_var.get()
                custom_pct = float(pct_str)
                custom_pct = max(0, min(100, custom_pct))  # Clamp between 0 and 100
                total = total * (1 - (custom_pct / 100))
        except Exception:
            # Ignore errors in custom discount input
            pass

        return total

    def update_order_summary(self):
        try:
            order = self.get_current_order()
        except Exception:
            return

        normal_lines = []
        combo_lines = []

        for cat, items in order.items():
            if cat in ("_discounts_applied", "combos"):
                continue
            if items:
                normal_lines.append(f"{cat.capitalize()}:")
                for it_name, qty in items.items():
                    normal_lines.append(f"  - {it_name}: x{qty}")

        if order.get("combos"):
            combo_lines.append("---------------------------------")
            combo_lines.append("Combos:")
            for combo_name, combo_info in order["combos"].items():
                qty = combo_info.get("qty", 0)
                combo_lines.append(f"  - {combo_name}: x{qty}")
                combo_meta = self.menu.get("sections", {}).get("combos", {}).get(combo_name, {})
                if combo_meta.get("mix_and_match", False):
                    selected_meals = self.combo_selected_items_per_meal.get(combo_name, [])
                    for i, meal in enumerate(selected_meals):
                        combo_lines.append(f"\n     Meal #{i+1}:")
                        for cat_view in ("drinks", "food", "desserts"):
                            items_in_cat = meal.get(cat_view, {})
                            if items_in_cat:
                                for item_ordered, qnt in items_in_cat.items():
                                    combo_lines.append(
                                        f"              {cat_view.capitalize()}: - {item_ordered} x {qnt}"
                                    )
                    combo_lines.append("")
                else:
                    combo_items = combo_meta.get("combo_items", {"food": {}, "drinks": {}, "desserts": {}})
                    combo_qty = qty  # quantity of this combo ordered
                    combo_lines.append(f"\n     Meal #1:")
                    for cat_view in ("drinks", "food", "desserts"):
                        items_dict = combo_items.get(cat_view, {})
                        for item_ordered, qnt in items_dict.items():
                            total_qty = qnt * combo_qty  # multiply per ordered quantity
                            combo_lines.append(
                                f"              {cat_view.capitalize()}: - {item_ordered} x {total_qty}"
                            )
                    combo_lines.append("")
            combo_lines.append("---------------------------------")

        lines = []
        if combo_lines and normal_lines:
            lines.extend(combo_lines)
            lines.append("---------------------------------")
            lines.extend(normal_lines)
            lines.append("---------------------------------")
        elif combo_lines:
            lines.extend(combo_lines)
        elif normal_lines:
            lines.extend(normal_lines)

        applied = order.get("_discounts_applied", [])
        if applied:
            lines.append("\nDiscounts Applied:")
            for disc_name in applied:
                lines.append(f"  - {disc_name}")

        total = self.calculate_order_cost(order)

        try:
            self.summary_text.config(state=tk.NORMAL)
            self.summary_text.delete("1.0", tk.END)
            if lines:
                self.summary_text.insert(tk.END, "\n".join(lines))
            else:
                self.summary_text.insert(tk.END, "No items selected.")
            self.summary_text.insert(tk.END, f"\n\nTotal: ${total:,.2f}")
            self.summary_text.config(state=tk.DISABLED)
            self.total_label.config(text=f"Total: ${total:,.2f}")
        except tk.TclError:
            pass

    def clear_all(self):
        self.global_order_qty.clear()
        for spin in self.current_item_spinboxes.values():
            spin.set(0)
        for combo_name in self.combo_selected_items_per_meal:
            self.combo_selected_items_per_meal[combo_name].clear()
        for var in self.discount_vars.values():
            var.set(False)
        for spin in self.combo_qty_vars.values():
            if spin:
                spin.set(0)
        self.update_order_summary()

    def confirm_purchase(self):
        order = self.get_current_order()
        total = self.calculate_order_cost(order)

        if not self.check_limits(order):
            return

        summary_lines = []
        for cat, items in order.items():
            if cat in ("_discounts_applied", "combos"):
                continue
            for it, qty in items.items():
                summary_lines.append(f"{it}: x{qty}")

        for combo_name, cinfo in order.get("combos", {}).items():
            qty = cinfo.get("qty", 0)
            summary_lines.append(f"Combo: {combo_name} x{qty}")

        applied = order.get("_discounts_applied", [])
        if applied:
            summary_lines.append("\nDiscounts applied:")
            for d in applied:
                summary_lines.append(f"  - {d}")

        msg = f"Confirm this purchase?\n\nOrder details:\n" + "\n".join(summary_lines) + f"\n\nTotal: ${total:,.2f}"

        if messagebox.askokcancel("Confirm Purchase", msg):
            messagebox.showinfo("Purchase Confirmed", "Order confirmed! Ready for next customer.")
            self.clear_all()