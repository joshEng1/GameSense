import tkinter as tk
from tkinter import ttk
import pandas as pd
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "games_25000.csv")

df = pd.read_csv(CSV_PATH, dtype=str)
df["rating_num"] = pd.to_numeric(df["rating"], errors="coerce")


def search():
    name = entry_name.get().strip().lower()
    genre = entry_genre.get().strip().lower()
    theme = entry_theme.get().strip().lower()
    platform = entry_platform.get().strip().lower()
    developer = entry_developer.get().strip().lower()
    publisher = entry_publisher.get().strip().lower()
    game_mode = entry_mode.get().strip().lower()
    rating_min = entry_rating_min.get().strip()
    rating_max = entry_rating_max.get().strip()

    mask = pd.Series([True] * len(df), index=df.index)

    if name:
        mask &= df["name"].str.lower().str.contains(name, na=False)
    if genre:
        mask &= df["genres"].str.lower().str.contains(genre, na=False)
    if theme:
        mask &= df["themes"].str.lower().str.contains(theme, na=False)
    if platform:
        mask &= df["platforms"].str.lower().str.contains(platform, na=False)
    if developer:
        mask &= df["developers"].str.lower().str.contains(developer, na=False)
    if publisher:
        mask &= df["publishers"].str.lower().str.contains(publisher, na=False)
    if game_mode:
        mask &= df["game_modes"].str.lower().str.contains(game_mode, na=False)
    if rating_min:
        try:
            mask &= df["rating_num"] >= float(rating_min)
        except ValueError:
            pass
    if rating_max:
        try:
            mask &= df["rating_num"] <= float(rating_max)
        except ValueError:
            pass

    results = df[mask][["name", "genres", "themes", "platforms", "developers", "publishers", "rating", "game_modes"]].head(100)

    for row in tree.get_children():
        tree.delete(row)

    for _, r in results.iterrows():
        rating = f"{float(r['rating']):.1f}" if pd.notna(r["rating"]) else "N/A"
        tree.insert("", "end", values=(
            r["name"],
            r["genres"] if pd.notna(r["genres"]) else "",
            r["themes"] if pd.notna(r["themes"]) else "",
            r["platforms"] if pd.notna(r["platforms"]) else "",
            r["developers"] if pd.notna(r["developers"]) else "",
            r["publishers"] if pd.notna(r["publishers"]) else "",
            rating,
            r["game_modes"] if pd.notna(r["game_modes"]) else "",
        ))

    count_label.config(text=f"{len(results)} result(s) shown (max 100)")


def clear():
    for entry in [entry_name, entry_genre, entry_theme, entry_platform,
                  entry_developer, entry_publisher, entry_mode,
                  entry_rating_min, entry_rating_max]:
        entry.delete(0, tk.END)
    for row in tree.get_children():
        tree.delete(row)
    count_label.config(text=f"{len(df):,} games available")


root = tk.Tk()
root.title("GameSense")
root.geometry("1300x750")
root.resizable(True, True)

# --- Big search bar ---
PLACEHOLDER = "What kind of game are you looking for?"

nlp_frame = tk.Frame(root, padx=12, pady=12)
nlp_frame.pack(fill="x")

entry_nlp = tk.Entry(nlp_frame, font=("Helvetica", 16), fg="gray")
entry_nlp.insert(0, PLACEHOLDER)
entry_nlp.pack(fill="x", ipady=8)

def on_nlp_focus_in(event):
    if entry_nlp.get() == PLACEHOLDER:
        entry_nlp.delete(0, tk.END)
        entry_nlp.config(fg="black")

def on_nlp_focus_out(event):
    if entry_nlp.get().strip() == "":
        entry_nlp.insert(0, PLACEHOLDER)
        entry_nlp.config(fg="gray")

entry_nlp.bind("<FocusIn>", on_nlp_focus_in)
entry_nlp.bind("<FocusOut>", on_nlp_focus_out)

# --- Search fields ---
fields_frame = tk.Frame(root, padx=12, pady=10)
fields_frame.pack(fill="x")

def labeled_entry(parent, label, row, col):
    tk.Label(parent, text=label, anchor="w").grid(row=row, column=col*2, sticky="w", padx=(8, 2), pady=4)
    e = tk.Entry(parent, width=22)
    e.grid(row=row, column=col*2+1, padx=(0, 12), pady=4)
    return e

entry_name      = labeled_entry(fields_frame, "Name",       0, 0)
entry_genre     = labeled_entry(fields_frame, "Genre",      0, 1)
entry_theme     = labeled_entry(fields_frame, "Theme",      0, 2)
entry_platform  = labeled_entry(fields_frame, "Platform",   0, 3)
entry_developer = labeled_entry(fields_frame, "Developer",  1, 0)
entry_publisher = labeled_entry(fields_frame, "Publisher",  1, 1)
entry_mode      = labeled_entry(fields_frame, "Game mode",  1, 2)

tk.Label(fields_frame, text="Rating min", anchor="w").grid(row=1, column=6, sticky="w", padx=(8, 2), pady=4)
entry_rating_min = tk.Entry(fields_frame, width=6)
entry_rating_min.grid(row=1, column=7, padx=(0, 4), pady=4)

tk.Label(fields_frame, text="max", anchor="w").grid(row=1, column=8, sticky="w", padx=(2, 2), pady=4)
entry_rating_max = tk.Entry(fields_frame, width=6)
entry_rating_max.grid(row=1, column=9, padx=(0, 12), pady=4)

# --- Buttons ---
btn_frame = tk.Frame(root, padx=12, pady=4)
btn_frame.pack(fill="x")
tk.Button(btn_frame, text="Search", command=search, width=12).pack(side="left", padx=(0, 8))
tk.Button(btn_frame, text="Clear", command=clear, width=8).pack(side="left")
count_label = tk.Label(btn_frame, text=f"{len(df):,} games available", fg="gray")
count_label.pack(side="left", padx=16)

# --- Results table ---
cols = ("Name", "Genres", "Themes", "Platforms", "Developers", "Publishers", "Rating", "Game modes")
col_widths = (180, 160, 130, 160, 140, 160, 60, 160)

tree_frame = tk.Frame(root, padx=12, pady=6)
tree_frame.pack(fill="both", expand=True)

scrollbar_y = tk.Scrollbar(tree_frame, orient="vertical")
scrollbar_x = tk.Scrollbar(tree_frame, orient="horizontal")

tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                    yscrollcommand=scrollbar_y.set,
                    xscrollcommand=scrollbar_x.set)

scrollbar_y.config(command=tree.yview)
scrollbar_x.config(command=tree.xview)

for col, width in zip(cols, col_widths):
    tree.heading(col, text=col)
    tree.column(col, width=width, minwidth=60, anchor="w")

scrollbar_y.pack(side="right", fill="y")
scrollbar_x.pack(side="bottom", fill="x")
tree.pack(fill="both", expand=True)

root.bind("<Return>", lambda e: search())

root.mainloop()