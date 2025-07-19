# style_helper.py

import tkinter.ttk as ttk
import colors


def apply_default_style(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    # General style
    style.configure(
        ".",
        background=colors.BG_COLOR,
        foreground=colors.FG_COLOR,
        font=colors.FONT_DEFAULT,
    )

    # TLabel
    style.configure("TLabel", background=colors.BG_COLOR, foreground=colors.FG_COLOR, font=colors.FONT_ITEM)

    # TButton default style
    style.configure(
        "TButton",
        background=colors.BUTTON_BG,
        foreground="white",
        font=colors.FONT_BUTTON,
        padding=6,
        borderwidth=0,
        relief="flat",
        focuscolor="",
    )
    style.map(
        "TButton",
        background=[("active", colors.BUTTON_HOVER_BG)],
        foreground=[("disabled", "#a9a9a9")],
    )

    # Accent Button style
    style.configure("Accent.TButton", background=colors.BUTTON_BG, foreground="white", font=colors.FONT_BUTTON)
    style.map("Accent.TButton", background=[("active", colors.BUTTON_HOVER_BG)])

    # Treeview
    style.configure(
        "Treeview",
        background=colors.PANEL_BG,
        foreground=colors.FG_COLOR,
        fieldbackground=colors.PANEL_BG,
        font=colors.FONT_DEFAULT,
        bordercolor=colors.PANEL_BG,
        borderwidth=0,
        relief="flat",
    )
    style.map("Treeview", background=[("selected", colors.ACCENT_COLOR)], foreground=[("selected", "white")])

    style.configure(
        "Treeview.Heading",
        background=colors.BUTTON_BG,
        foreground="white",
        font=colors.FONT_HEADER,
        relief="flat",
    )

    # Labelframe
    style.configure(
        "TLabelframe",
        background=colors.BG_COLOR,
        foreground=colors.ACCENT_COLOR,
        font=colors.FONT_HEADER,
        borderwidth=1,
        relief="solid",
    )
    style.configure("TLabelframe.Label", background=colors.BG_COLOR, foreground=colors.ACCENT_COLOR, font=colors.FONT_HEADER)

    # TEntry
    style.configure(
        "TEntry",
        fieldbackground=colors.SUBPANEL_BG,
        background=colors.SUBPANEL_BG,
        foreground=colors.FG_COLOR,
        borderwidth=0,
        relief="flat",
        font=colors.FONT_SPINBOX,
    )

    # Vertical Scrollbar
    style.configure(
        "Vertical.TScrollbar",
        gripcount=0,
        background=colors.SCROLLBAR_BG,
        darkcolor="#3f4a82",
        lightcolor="#172b5c",
        troughcolor="#1c2240",
        bordercolor="#5a4db2",
        arrowcolor="#9b9bff",
    )

    # Discount checkbutton style
    style.configure(
        "Discount.TCheckbutton",
        background=colors.PANEL_BG,
        foreground=colors.FG_COLOR,
        font=colors.FONT_DISCOUNT,
    )
    style.map(
        "Discount.TCheckbutton",
        background=[("active", colors.BUTTON_BG), ("!active", colors.PANEL_BG)],
        foreground=[("active", colors.FG_COLOR), ("!active", colors.FG_COLOR)],
    )