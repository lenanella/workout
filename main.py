import tkinter as tk
from tkinter import ttk, messagebox
import asyncio
import threading
import winsound

import database
import network
import file_manager


BG        = "#1e1e2e"  
SURFACE   = "#2a2a3d"  
ACCENT    = "#7c6af7"   
ACCENT2   = "#f7826a"   
GREEN     = "#3ddc97"  
TEXT      = "#e0e0f0"   
SUBTEXT   = "#9090b0"  
ENTRY_BG  = "#13131f"   
TREE_SEL  = "#3a3a5c"   
FONT      = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H    = ("Segoe UI", 13, "bold")


def run_async(coro):
    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
        loop.close()
    threading.Thread(target=runner, daemon=True).start()


class WorkoutDiaryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Workout Diary")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self._apply_styles()
        database.init_db()
        self._build_ui()
        self.refresh_list()



    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".",
            background=BG, foreground=TEXT,
            font=FONT, borderwidth=0)

        style.configure("Card.TFrame", background=SURFACE)
        style.configure("Root.TFrame", background=BG)

        style.configure("Card.TLabelframe",
            background=SURFACE, foreground=SUBTEXT,
            font=("Segoe UI", 9), bordercolor="#3a3a5c",
            relief="flat", padding=12)
        style.configure("Card.TLabelframe.Label",
            background=SURFACE, foreground=SUBTEXT, font=("Segoe UI", 9))

        style.configure("Treeview",
            background=SURFACE, foreground=TEXT,
            fieldbackground=SURFACE, rowheight=26,
            borderwidth=0, font=FONT)
        style.configure("Treeview.Heading",
            background="#13131f", foreground=SUBTEXT,
            font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview",
            background=[("selected", TREE_SEL)],
            foreground=[("selected", TEXT)])

        style.configure("Vertical.TScrollbar",
            background=SURFACE, troughcolor=BG,
            arrowcolor=SUBTEXT, borderwidth=0)


    def _build_ui(self):
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(padx=20, pady=20)

      
        tk.Label(outer, text="💪 Workout Diary",
                 bg=BG, fg=TEXT, font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 14))

        card = tk.Frame(outer, bg=SURFACE, bd=0)
        card.pack(fill="x", pady=(0, 12))

        inner = tk.Frame(card, bg=SURFACE)
        inner.pack(padx=16, pady=14, fill="x")

        tk.Label(inner, text="NEW WORKOUT", bg=SURFACE, fg=SUBTEXT,
                 font=("Segoe UI", 8, "bold")).grid(row=0, columnspan=4, sticky="w", pady=(0, 10))

        fields = [
            ("Date", "YYYY-MM-DD"),
            ("Exercise", "e.g. Running"),
            ("Duration (min)", "e.g. 45"),
            ("Notes", "optional"),
        ]
        self.entries = {}
        col_offset = 0
        for i, (label, placeholder) in enumerate(fields):
            col = (i % 2) * 2
            row = 1 + i // 2

            tk.Label(inner, text=label, bg=SURFACE, fg=SUBTEXT,
                     font=("Segoe UI", 9)).grid(row=row*2-1, column=col, sticky="w", padx=(0 if col==0 else 16, 0))

            e = tk.Entry(inner, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                         font=FONT, relief="flat", width=24,
                         highlightthickness=1, highlightcolor=ACCENT,
                         highlightbackground="#2e2e45")
            e.insert(0, placeholder)
            e.config(fg=SUBTEXT)
            e.bind("<FocusIn>",  lambda ev, en=e, ph=placeholder: self._on_focus_in(ev, en, ph))
            e.bind("<FocusOut>", lambda ev, en=e, ph=placeholder: self._on_focus_out(ev, en, ph))
            e.grid(row=row*2, column=col, sticky="ew", pady=(2, 8),
                   padx=(0 if col==0 else 16, 0), ipady=6, ipadx=6)
            self.entries[label] = e

        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(2, weight=1)

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill="x", pady=(0, 12))

        self._btn(btn_row, "＋  Add Workout",   GREEN,   "#2e2e2e", self.add_workout).pack(side="left", padx=(0, 8))
        self._btn(btn_row, "↓  Export JSON",    ACCENT,  "#2e2e2e", self.export_json).pack(side="left", padx=(0, 8))
        self._btn(btn_row, "Дай мотивации", ACCENT2, "#2e2e2e", self.get_motivation).pack(side="left")

        self.quote_frame = tk.Frame(outer, bg="#2a1f3d", bd=0)
        self.quote_frame.pack(fill="x", pady=(0, 12))

        self.quote_var = tk.StringVar(value="")
        self.quote_label = tk.Label(
            self.quote_frame, textvariable=self.quote_var,
            bg="#2a1f3d", fg="#c9b8ff",
            font=("Segoe UI", 10, "italic"),
            wraplength=500, justify="center", pady=10, padx=14
        )
        self.quote_label.pack()
        self.quote_frame.pack_forget() 


        list_card = tk.Frame(outer, bg=SURFACE)
        list_card.pack(fill="x")

        tk.Label(list_card, text="ALL WORKOUTS", bg=SURFACE, fg=SUBTEXT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=16, pady=(12, 6))

        tree_frame = tk.Frame(list_card, bg=SURFACE)
        tree_frame.pack(padx=16, pady=(0, 14), fill="x")

        cols    = ("id", "date", "exercise", "duration", "notes")
        widths  = (36, 100, 140, 80, 190)
        headers = ("#", "Date", "Exercise", "Min", "Notes")

        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        for col, w, h in zip(cols, widths, headers):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=w, anchor="center" if col in ("id","duration") else "w")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


        self.tree.tag_configure("odd",  background=SURFACE)
        self.tree.tag_configure("even", background="#232335")

    def _btn(self, parent, text, bg, activebg, command):
        return tk.Button(
            parent, text=text, command=command,
            bg=bg, fg="#1e1e2e", activebackground=bg,
            font=("Segoe UI", 10, "bold"),
            relief="flat", bd=0, cursor="hand2",
            padx=16, pady=8
        )

    def _on_focus_in(self, event, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=TEXT)

    def _on_focus_out(self, event, entry, placeholder):
        if not entry.get():
            entry.insert(0, placeholder)
            entry.config(fg=SUBTEXT)

    def _get_entry(self, label):
        """Return entry value, ignoring placeholder text."""
        placeholders = {
            "Date": "YYYY-MM-DD",
            "Exercise": "e.g. Running",
            "Duration (min)": "e.g. 45",
            "Notes": "optional",
        }
        val = self.entries[label].get().strip()
        return "" if val == placeholders.get(label, "") else val


    def add_workout(self):
        date     = self._get_entry("Date")
        exercise = self._get_entry("Exercise")
        dur_str  = self._get_entry("Duration (min)")
        notes    = self._get_entry("Notes")

        if not date or not exercise or not dur_str:
            messagebox.showwarning("Missing fields", "Date, Exercise and Duration are required.")
            return
        try:
            duration = int(dur_str)
        except ValueError:
            messagebox.showerror("Invalid input", "Duration must be a number.")
            return

        database.add_workout(date, exercise, duration, notes)
        winsound.MessageBeep(winsound.MB_OK)

        for label, entry in self.entries.items():
            placeholders = {
                "Date": "YYYY-MM-DD", "Exercise": "e.g. Running",
                "Duration (min)": "e.g. 45", "Notes": "optional",
            }
            entry.delete(0, tk.END)
            entry.insert(0, placeholders[label])
            entry.config(fg=SUBTEXT)

        self.refresh_list()

    def refresh_list(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, workout in enumerate(database.get_all_workouts()):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", tk.END, values=workout, tags=(tag,))

    def export_json(self):
        file_manager.export_to_json(database.get_all_workouts())
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
        messagebox.showinfo("Exported", "Workouts saved to export.json")

    def get_motivation(self):
        self.quote_var.set("Загружаю цитату...")
        self.quote_frame.pack(fill="x", pady=(0, 12), before=self.quote_frame.master.winfo_children()[-1])
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)

        async def fetch():
            quote = await network.fetch_quote()
            self.root.after(0, lambda: self.quote_var.set(quote))
            self.root.after(0, lambda: self.quote_frame.pack(fill="x", pady=(0, 12)))

        run_async(fetch())


if __name__ == "__main__":
    root = tk.Tk()
    app = WorkoutDiaryApp(root)
    root.mainloop()
