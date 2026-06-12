"""View base com componentes reestilizados - FALL Construções"""
import tkinter as tk
from tkinter import ttk, messagebox
from config import ModernTheme


def _apply_ttk_style():
    """Aplica estilo global ao ttk (chame uma vez no app principal)."""
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # ── Notebook ──────────────────────────────────────────────────────────────
    style.configure(
        "TNotebook",
        background=ModernTheme.BG,
        borderwidth=0,
        tabmargins=[0, 4, 0, 0],
    )
    style.configure(
        "TNotebook.Tab",
        background=ModernTheme.CARD_BG,
        foreground=ModernTheme.TEXT_LIGHT,
        font=ModernTheme.FONT_BASE,
        padding=[14, 8],
        borderwidth=0,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", ModernTheme.PRIMARY), ("active", ModernTheme.PRIMARY_LIGHT)],
        foreground=[("selected", "white"), ("active", ModernTheme.PRIMARY)],
    )

    # ── Treeview ──────────────────────────────────────────────────────────────
    style.configure(
        "Treeview",
        background=ModernTheme.CARD_BG,
        foreground=ModernTheme.TEXT,
        fieldbackground=ModernTheme.CARD_BG,
        rowheight=32,
        font=ModernTheme.FONT_BASE,
        borderwidth=0,
    )
    style.configure(
        "Treeview.Heading",
        background=ModernTheme.SIDEBAR_BG,
        foreground=ModernTheme.TEXT_ON_DARK,
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        padding=[6, 6],
    )
    style.map(
        "Treeview",
        background=[("selected", ModernTheme.PRIMARY)],
        foreground=[("selected", "white")],
    )
    style.map(
        "Treeview.Heading",
        background=[("active", ModernTheme.FERRO)],
    )

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    style.configure(
        "Vertical.TScrollbar",
        background=ModernTheme.BORDER,
        troughcolor=ModernTheme.BG,
        arrowcolor=ModernTheme.TEXT_LIGHT,
        borderwidth=0,
        relief="flat",
    )
    style.map(
        "Vertical.TScrollbar",
        background=[("active", ModernTheme.PRIMARY)],
    )

    # ── Combobox ──────────────────────────────────────────────────────────────
    style.configure(
        "TCombobox",
        background=ModernTheme.CARD_BG,
        fieldbackground=ModernTheme.CARD_BG,
        foreground=ModernTheme.TEXT,
        arrowcolor=ModernTheme.PRIMARY,
        borderwidth=1,
        relief="solid",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", ModernTheme.CARD_BG)],
        bordercolor=[("focus", ModernTheme.PRIMARY)],
    )

    # ── Radiobutton ───────────────────────────────────────────────────────────
    style.configure(
        "TRadiobutton",
        background=ModernTheme.BG,
        foreground=ModernTheme.TEXT,
        font=ModernTheme.FONT_BASE,
    )


