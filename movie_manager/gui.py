"""Graphical interface for the Movie Manager, built with Tkinter.

Layout:
    [ Search box ] [ field ▼ ] [Search] [Clear]
    ┌──────────── movie table ────────────┐  ┌── details form ──┐
    │ Title | Year | Genre | Director ... │  │ Title / Year ... │
    └─────────────────────────────────────┘  │ [Add] [Save]     │
                                             │ [Delete] [New]   │
    status bar                               └──────────────────┘
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .core import DEFAULT_FILE, MovieCollection, MovieError

COLUMNS = ("title", "year", "genre", "director", "actors")
SEARCH_FIELDS = ("all", "title", "genre", "director", "actors", "year")


class MovieManagerApp(tk.Tk):
    def __init__(self, collection=None):
        super().__init__()
        self.title("Movie Manager")
        self.geometry("1000x520")
        self.minsize(820, 420)

        self.collection = collection or MovieCollection()
        self.selected_title = None   # title of the movie being edited
        self.unsaved = False

        self._build_menu()
        self._build_search_bar()
        self._build_main_area()
        self._build_status_bar()

        self.refresh_table()
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open…", command=self.on_load, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.on_save, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As…", command=self.on_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        self.bind("<Control-s>", lambda e: self.on_save())
        self.bind("<Control-o>", lambda e: self.on_load())
        self.file_path = DEFAULT_FILE

    def _build_search_bar(self):
        bar = ttk.Frame(self, padding=(10, 10, 10, 0))
        bar.pack(fill="x")

        ttk.Label(bar, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.search_var, width=35)
        entry.pack(side="left", padx=5)
        entry.bind("<Return>", lambda e: self.refresh_table())

        ttk.Label(bar, text="in").pack(side="left")
        self.field_var = tk.StringVar(value="all")
        ttk.Combobox(bar, textvariable=self.field_var, values=SEARCH_FIELDS,
                     state="readonly", width=10).pack(side="left", padx=5)

        ttk.Button(bar, text="Search", command=self.refresh_table).pack(side="left", padx=2)
        ttk.Button(bar, text="Show all", command=self.clear_search).pack(side="left", padx=2)

    def _build_main_area(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # --- Details form (right) --- packed first so it never gets squeezed
        form = ttk.LabelFrame(main, text="Movie details", padding=10)
        form.pack(side="right", fill="y", padx=(10, 0))

        self.form_vars = {}
        labels = {
            "title": "Title",
            "year": "Year",
            "genre": "Genre",
            "director": "Director",
            "actors": "Actors (comma separated)",
        }
        for row, (key, label) in enumerate(labels.items()):
            ttk.Label(form, text=label).grid(row=row * 2, column=0, sticky="w", pady=(4, 0))
            var = tk.StringVar()
            ttk.Entry(form, textvariable=var, width=32).grid(row=row * 2 + 1, column=0,
                                                             columnspan=2, sticky="we")
            self.form_vars[key] = var

        buttons = ttk.Frame(form)
        buttons.grid(row=20, column=0, columnspan=2, pady=(15, 0), sticky="we")
        buttons.columnconfigure((0, 1), weight=1)

        ttk.Button(buttons, text="Add movie", command=self.on_add).grid(
            row=0, column=0, sticky="we", padx=2, pady=2)
        self.update_btn = ttk.Button(buttons, text="Save changes", command=self.on_update)
        self.update_btn.grid(row=0, column=1, sticky="we", padx=2, pady=2)
        self.delete_btn = ttk.Button(buttons, text="Delete", command=self.on_delete)
        self.delete_btn.grid(row=1, column=0, sticky="we", padx=2, pady=2)
        ttk.Button(buttons, text="Clear form", command=self.clear_form).grid(
            row=1, column=1, sticky="we", padx=2, pady=2)


        # --- Movie table (left) ---
        table_frame = ttk.Frame(main)
        table_frame.pack(side="left", fill="both", expand=True)

        self.tree = ttk.Treeview(table_frame, columns=COLUMNS, show="headings",
                                 selectmode="browse")
        widths = {"title": 170, "year": 60, "genre": 90, "director": 140, "actors": 260}
        for col in COLUMNS:
            self.tree.heading(col, text=col.capitalize(),
                              command=lambda c=col: self.sort_by(c))
            self.tree.column(col, width=widths[col], anchor="w")
        self.tree.column("year", anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self._set_edit_buttons(False)

    def _build_status_bar(self):
        self.status_var = tk.StringVar()
        ttk.Label(self, textvariable=self.status_var, relief="sunken",
                  anchor="w", padding=(8, 2)).pack(fill="x", side="bottom")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def set_status(self, text):
        self.status_var.set(text)

    def _set_edit_buttons(self, enabled):
        state = "normal" if enabled else "disabled"
        self.update_btn.config(state=state)
        self.delete_btn.config(state=state)

    def _form_values(self):
        return {key: var.get() for key, var in self.form_vars.items()}

    def _mark_changed(self, message):
        self.unsaved = True
        self.title("Movie Manager *")
        self.set_status(message)

    def refresh_table(self, select=None):
        """Redraw the table using the current search filter."""
        self.tree.delete(*self.tree.get_children())
        results = self.collection.search(self.search_var.get(), self.field_var.get())
        for title, d in results.items():
            self.tree.insert("", "end", iid=title, values=(
                title, d["year"], d["genre"], d["director"], ", ".join(d["actors"])))

        total = len(self.collection.movies)
        if self.search_var.get().strip():
            self.set_status(f"{len(results)} of {total} movies match your search.")
        else:
            self.set_status(f"{total} movies in your collection.")

        if select and self.tree.exists(select):
            self.tree.selection_set(select)
            self.tree.see(select)

    def sort_by(self, column):
        """Sort the table when a column heading is clicked (click again to reverse)."""
        rows = [(self.tree.set(iid, column), iid) for iid in self.tree.get_children()]
        reverse = getattr(self, "_sort_state", None) == (column, False)
        key = (lambda r: int(r[0])) if column == "year" else (lambda r: r[0].lower())
        rows.sort(key=key, reverse=reverse)
        for index, (_, iid) in enumerate(rows):
            self.tree.move(iid, "", index)
        self._sort_state = (column, reverse)

    def clear_search(self):
        self.search_var.set("")
        self.field_var.set("all")
        self.refresh_table()

    def clear_form(self):
        for var in self.form_vars.values():
            var.set("")
        self.selected_title = None
        self.tree.selection_remove(self.tree.selection())
        self._set_edit_buttons(False)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        title = selection[0]
        d = self.collection.movies[title]
        self.form_vars["title"].set(title)
        self.form_vars["year"].set(d["year"])
        self.form_vars["genre"].set(d["genre"])
        self.form_vars["director"].set(d["director"])
        self.form_vars["actors"].set(", ".join(d["actors"]))
        self.selected_title = title
        self._set_edit_buttons(True)

    def on_add(self):
        try:
            title = self.collection.add(**self._form_values())
        except MovieError as err:
            messagebox.showerror("Cannot add movie", str(err), parent=self)
            return
        self.clear_form()
        self.refresh_table(select=title)
        self._mark_changed(f'Added "{title}".')

    def on_update(self):
        if not self.selected_title:
            return
        values = self._form_values()
        try:
            new_title = self.collection.edit(
                self.selected_title, values["title"], values["year"],
                values["genre"], values["director"], values["actors"])
        except MovieError as err:
            messagebox.showerror("Cannot save changes", str(err), parent=self)
            return
        self.refresh_table(select=new_title)
        self._mark_changed(f'Updated "{new_title}".')

    def on_delete(self):
        title = self.selected_title
        if not title:
            return
        if not messagebox.askyesno("Delete movie", f'Delete "{title}"?', parent=self):
            return
        self.collection.delete(title)
        self.clear_form()
        self.refresh_table()
        self._mark_changed(f'Deleted "{title}".')

    def on_save(self):
        try:
            self.collection.save(self.file_path)
        except OSError as err:
            messagebox.showerror("Save failed", str(err), parent=self)
            return
        self.unsaved = False
        self.title("Movie Manager")
        self.set_status(f"Saved {len(self.collection.movies)} movies to {self.file_path}")

    def on_save_as(self):
        path = filedialog.asksaveasfilename(
            parent=self, defaultextension=".json",
            filetypes=[("JSON files", "*.json")], initialfile=self.file_path)
        if path:
            self.file_path = path
            self.on_save()

    def on_load(self):
        if self.unsaved and not messagebox.askyesno(
                "Unsaved changes", "Discard unsaved changes and open a file?", parent=self):
            return
        path = filedialog.askopenfilename(
            parent=self, filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            self.collection.load(path)
        except MovieError as err:
            messagebox.showerror("Open failed", str(err), parent=self)
            return
        self.file_path = path
        self.unsaved = False
        self.title("Movie Manager")
        self.clear_form()
        self.clear_search()
        self.set_status(f"Loaded {len(self.collection.movies)} movies from {path}")

    def on_exit(self):
        if self.unsaved:
            answer = messagebox.askyesnocancel(
                "Unsaved changes", "Save your changes before closing?", parent=self)
            if answer is None:       # Cancel
                return
            if answer:               # Yes
                self.on_save()
        self.destroy()


def main():
    collection = MovieCollection()
    # Load saved movies automatically if the default file exists
    try:
        collection.load(DEFAULT_FILE)
    except MovieError:
        pass
    MovieManagerApp(collection).mainloop()


if __name__ == "__main__":
    main()
