import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from menu_manager import load_menu_files, save_menu_file, delete_menu_file, MENU_DIR
from order_ui import OrderUIWindow
from menu_editor import MenuEditorWindow
from style_helper import apply_default_style
import colors
import colorsys
import updater

APP_VERSION = "v1.1.0" 


class LandingPage:
    def __init__(self, root):
        self.root = root
        self.root.title("Menu Manager")
        self.root.minsize(500, 380)
        self.root.configure(bg=colors.BG_COLOR)
        apply_default_style(root)

        self.establishments = load_menu_files()
        if not self.establishments:
            self.establishments = ["default"]

        # ----- Main frame with padding -----
        main_frame = tk.Frame(root, bg=colors.BG_COLOR, padx=30, pady=25)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Title
        lbl_title = tk.Label(
            main_frame,
            text="Select Establishment",
            font=colors.FONT_HEADER,
            bg=colors.BG_COLOR,
            fg=colors.ACCENT_COLOR,
        )
        lbl_title.grid(row=0, column=0, columnspan=2, sticky="w")

        # Combobox centered and wider for better UX
        self.selected_estab = tk.StringVar(value=self.establishments[0])
        self.combo_estab = ttk.Combobox(
            main_frame,
            values=self.establishments,
            state="readonly",
            textvariable=self.selected_estab,
            font=colors.FONT_DEFAULT,
            justify=tk.CENTER,
            width=32,
        )
        self.combo_estab.grid(row=1, column=0, columnspan=2, pady=(10, 20), sticky="ew")

        # ---- Buttons Section ----
        # Group 1: Ordering & Editor
        btn_order = ttk.Button(main_frame, text="Order Tab", command=self.open_order_tab_new)
        btn_editor = ttk.Button(main_frame, text="Open Menu Editor", command=self.open_menu_editor)
        btn_order.grid(row=2, column=0, padx=8, pady=5, sticky="ew")
        btn_editor.grid(row=2, column=1, padx=8, pady=5, sticky="ew")

        # Group 2: Export / Import
        btn_export = ttk.Button(main_frame, text="Export Menu Code", command=self.export_menu)
        btn_import = ttk.Button(main_frame, text="Import Menu Code", command=self.import_menu)
        btn_export.grid(row=3, column=0, padx=8, pady=5, sticky="ew")
        btn_import.grid(row=3, column=1, padx=8, pady=5, sticky="ew")

        # Group 3: Create / Delete
        btn_create = ttk.Button(main_frame, text="Create New Menu", command=self.create_menu)
        btn_delete = ttk.Button(main_frame, text="Delete Selected Menu", command=self.delete_menu)
        btn_create.grid(row=4, column=0, padx=8, pady=5, sticky="ew")
        btn_delete.grid(row=4, column=1, padx=8, pady=5, sticky="ew")

        # update
        btn_update = ttk.Button(main_frame, text="Check for Updates", command=self.check_updates)
        btn_update.grid(row=5, column=0, columnspan=2, padx=8, pady=5, sticky="ew")

        # Configure grid column weight for even stretching
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)


        # ----- Footer -----
        footer_frame = tk.Frame(root, bg=colors.BG_COLOR)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=10)

        # Credit (left)
        credit_frame = tk.Frame(footer_frame, bg=colors.BG_COLOR)
        credit_frame.pack(side=tk.LEFT, anchor="w")

        # Make credit_label an instance attribute
        self.credit_label = tk.Label(
            credit_frame,
            text="Created by Zerkrx | Axel Pykes",
            font=(colors.FONT_DEFAULT[0], 8),
            bg=colors.BG_COLOR,
            fg=colors.FG_COLOR,
        )
        self.credit_label.pack(anchor="w")

        version_frame = tk.Frame(footer_frame, bg=colors.BG_COLOR)
        version_frame.pack(side=tk.RIGHT, anchor="e")

        version_label = tk.Label(
            version_frame,
            text=f"Version: {APP_VERSION}",
            font=(colors.FONT_DEFAULT[0], 8),
            bg=colors.BG_COLOR,
            fg=colors.FG_COLOR,
        )
        version_label.pack(anchor="e")

        # Animation tracker variable
        self.rainbow_animation_offset = 0

        # Start the rainbow animation on the credit label
        self.animate_rainbow_text()

        # Store window references
        self.order_win = None
        self.editor_win = None
        self.latest_selected_estab = self.establishments[0]


    def check_updates(self):
        repo_path = os.path.abspath(os.path.dirname(__file__))  # Assuming the repo root is this folder
        updated = updater.check_for_updates(repo_path)
        if updated:
            # Optionally, auto restart or close to prompt user
            self.root.destroy()

    def animate_rainbow_text(self):
        import colorsys

        hue = self.rainbow_animation_offset % 360
        r, g, b = colorsys.hsv_to_rgb(hue / 360, 1, 1)
        hex_color = f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
        self.credit_label.config(fg=hex_color)

        self.rainbow_animation_offset += 2
        if self.rainbow_animation_offset >= 360:
            self.rainbow_animation_offset = 0

        self.root.after(33, self.animate_rainbow_text)

        # Store window references
        self.order_win = None
        self.editor_win = None
        self.latest_selected_estab = self.establishments[0]

    def refresh_establishments(self):
        previous_selection = self.selected_estab.get()
        self.establishments = load_menu_files()
        if not self.establishments:
            self.establishments = ["default"]
        self.combo_estab['values'] = self.establishments
        if previous_selection in self.establishments:
            self.selected_estab.set(previous_selection)
            self.latest_selected_estab = previous_selection
        else:
            self.selected_estab.set(self.establishments[0])
            self.latest_selected_estab = self.establishments[0]

    def open_order_tab_new(self):
        est = self.selected_estab.get()
        if self.order_win and self.order_win.winfo_exists():
            self.order_win.lift()
            return
        self.order_win = tk.Toplevel(self.root)
        OrderUIWindow(self.order_win, est)
        self.order_win.focus_force()

    def open_order_tab(self):
        est = self.selected_estab.get()
        if self.order_win and self.order_win.winfo_exists():
            self.order_win.lift()
            return
        self.order_win = tk.Toplevel(self.root)
        self.order_win.title(f"Order Tab - {est}")
        self.order_win.geometry("1100x800")
        OrderUIWindow(self.order_win, est)
        self.order_win.focus_force()

    def open_menu_editor(self):
        est = self.selected_estab.get()
        if self.editor_win and self.editor_win.winfo_exists():
            self.editor_win.lift()
            return

        def on_save_and_select_latest():
            self.refresh_establishments()
            self.selected_estab.set(est)
            self.latest_selected_estab = est

        self.editor_win = tk.Toplevel(self.root)
        self.editor_win.title(f"Menu Editor - {est}")
        self.editor_win.geometry("900x700")
        self.editor_win.transient(self.root)
        self.editor_win.grab_set()
        MenuEditorWindow(self.editor_win, est, on_save_callback=on_save_and_select_latest)

    def export_menu(self):
        est = self.selected_estab.get()
        file_path = os.path.join(MENU_DIR, f"{est}.json")
        if not os.path.isfile(file_path):
            messagebox.showerror("Error", f"Menu file for '{est}' not found.")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                menu_data = json.load(f)
            export_code = json.dumps({"establishment": est, "menu": menu_data}, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load menu: {e}")
            return

        export_win = tk.Toplevel(self.root)
        export_win.title(f"Export Menu Code for '{est}'")
        export_win.geometry("800x600")
        export_win.transient(self.root)

        lbl = tk.Label(export_win, text="Copy this code to share with others:")
        lbl.pack(anchor=tk.W, padx=10, pady=5)

        txt = tk.Text(export_win, wrap=tk.NONE)
        txt.insert("1.0", export_code)
        txt.config(state=tk.DISABLED)
        txt.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(export_code)
            messagebox.showinfo("Copied", "Code copied to clipboard!")

        copy_btn = ttk.Button(export_win, text="Copy to Clipboard", command=copy_to_clipboard)
        copy_btn.pack(pady=5)

        close_btn = ttk.Button(export_win, text="Close", command=export_win.destroy)
        close_btn.pack(pady=5)

    def import_menu(self):
        import_win = tk.Toplevel(self.root)
        import_win.title("Import Menu Code")
        import_win.geometry("600x500")
        import_win.transient(self.root)

        lbl = tk.Label(import_win, text="Paste the menu code here:")
        lbl.pack(anchor=tk.W, padx=10, pady=5)

        txt = tk.Text(import_win, wrap=tk.NONE)
        txt.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

        def do_import():
            code = txt.get("1.0", tk.END).strip()
            if not code:
                messagebox.showwarning("Empty", "Please paste some menu code to import.")
                return
            try:
                data = json.loads(code)
                est_name = data.get("establishment", None)
                menu_data = data.get("menu", None)
                if not est_name or not menu_data:
                    raise ValueError("Invalid menu code structure.")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid JSON code: {e}")
                return

            file_path = os.path.join(MENU_DIR, f"{est_name}.json")
            if os.path.isfile(file_path):
                if not messagebox.askyesno("Overwrite?", f"A menu named '{est_name}' already exists. Overwrite?"):
                    return

            try:
                os.makedirs(MENU_DIR, exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(menu_data, f, indent=2)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save imported menu: {e}")
                return

            messagebox.showinfo("Success", f"Menu '{est_name}' imported successfully.")
            import_win.destroy()
            self.refresh_establishments()
            self.selected_estab.set(est_name)
            self.latest_selected_estab = est_name

        btn_frame = tk.Frame(import_win)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        btn_import = ttk.Button(btn_frame, text="Import", command=do_import)
        btn_import.pack(side=tk.LEFT, padx=5)
        btn_cancel = ttk.Button(btn_frame, text="Cancel", command=import_win.destroy)
        btn_cancel.pack(side=tk.LEFT, padx=5)

    def create_menu(self):
        name = simpledialog.askstring("Create New Menu", "Enter new establishment (menu) name:", parent=self.root)
        if not name:
            return
        name = name.strip()
        if not name:
            messagebox.showwarning("Invalid Name", "Menu name cannot be empty.")
            return

        if name in self.establishments:
            messagebox.showwarning("Exists", f"A menu named '{name}' already exists.")
            return

        os.makedirs(MENU_DIR, exist_ok=True)

        default_menu = {
            "sections": {
                "food": [],
                "drinks": {},
                "desserts": [],
                "animal_treats": [],
                "combos": {}
            },
            "item_limits": {},
            "discounts": {},
            "prices": {"food": 10, "drinks": 7, "animal_treat": 3, "combos": {}}
        }

        file_path = os.path.join(MENU_DIR, f"{name}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(default_menu, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create new menu: {e}")
            return

        messagebox.showinfo("Created", f"Menu '{name}' created successfully.")
        self.refresh_establishments()
        self.selected_estab.set(name)
        self.latest_selected_estab = name

    def delete_menu(self):
        est = self.selected_estab.get()
        if est == "default":
            messagebox.showwarning("Cannot Delete", "Default menu cannot be deleted.")
            return

        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the menu '{est}'? This cannot be undone."):
            return

        try:
            delete_menu_file(est)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete menu: {e}")
            return

        messagebox.showinfo("Deleted", f"Menu '{est}' deleted.")
        self.refresh_establishments()
        self.selected_estab.set(self.establishments[0])
        self.latest_selected_estab = self.establishments[0]