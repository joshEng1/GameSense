import tkinter as tk
from tkinter import ttk
import pandas as pd
from search_engine import SearchEngine

engine = SearchEngine()

PLACEHOLDER = "What kind of game are you looking for?"
current_results = None


def search():
    global current_results

    query_text = entry_nlp.get().strip()

    if query_text == PLACEHOLDER:
        query_text = ""

    results = engine.search(
        query_text=query_text,
        name=entry_name.get().strip(),
        genre=entry_genre.get().strip(),
        theme=entry_theme.get().strip(),
        platform=entry_platform.get().strip(),
        developer=entry_developer.get().strip(),
        publisher=entry_publisher.get().strip(),
        game_mode=entry_mode.get().strip(),
        rating_min=entry_rating_min.get().strip(),
        rating_max=entry_rating_max.get().strip(),
        limit=100,
    )

    current_results = results.reset_index(drop=True)

    for row in tree.get_children():
        tree.delete(row)

    for i, (_, r) in enumerate(current_results.iterrows()):
        rating = "N/A"
        if pd.notna(r["rating"]) and str(r["rating"]).strip() != "":
            try:
                rating = f"{float(r['rating']):.1f}"
            except ValueError:
                rating = str(r["rating"])

        tree.insert(
            "",
            "end",
            iid=str(i),
            values=(
                r["name"] if pd.notna(r["name"]) else "",
                r["genres"] if pd.notna(r["genres"]) else "",
                r["themes"] if pd.notna(r["themes"]) else "",
                r["platforms"] if pd.notna(r["platforms"]) else "",
                r["developers"] if pd.notna(r["developers"]) else "",
                r["publishers"] if pd.notna(r["publishers"]) else "",
                rating,
                r["game_modes"] if pd.notna(r["game_modes"]) else "",
            )
        )

    count_label.config(text=f"{len(current_results)} result(s) shown (max 100)")
    
def show_game_details(event=None):
    selected = tree.selection()
    if not selected:
        return

    row_id = selected[0]

    if current_results is None:
        return

    try:
        game = current_results.iloc[int(row_id)]
    except (ValueError, IndexError):
        return

    detail_window = tk.Toplevel(root)
    detail_window.title(game["name"] if pd.notna(game["name"]) else "Game Details")
    detail_window.geometry("750x600")

    text_frame = tk.Frame(detail_window, padx=12, pady=12)
    text_frame.pack(fill="both", expand=True)

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")

    detail_text = tk.Text(
        text_frame,
        wrap="word",
        yscrollcommand=scrollbar.set,
        font=("Helvetica", 11)
    )
    detail_text.pack(fill="both", expand=True)
    scrollbar.config(command=detail_text.yview)

    def safe_value(column_name):
        if column_name in game and pd.notna(game[column_name]) and str(game[column_name]).strip():
            return str(game[column_name])
        return "N/A"

    details = f"""
        Name: {safe_value("name")}

        Rating: {safe_value("rating")}
        Genres: {safe_value("genres")}
        Themes: {safe_value("themes")}
        Platforms: {safe_value("platforms")}
        Game Modes: {safe_value("game_modes")}
        Developers: {safe_value("developers")}
        Publishers: {safe_value("publishers")}
        Keywords: {safe_value("keywords")}

        Summary:
        {safe_value("summary")}

        Storyline:
        {safe_value("storyline")}
        """.strip()

    detail_text.insert("1.0", details)
    detail_text.config(state="disabled")
    
def labeled_entry(parent, label, row, col):
    tk.Label(parent, text=label, anchor="w").grid(
        row=row,
        column=col * 2,
        sticky="w",
        padx=(8, 2),
        pady=4
    )
    e = tk.Entry(parent, width=22)
    e.grid(
        row=row,
        column=col * 2 + 1,
        padx=(0, 12),
        pady=4
    )
    return e


def clear():
    global current_results

    for entry in [
        entry_name,
        entry_genre,
        entry_theme,
        entry_platform,
        entry_developer,
        entry_publisher,
        entry_mode,
        entry_rating_min,
        entry_rating_max,
    ]:
        entry.delete(0, tk.END)

    entry_nlp.delete(0, tk.END)
    entry_nlp.insert(0, PLACEHOLDER)
    entry_nlp.config(fg="gray")

    for row in tree.get_children():
        tree.delete(row)

    current_results = None
    count_label.config(text=f"{engine.get_total_count():,} games available")

