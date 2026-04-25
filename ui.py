import tkinter as tk
from tkinter import ttk
import pandas as pd

# =========================================================
# Constants / Global UI Text
# =========================================================
PLACEHOLDER = "What kind of game are you looking for?"


class GameUI:
    def __init__(self, engine):
        # =========================================================
        # Core App Setup
        # =========================================================
        self.engine = engine
        self.current_results = None

        self.root = tk.Tk()
        self.root.title("GameSense")
        self.root.geometry("1320x780")
        self.root.minsize(1100, 650)

        # Build the application
        self._setup_theme()
        self._build_ui()
        self._bind_events()
        self._reset_placeholder()

    # =========================================================
    # Theme / Styling Configuration
    # =========================================================
    def _setup_theme(self):
        self.colors = {
            # Main backgrounds
            "bg": "#FFFFFF",
            "card": "#F7F7F7",

            # Header
            "header": "#500000",
            "header_text": "#FFFFFF",
            "header_subtitle": "#E5E7EB",

            # Text
            "text": "#111111",
            "muted": "#6B7280",

            # Borders / accents
            "border": "#C0C0C0",
            "soft_fill": "#EFEFEF",
            "alt_row": "#F1F1F1",

            # Buttons
            "primary": "#500000",
            "primary_hover": "#3E0000",
            "secondary": "#E5E7EB",
            "secondary_hover": "#D1D5DB",

            # Inputs / states
            "input_bg": "#FFFFFF",
            "focus": "#500000",
            "selected": "#E6D6D6",
            
            # Match relevance colors
            "match_high": "#E8F5E9",
            "match_good": "#EAF2FF",
            "match_mid": "#FFF8E1",
            "match_low": "#FDECEC",
        }

        self.fonts = {
            "title": ("Segoe UI", 22, "bold"),
            "subtitle": ("Segoe UI", 10),
            "label": ("Segoe UI", 10, "bold"),
            "body": ("Segoe UI", 10),
            "search": ("Segoe UI", 14),
            "button": ("Segoe UI", 10, "bold"),
            "table": ("Segoe UI", 10),
            "table_heading": ("Segoe UI", 10, "bold"),
            "detail_title": ("Segoe UI", 16, "bold"),
            "detail_section": ("Segoe UI", 11, "bold"),
        }

        self.root.configure(bg=self.colors["bg"])

        self.style = ttk.Style()
        self.style.theme_use("default")

        # -------------------------
        # Treeview styling
        # -------------------------
        self.style.configure(
            "Game.Treeview",
            background=self.colors["card"],
            foreground=self.colors["text"],
            fieldbackground=self.colors["card"],
            rowheight=30,
            borderwidth=0,
            font=self.fonts["table"],
        )

        self.style.configure(
            "Game.Treeview.Heading",
            background=self.colors["header"],
            foreground=self.colors["header_text"],
            font=self.fonts["table_heading"],
            relief="flat",
            borderwidth=1,
        )

        self.style.map(
            "Game.Treeview",
            background=[("selected", self.colors["selected"])],
            foreground=[("selected", self.colors["text"])],
        )

        self.style.map(
            "Game.Treeview.Heading",
            background=[("active", self.colors["primary_hover"])],
            foreground=[("active", self.colors["header_text"])],
        )

    # =========================================================
    # Main UI Construction
    # =========================================================
    def _build_ui(self):
        self._build_header()
        self._build_search_bar()
        self._build_filters_card()
        self._build_button_row()
        self._build_results_table()

    # =========================================================
    # Header Section
    # =========================================================
    def _build_header(self):
        header = tk.Frame(self.root, bg=self.colors["header"], height=100)
        header.pack(fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=self.colors["header"])
        left.pack(side="left", padx=20, pady=14)

        title = tk.Label(
            left,
            text="GameSense",
            bg=self.colors["header"],
            fg=self.colors["header_text"],
            font=self.fonts["title"],
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            left,
            text="Search and explore games with smarter ranking",
            bg=self.colors["header"],
            fg=self.colors["header_subtitle"],
            font=self.fonts["subtitle"],
        )
        subtitle.pack(anchor="w")

    # =========================================================
    # Search Bar Section
    # =========================================================
    def _build_search_bar(self):
        search_wrap = tk.Frame(self.root, bg=self.colors["bg"])
        search_wrap.pack(fill="x", padx=20, pady=(18, 10))

        search_card = tk.Frame(
            search_wrap,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
        )
        search_card.pack(fill="x")

        self.entry_nlp = tk.Entry(
            search_card,
            font=self.fonts["search"],
            fg=self.colors["muted"],
            bg=self.colors["input_bg"],
            relief="flat",
            insertbackground=self.colors["text"],
            bd=0,
        )
        self.entry_nlp.pack(fill="x", padx=16, pady=16, ipady=8)

    # =========================================================
    # Filters Section
    # =========================================================
    def _build_filters_card(self):
        self.filters_card = tk.Frame(
            self.root,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
        )
        self.filters_card.pack(fill="x", padx=20, pady=(0, 10))

        filters_title = tk.Label(
            self.filters_card,
            text="Filters",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 11, "bold"),
        )
        filters_title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 6))

        fields_frame = tk.Frame(self.filters_card, bg=self.colors["card"])
        fields_frame.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 12))

        for i in range(4):
            fields_frame.grid_columnconfigure(i, weight=1)

        for r in range(4):
            fields_frame.grid_rowconfigure(r, pad=4)

        # -------------------------
        # First row of filters
        # -------------------------
        self.entry_name = self._labeled_entry(fields_frame, "Name", 0, 0)
        self.entry_genre = self._labeled_entry(fields_frame, "Genre", 0, 1)
        self.entry_theme = self._labeled_entry(fields_frame, "Theme", 0, 2)
        self.entry_platform = self._labeled_entry(fields_frame, "Platform", 0, 3)

        # -------------------------
        # Second row of filters
        # -------------------------
        self.entry_developer = self._labeled_entry(fields_frame, "Developer", 1, 0)
        self.entry_publisher = self._labeled_entry(fields_frame, "Publisher", 1, 1)
        self.entry_mode = self._labeled_entry(fields_frame, "Game Mode", 1, 2)

        # -------------------------
        # Rating range in second row, fourth column
        # -------------------------
        rating_label = tk.Label(
            fields_frame,
            text="Rating Range",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=self.fonts["label"],
        )
        rating_label.grid(row=2, column=3, sticky="w", padx=8, pady=(8, 4))

        rating_frame = tk.Frame(fields_frame, bg=self.colors["card"])
        rating_frame.grid(row=3, column=3, sticky="w", padx=8, pady=(0, 4))

        self.entry_rating_min = self._styled_entry(rating_frame, width=8)
        self.entry_rating_min.pack(side="left")

        dash = tk.Label(
            rating_frame,
            text="to",
            bg=self.colors["card"],
            fg=self.colors["muted"],
            font=self.fonts["body"],
        )
        dash.pack(side="left", padx=8)

        self.entry_rating_max = self._styled_entry(rating_frame, width=8)
        self.entry_rating_max.pack(side="left")

    # =========================================================
    # Button Row / Status Section
    # =========================================================
    def _build_button_row(self):
        btn_row = tk.Frame(self.root, bg=self.colors["bg"])
        btn_row.pack(fill="x", padx=20, pady=(0, 10))

        left = tk.Frame(btn_row, bg=self.colors["bg"])
        left.pack(side="left")

        self.search_btn = tk.Button(
            left,
            text="Search",
            command=self.search,
            bg=self.colors["primary"],
            fg="white",
            font=self.fonts["button"],
            relief="flat",
            bd=0,
            activebackground=self.colors["primary_hover"],
            activeforeground="white",
            padx=18,
            pady=10,
            cursor="hand2",
        )
        self.search_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = tk.Button(
            left,
            text="Clear",
            command=self.clear,
            bg=self.colors["secondary"],
            fg=self.colors["text"],
            font=self.fonts["button"],
            relief="flat",
            bd=0,
            activebackground=self.colors["secondary_hover"],
            activeforeground=self.colors["text"],
            padx=18,
            pady=10,
            cursor="hand2",
        )
        self.clear_btn.pack(side="left")

        self.count_label = tk.Label(
            btn_row,
            text=f"{self.engine.get_total_count():,} games available",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=self.fonts["body"],
        )
        self.count_label.pack(side="left", padx=18, pady=6)

    # =========================================================
    # Results Table Section
    # =========================================================
    def _build_results_table(self):
        results_card = tk.Frame(
            self.root,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
        )
        results_card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        results_title = tk.Label(
            results_card,
            text="Results",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=("Segoe UI", 11, "bold"),
        )
        results_title.pack(anchor="w", padx=16, pady=(14, 8))

        table_frame = tk.Frame(results_card, bg=self.colors["card"])
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        cols = (
            "Name",
            "Match",
            "Genres",
            "Themes",
            "Platforms",
            "Developers",
            "Publishers",
            "Rating",
            "Game Modes",
        )
        col_widths = (190, 190, 150, 130, 160, 140, 150, 70, 130)

        scrollbar_y = ttk.Scrollbar(table_frame, orient="vertical")
        scrollbar_x = ttk.Scrollbar(table_frame, orient="horizontal")

        self.tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            style="Game.Treeview",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
        )

        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)

        for col, width in zip(cols, col_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, minwidth=70, anchor="w")

        self.tree.tag_configure("evenrow", background=self.colors["card"])
        self.tree.tag_configure("oddrow", background=self.colors["alt_row"])
        self.tree.tag_configure("match_high", background=self.colors["match_high"])
        self.tree.tag_configure("match_good", background=self.colors["match_good"])
        self.tree.tag_configure("match_mid", background=self.colors["match_mid"])
        self.tree.tag_configure("match_low", background=self.colors["match_low"])

        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

    # =========================================================
    # Helper Methods for Shared UI Elements
    # =========================================================
    def _styled_entry(self, parent, width=22):
        entry = tk.Entry(
            parent,
            width=width,
            font=self.fonts["body"],
            bg=self.colors["input_bg"],
            fg=self.colors["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            highlightcolor=self.colors["focus"],
            insertbackground=self.colors["text"],
        )
        return entry

    def _labeled_entry(self, parent, label, row, col):
        label_widget = tk.Label(
            parent,
            text=label,
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=self.fonts["label"],
        )
        label_widget.grid(row=row * 2, column=col, sticky="w", padx=8, pady=(8, 4))

        entry = self._styled_entry(parent)
        entry.grid(row=row * 2 + 1, column=col, sticky="ew", padx=8, pady=(0, 4), ipady=6)

        return entry
        
    def _normalize_score(self, score):
        try:
            score = float(score)
        except (ValueError, TypeError):
            return 0.0

        return max(0.0, min(score, 1.0))


    def _score_bar(self, normalized_score, length=10):
        try:
            normalized_score = float(normalized_score)
        except (ValueError, TypeError):
            normalized_score = 0.0

        normalized_score = max(0.0, min(normalized_score, 1.0))
        filled = round(normalized_score * length)
        return "█" * filled + "░" * (length - filled)


    def _relevance_label(self, normalized_score):
        try:
            normalized_score = float(normalized_score)
        except (ValueError, TypeError):
            return "N/A"

        if normalized_score >= 0.85:
            return "Top Result"
        elif normalized_score >= 0.60:
            return "High Relevance"
        elif normalized_score >= 0.35:
            return "Moderate Relevance"
        else:
            return "Low Relevance"


    def _match_display(self, raw_score):
        normalized = self._normalize_score(raw_score)
        label = self._relevance_label(normalized)
        bar = self._score_bar(normalized)
        percent = int(round(normalized * 100))
        return f"{label} {bar} Score {percent}"
    
    def _match_tag(self, raw_score):
        normalized = self._normalize_score(raw_score)

        if normalized >= 0.85:
            return "match_high"
        elif normalized >= 0.60:
            return "match_good"
        elif normalized >= 0.35:
            return "match_mid"
        else:
            return "match_low"

    # =========================================================
    # Event Binding Section
    # =========================================================
    def _bind_events(self):
        self.entry_nlp.bind("<FocusIn>", self._on_nlp_focus_in)
        self.entry_nlp.bind("<FocusOut>", self._on_nlp_focus_out)
        self.tree.bind("<Double-1>", self.show_game_details)
        self.root.bind("<Return>", lambda event: self.search())

        self.search_btn.bind(
            "<Enter>",
            lambda e: self.search_btn.configure(bg=self.colors["primary_hover"])
        )
        self.search_btn.bind(
            "<Leave>",
            lambda e: self.search_btn.configure(bg=self.colors["primary"])
        )

        self.clear_btn.bind(
            "<Enter>",
            lambda e: self.clear_btn.configure(bg=self.colors["secondary_hover"])
        )
        self.clear_btn.bind(
            "<Leave>",
            lambda e: self.clear_btn.configure(bg=self.colors["secondary"])
        )

    # =========================================================
    # Placeholder / Search Bar UX
    # =========================================================
    def _reset_placeholder(self):
        self.entry_nlp.delete(0, tk.END)
        self.entry_nlp.insert(0, PLACEHOLDER)
        self.entry_nlp.config(fg=self.colors["muted"])

    def _on_nlp_focus_in(self, event):
        if self.entry_nlp.get() == PLACEHOLDER:
            self.entry_nlp.delete(0, tk.END)
            self.entry_nlp.config(fg=self.colors["text"])

    def _on_nlp_focus_out(self, event):
        if self.entry_nlp.get().strip() == "":
            self._reset_placeholder()

    # =========================================================
    # Clear / Reset UI State
    # =========================================================
    def clear(self):
        self.current_results = None

        for entry in [
            self.entry_name,
            self.entry_genre,
            self.entry_theme,
            self.entry_platform,
            self.entry_developer,
            self.entry_publisher,
            self.entry_mode,
            self.entry_rating_min,
            self.entry_rating_max,
        ]:
            entry.delete(0, tk.END)

        self._reset_placeholder()

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.count_label.config(text=f"{self.engine.get_total_count():,} games available")

    # =========================================================
    # Search Action / Populate Results Table
    # =========================================================
    def search(self):
        query_text = self.entry_nlp.get().strip()
        if query_text == PLACEHOLDER:
            query_text = ""

        results = self.engine.search(
            query_text=query_text,
            name=self.entry_name.get().strip(),
            genre=self.entry_genre.get().strip(),
            theme=self.entry_theme.get().strip(),
            platform=self.entry_platform.get().strip(),
            developer=self.entry_developer.get().strip(),
            publisher=self.entry_publisher.get().strip(),
            game_mode=self.entry_mode.get().strip(),
            rating_min=self.entry_rating_min.get().strip(),
            rating_max=self.entry_rating_max.get().strip(),
            limit=100,
        )

        self.current_results = results.reset_index(drop=True)

        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, (_, r) in enumerate(self.current_results.iterrows()):
            rating = "N/A"
            if pd.notna(r.get("rating")) and str(r["rating"]).strip() != "":
                try:
                    rating = f"{float(r['rating']):.1f}"
                except ValueError:
                    rating = str(r["rating"])

            match_text = self._match_display(r.get("score"))

            values = (
                r["name"] if pd.notna(r.get("name")) else "",
                match_text,
                r["genres"] if pd.notna(r.get("genres")) else "",
                r["themes"] if pd.notna(r.get("themes")) else "",
                r["platforms"] if pd.notna(r.get("platforms")) else "",
                r["developers"] if pd.notna(r.get("developers")) else "",
                r["publishers"] if pd.notna(r.get("publishers")) else "",
                rating,
                r["game_modes"] if pd.notna(r.get("game_modes")) else "",
            )

            tag = self._match_tag(r.get("score"))

            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=values,
                tags=(tag,),
            )

        self.count_label.config(text=f"{len(self.current_results)} result(s) shown (max 100)")

    # =========================================================
    # Game Detail Popup Window
    # =========================================================
    def show_game_details(self, event=None):
        selected = self.tree.selection()
        if not selected or self.current_results is None:
            return

        row_id = selected[0]

        try:
            game = self.current_results.iloc[int(row_id)]
        except (ValueError, IndexError):
            return

        detail_window = tk.Toplevel(self.root)
        detail_window.title(game["name"] if pd.notna(game.get("name")) else "Game Details")
        detail_window.geometry("860x680")
        detail_window.minsize(700, 500)
        detail_window.configure(bg=self.colors["bg"])

        # -------------------------
        # Popup header
        # -------------------------
        popup_header = tk.Frame(detail_window, bg=self.colors["header"], height=88)
        popup_header.pack(fill="x")
        popup_header.pack_propagate(False)

        popup_title = tk.Label(
            popup_header,
            text=game["name"] if pd.notna(game.get("name")) else "Game Details",
            bg=self.colors["header"],
            fg=self.colors["header_text"],
            font=self.fonts["detail_title"],
        )
        popup_title.pack(anchor="w", padx=20, pady=(14, 2))

        popup_subtitle = tk.Label(
            popup_header,
            text="Detailed game information",
            bg=self.colors["header"],
            fg=self.colors["header_subtitle"],
            font=self.fonts["subtitle"],
        )
        popup_subtitle.pack(anchor="w", padx=20)

        # -------------------------
        # Popup content card
        # -------------------------
        outer = tk.Frame(detail_window, bg=self.colors["bg"])
        outer.pack(fill="both", expand=True, padx=20, pady=18)

        container = tk.Frame(
            outer,
            bg=self.colors["card"],
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
        )
        container.pack(fill="both", expand=True)

        top_card = tk.Frame(container, bg=self.colors["card"])
        top_card.pack(fill="x", padx=18, pady=(18, 8))

        def safe_value(column_name):
            if column_name in game and pd.notna(game[column_name]) and str(game[column_name]).strip():
                return str(game[column_name])
            return "N/A"

        # score_text = "N/A"
        # if pd.notna(game.get("score")):
        #     try:
        #         score_text = f"{float(game['score']):.3f}"
        #     except (ValueError, TypeError):
        #         score_text = str(game["score"])
        
        score_text = self._match_display(game.get("score"))

        rating_text = "N/A"
        if pd.notna(game.get("rating")):
            try:
                rating_text = f"{float(game['rating']):.1f}"
            except (ValueError, TypeError):
                rating_text = str(game["rating"])

        info_items = [
            ("Match", score_text),
            ("Rating", rating_text),
            ("Genres", safe_value("genres")),
            ("Themes", safe_value("themes")),
            ("Platforms", safe_value("platforms")),
            ("Game Modes", safe_value("game_modes")),
            ("Developers", safe_value("developers")),
            ("Publishers", safe_value("publishers")),
        ]

        info_grid = tk.Frame(top_card, bg=self.colors["soft_fill"])
        info_grid.pack(fill="x")
        info_grid.configure(
            highlightbackground=self.colors["border"],
            highlightthickness=1,
            bd=0,
        )

        for idx, (label, value) in enumerate(info_items):
            row = idx // 2
            col = (idx % 2) * 2

            lbl = tk.Label(
                info_grid,
                text=f"{label}:",
                bg=self.colors["soft_fill"],
                fg=self.colors["text"],
                font=self.fonts["label"],
                anchor="w",
            )
            lbl.grid(row=row, column=col, sticky="nw", padx=(14, 8), pady=10)

            val = tk.Label(
                info_grid,
                text=value,
                bg=self.colors["soft_fill"],
                fg=self.colors["text"],
                font=self.fonts["body"],
                anchor="w",
                justify="left",
                wraplength=250,
            )
            val.grid(row=row, column=col + 1, sticky="nw", padx=(0, 14), pady=10)

        text_section_label = tk.Label(
            container,
            text="Description",
            bg=self.colors["card"],
            fg=self.colors["text"],
            font=self.fonts["detail_section"],
        )
        text_section_label.pack(anchor="w", padx=18, pady=(8, 6))

        text_frame = tk.Frame(container, bg=self.colors["card"])
        text_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")
        
        
        detail_text = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=scrollbar.set,
            font=("Segoe UI", 10),
            bg=self.colors["card"],
            fg=self.colors["text"],
            relief="flat",
            padx=12,
            pady=12,
            insertbackground=self.colors["text"],
            spacing1=4,
            spacing2=2,
            spacing3=8,
        )
        detail_text.pack(fill="both", expand=True)
        scrollbar.config(command=detail_text.yview)

        # details = f"""Keywords:
        # {safe_value("keywords")}

        # Summary:
        # {safe_value("summary")}

        # Storyline:
        # {safe_value("storyline")}"""
        
        # detail_text.tag_configure(
        #     "section",
        #     lmargin1=20,
        #     lmargin2=20
        # )
        
        detail_text.insert("1.0", "Keywords:\n", "header")
        detail_text.insert("end", safe_value("keywords") + "\n\n", "section")
        detail_text.insert("end", "Summary:\n", "header")
        detail_text.insert("end", safe_value("summary") + "\n\n", "section")
        detail_text.insert("end", "Storyline:\n", "header")
        detail_text.insert("end", safe_value("storyline") + "\n\n", "section")
        detail_text.config(state="disabled")

    # =========================================================
    # Run Application
    # =========================================================
    def run(self):
        self.root.mainloop()