class BaseView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller
        self.frame = None

    # ── Visibilidade ──────────────────────────────────────────────────────────
    def show(self):
        if self.frame:
            self.frame.pack(fill=tk.BOTH, expand=True)

    def hide(self):
        if self.frame:
            self.frame.pack_forget()

    # ── Header de página ──────────────────────────────────────────────────────
    def make_page_header(self, parent, icon, title, subtitle=""):
        """Barra de título no topo de cada view."""
        bar = tk.Frame(parent, bg=ModernTheme.HEADER_BG, height=ModernTheme.HEADER_HEIGHT)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        inner = tk.Frame(bar, bg=ModernTheme.HEADER_BG)
        inner.pack(side=tk.LEFT, padx=20, fill=tk.Y)

        tk.Label(
            inner, text=f"{icon}  {title}",
            font=ModernTheme.FONT_XL,
            bg=ModernTheme.HEADER_BG, fg="white",
        ).pack(side=tk.LEFT, pady=0)

        if subtitle:
            tk.Label(
                inner, text=subtitle,
                font=ModernTheme.FONT_SM,
                bg=ModernTheme.HEADER_BG, fg=ModernTheme.TEXT_MUTED,
            ).pack(side=tk.LEFT, padx=(12, 0))

        return bar

    # ── Card ──────────────────────────────────────────────────────────────────
    def create_card(self, parent, title="", fill=tk.X, padx=10, pady=6):
        """Card branco com borda sutil e título opcional."""
        outer = tk.Frame(parent, bg=ModernTheme.BORDER)
        outer.pack(fill=fill, padx=padx, pady=pady)

        card = tk.Frame(outer, bg=ModernTheme.CARD_BG, padx=1, pady=1)
        card.pack(fill=fill, padx=1, pady=1)

        if title:
            hdr = tk.Frame(card, bg=ModernTheme.CARD_BG)
            hdr.pack(fill=tk.X, padx=ModernTheme.CARD_PAD, pady=(12, 4))

            tk.Frame(hdr, bg=ModernTheme.PRIMARY, width=4, height=18).pack(side=tk.LEFT)
            tk.Label(
                hdr, text=f"  {title}",
                font=ModernTheme.FONT_LG,
                bg=ModernTheme.CARD_BG, fg=ModernTheme.TEXT,
            ).pack(side=tk.LEFT)

        return card

    # ── Botões ────────────────────────────────────────────────────────────────
    def styled_button(self, parent, text, command,
                      color=None, width=None, icon="", variant="solid"):
        """
        variant: 'solid' | 'outline' | 'ghost'
        """
        color = color or ModernTheme.PRIMARY
        pad_x = ModernTheme.BTN_PAD_X
        pad_y = ModernTheme.BTN_PAD_Y

        label = f"{icon}  {text}".strip() if icon else text

        if variant == "outline":
            btn = tk.Button(
                parent, text=label, command=command,
                bg=ModernTheme.CARD_BG, fg=color,
                font=("Segoe UI", 10, "bold"),
                bd=1, relief=tk.SOLID,
                highlightbackground=color, highlightthickness=1,
                padx=pad_x, pady=pad_y,
                cursor="hand2",
                activebackground=color, activeforeground="white",
            )
        elif variant == "ghost":
            btn = tk.Button(
                parent, text=label, command=command,
                bg=ModernTheme.BG, fg=color,
                font=("Segoe UI", 10),
                bd=0, relief=tk.FLAT,
                padx=pad_x, pady=pad_y,
                cursor="hand2",
                activebackground=ModernTheme.PRIMARY_LIGHT,
                activeforeground=color,
            )
        else:  # solid
            btn = tk.Button(
                parent, text=label, command=command,
                bg=color, fg="white",
                font=("Segoe UI", 10, "bold"),
                bd=0, relief=tk.FLAT,
                padx=pad_x, pady=pad_y,
                cursor="hand2",
                activebackground=ModernTheme.PRIMARY_HOVER if color == ModernTheme.PRIMARY else color,
                activeforeground="white",
            )

        if width:
            btn.config(width=width)

        # Efeito hover simples
        orig_bg = btn.cget("bg")
        def on_enter(e):
            if variant == "solid":
                btn.config(bg=ModernTheme.PRIMARY_HOVER if color == ModernTheme.PRIMARY else color)
        def on_leave(e):
            if variant == "solid":
                btn.config(bg=orig_bg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return btn

    # ── Inputs ────────────────────────────────────────────────────────────────
    def styled_entry(self, parent, placeholder="", width=30, show=None, font=None):
        font = font or ModernTheme.FONT_MD
        entry = tk.Entry(
            parent,
            font=font,
            bd=1, relief=tk.SOLID,
            highlightthickness=2,
            highlightcolor=ModernTheme.BORDER_FOCUS,
            highlightbackground=ModernTheme.BORDER,
            bg=ModernTheme.CARD_BG,
            fg=ModernTheme.TEXT,
            insertbackground=ModernTheme.PRIMARY,
            width=width,
            show=show or "",
        )
        if placeholder:
            entry.insert(0, placeholder)
            entry.config(fg=ModernTheme.TEXT_MUTED)
            entry.bind("<FocusIn>",  lambda e: self._entry_focus_in(entry, placeholder))
            entry.bind("<FocusOut>", lambda e: self._entry_focus_out(entry, placeholder))
        return entry

    def _entry_focus_in(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=ModernTheme.TEXT)

    def _entry_focus_out(self, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=ModernTheme.TEXT_MUTED)

    # ── Label de seção ────────────────────────────────────────────────────────
    def section_label(self, parent, text, pady=(14, 4)):
        tk.Label(
            parent, text=text.upper(),
            font=("Segoe UI", 8, "bold"),
            bg=ModernTheme.BG, fg=ModernTheme.TEXT_MUTED,
            anchor=tk.W,
        ).pack(fill=tk.X, padx=16, pady=pady)

    # ── Badge de status ───────────────────────────────────────────────────────
    def status_badge(self, parent, text, status):
        colors = {
            "pago":       (ModernTheme.SUCCESS_LIGHT, ModernTheme.SUCCESS),
            "pendente":   (ModernTheme.WARNING_LIGHT, ModernTheme.WARNING),
            "cancelado":  (ModernTheme.DANGER_LIGHT,  ModernTheme.DANGER),
            "atrasado":   (ModernTheme.DANGER_LIGHT,  ModernTheme.DANGER),
            "agendada":   (ModernTheme.INFO_LIGHT,    ModernTheme.INFO),
            "em_transito":(ModernTheme.WARNING_LIGHT, ModernTheme.WARNING),
            "entregue":   (ModernTheme.SUCCESS_LIGHT, ModernTheme.SUCCESS),
        }
        bg, fg = colors.get(status, (ModernTheme.BORDER, ModernTheme.TEXT_LIGHT))
        lbl = tk.Label(
            parent, text=f"  {text}  ",
            font=("Segoe UI", 9, "bold"),
            bg=bg, fg=fg, padx=4, pady=2,
        )
        return lbl

    # ── Mensagens ─────────────────────────────────────────────────────────────
    def show_message(self, title, message, msg_type="info"):
        if msg_type == "error":
            messagebox.showerror(title, message)
        elif msg_type == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)

    # ── Toolbar padrão ────────────────────────────────────────────────────────
    def make_toolbar(self, parent, bg=None):
        bg = bg or ModernTheme.BG
        bar = tk.Frame(parent, bg=bg, pady=10)
        bar.pack(fill=tk.X, padx=16)
        return bar

    # ── Separador ─────────────────────────────────────────────────────────────
    def divider(self, parent, padx=0, pady=6):
        tk.Frame(parent, bg=ModernTheme.BORDER, height=1).pack(
            fill=tk.X, padx=padx, pady=pady
        )

    # ── Formulário em dialog ──────────────────────────────────────────────────
    def make_dialog(self, title, width=480, height=520):
        dlg = tk.Toplevel(self.parent)
        dlg.title(title)
        dlg.geometry(f"{width}x{height}")
        dlg.configure(bg=ModernTheme.BG)
        dlg.transient(self.parent)
        dlg.grab_set()
        # Centraliza
        dlg.update_idletasks()
        x = (dlg.winfo_screenwidth()  // 2) - (width  // 2)
        y = (dlg.winfo_screenheight() // 2) - (height // 2)
        dlg.geometry(f"{width}x{height}+{x}+{y}")
        return dlg

    def form_field(self, parent, label, widget_or_none=None,
                   width=40, show=None, value=""):
        """Cria label + entry padronizado dentro de um container."""
        tk.Label(
            parent, text=label,
            font=("Segoe UI", 10, "bold"),
            bg=ModernTheme.BG, fg=ModernTheme.TEXT,
            anchor=tk.W,
        ).pack(fill=tk.X, padx=20, pady=(10, 2))

        if widget_or_none is None:
            entry = self.styled_entry(parent, width=width, show=show)
            if value:
                entry.insert(0, value)
            entry.pack(fill=tk.X, padx=20, pady=(0, 4))
            return entry
        else:
            widget_or_none.pack(fill=tk.X, padx=20, pady=(0, 4))
            return widget_or_none