def on_nlp_focus_in(event):
    if entry_nlp.get() == PLACEHOLDER:
        entry_nlp.delete(0, tk.END)
        entry_nlp.config(fg="black")


def on_nlp_focus_out(event):
    if entry_nlp.get().strip() == "":
        entry_nlp.insert(0, PLACEHOLDER)
        entry_nlp.config(fg="gray")


root = tk.Tk()
root.title("GameSense")
root.geometry("1300x750")
root.resizable(True, True)

# --- Big search bar ---
nlp_frame = tk.Frame(root, padx=12, pady=12)
nlp_frame.pack(fill="x")

entry_nlp = tk.Entry(nlp_frame, font=("Helvetica", 16), fg="gray")
entry_nlp.insert(0, PLACEHOLDER)
entry_nlp.pack(fill="x", ipady=8)

entry_nlp.bind("<FocusIn>", on_nlp_focus_in)
entry_nlp.bind("<FocusOut>", on_nlp_focus_out)

# --- Search fields ---
fields_frame = tk.Frame(root, padx=12, pady=10)
fields_frame.pack(fill="x")

entry_name = labeled_entry(fields_frame, "Name", 0, 0)
entry_genre = labeled_entry(fields_frame, "Genre", 0, 1)
entry_theme = labeled_entry(fields_frame, "Theme", 0, 2)
entry_platform = labeled_entry(fields_frame, "Platform", 0, 3)

entry_developer = labeled_entry(fields_frame, "Developer", 1, 0)
entry_publisher = labeled_entry(fields_frame, "Publisher", 1, 1)
entry_mode = labeled_entry(fields_frame, "Game mode", 1, 2)

tk.Label(fields_frame, text="Rating min", anchor="w").grid(
    row=1,
    column=6,
    sticky="w",
    padx=(8, 2),
    pady=4
)
entry_rating_min = tk.Entry(fields_frame, width=6)
entry_rating_min.grid(row=1, column=7, padx=(0, 4), pady=4)

tk.Label(fields_frame, text="max", anchor="w").grid(
    row=1,
    column=8,
    sticky="w",
    padx=(2, 2),
    pady=4
)
entry_rating_max = tk.Entry(fields_frame, width=6)
entry_rating_max.grid(row=1, column=9, padx=(0, 12), pady=4)

# --- Buttons ---
btn_frame = tk.Frame(root, padx=12, pady=4)
btn_frame.pack(fill="x")

tk.Button(btn_frame, text="Search", command=search, width=12).pack(
    side="left",
    padx=(0, 8)
)
tk.Button(btn_frame, text="Clear", command=clear, width=8).pack(side="left")

count_label = tk.Label(
    btn_frame,
    text=f"{engine.get_total_count():,} games available",
    fg="gray"
)
count_label.pack(side="left", padx=16)

# --- Results table ---
cols = (
    "Name",
    "Genres",
    "Themes",
    "Platforms",
    "Developers",
    "Publishers",
    "Rating",
    "Game modes"
)
col_widths = (180, 160, 130, 160, 140, 160, 60, 160)

tree_frame = tk.Frame(root, padx=12, pady=6)
tree_frame.pack(fill="both", expand=True)

scrollbar_y = tk.Scrollbar(tree_frame, orient="vertical")
scrollbar_x = tk.Scrollbar(tree_frame, orient="horizontal")

tree = ttk.Treeview(
    tree_frame,
    columns=cols,
    show="headings",
    yscrollcommand=scrollbar_y.set,
    xscrollcommand=scrollbar_x.set
)

scrollbar_y.config(command=tree.yview)
scrollbar_x.config(command=tree.xview)

for col, width in zip(cols, col_widths):
    tree.heading(col, text=col)
    tree.column(col, width=width, minwidth=60, anchor="w")

scrollbar_y.pack(side="right", fill="y")
scrollbar_x.pack(side="bottom", fill="x")
tree.pack(fill="both", expand=True)

tree.pack(fill="both", expand=True)
tree.bind("<Double-1>", show_game_details)

root.bind("<Return>", lambda event: search())

root.mainloop()