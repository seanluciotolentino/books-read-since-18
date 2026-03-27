# CLAUDE.md

## Project Overview

A personal Streamlit dashboard tracking books read since age 18. The live data source is a Google Sheet ("emmas books"); `books.csv` in the repo is a static snapshot used for reference only — it is **not** read by the app at runtime.

The app is deployed on Streamlit Community Cloud. The `CODEOWNERS` file assigns `@streamlit/community-cloud` as owner of all files.

---

## Repository Structure

```
books-read-since-18/
├── streamlit_app.py       # Single-file app — all logic lives here
├── books.csv              # Static data snapshot (743 books); NOT used at runtime
├── requirements.txt       # Python dependencies
├── .devcontainer/
│   └── devcontainer.json  # GitHub Codespaces / VS Code dev container config
├── .github/
│   └── CODEOWNERS         # Streamlit Community Cloud ownership
└── .gitignore             # Includes .streamlit/secrets.toml (never commit secrets)
```

---

## Tech Stack

| Dependency | Version | Purpose |
|---|---|---|
| `streamlit` | 1.25.0 | Web app framework |
| `pandas` | 2.1.1 | Data manipulation |
| `plotly` | 5.17.0 | Interactive charts |
| `gspread` | 6.1.4 | Google Sheets API client |
| `google-auth` | (transitive) | OAuth2 service account credentials |

Python runtime: **3.11** (per devcontainer image).

---

## Data Source & Secrets

The app reads from a Google Sheet named `"emmas books"` at startup. Authentication uses a Google Cloud service account.

**Required secrets** (in `.streamlit/secrets.toml`, gitignored):

```toml
[google_cloud]
credentials = "<JSON string with service account fields, private_key replaced by placeholder>"

[default]
private_key = "<actual private key PEM string>"
```

The app reconstructs the credentials at runtime:
```python
secrets = json.loads(st.secrets['google_cloud']["credentials"].replace('\n', ''))
secrets['private_key'] = st.secrets['private_key']
```

**Never commit `.streamlit/secrets.toml`.**

---

## Data Schema

The Google Sheet (and `books.csv`) has these columns:

| Column | Type | Notes |
|---|---|---|
| `title` | string | Book title |
| `author` | string | Author name |
| `date read` | datetime | Parsed with `pd.to_datetime` |
| `stars` | int | Rating: 0 (unrated), 1 (liked), 2 (loved) |
| `published_date` | string/int | First publish year, from Open Library |
| `pages` | int | Page count, from Open Library |
| `genre` | string | e.g. fiction, classics, nonfiction, memoir |

`load_data()` filters to `Year Read >= 2012` after parsing.

---

## Key Functions

- **`load_data()`** — Fetches all rows from the Google Sheet, parses types, adds `Year Read` column, filters to 2012+.
- **`add_book(title, author, genre, stars)`** — Queries the Open Library API (`https://openlibrary.org/search.json`) for page count and publish year, returns a dict for the new row. Does **not** write to the sheet itself — the sidebar form handles the write.
- **`classify_fiction_nonfiction(df)`** — Maps `genre` to `'Fiction'` or `'Non-Fiction'`; `nonfiction` and `memoir` genres are treated as Non-Fiction.
- **`metric_with_icon(label, value, icon_key, font_size)`** — Renders a custom styled metric card using inline SVG icons and HTML via `st.markdown(..., unsafe_allow_html=True)`.
- **`local_css()`** — Injects global CSS (Outfit font, dark metric card styles, gradient header).

---

## App Layout

1. **Sidebar** — Form to add a new book (title, author, genre, star rating). On submit: calls Open Library API, appends row to Google Sheet, triggers `st.balloons()`.
2. **Header metrics** — Most recent book (full width), then a 2-column grid: total books, avg books/year, books this year / total pages, avg pages/year, pages this year.
3. **Stacked bar chart** — Books by genre per year (Plotly, dark theme). Yearly totals shown as red scatter labels above bars.
4. **Donut charts** (side by side) — All-time genre breakdown and Fiction vs Non-Fiction split.
5. **Book table** — Searchable (title/author/genre), tabbed by rating (All / Loved / Liked / Unrated), sorted by year descending.

---

## Running Locally

```bash
pip install -r requirements.txt
# Create .streamlit/secrets.toml with Google credentials (see above)
streamlit run streamlit_app.py
```

App runs on `http://localhost:8501`.

### Via Dev Container (Codespaces / VS Code)

The devcontainer auto-installs requirements and starts the app with CORS and XSRF protection disabled (for local preview). Port 8501 is forwarded automatically.

---

## Development Conventions

- **Single file**: All app logic is in `streamlit_app.py`. Do not split into modules unless the file grows significantly.
- **No tests**: There is no test suite. Manual testing via the running app is the current workflow.
- **No linter config**: No `pyproject.toml`, `setup.cfg`, or `.flake8`. Follow PEP 8 conventions informally.
- **Dark theme**: All Plotly charts use `template="plotly_dark"`. Match this in any new charts.
- **Color accent**: Primary accent color is `#FF4B4B` (Streamlit red). Used in chart labels, icon fills, and the gradient header.
- **`unsafe_allow_html=True`**: Used intentionally for custom metric cards and CSS injection. New HTML should be minimal and sanitized.
- **Genre values**: Existing genres in the data are `fiction`, `classics`, `nonfiction`, `memoir`, `other`. When adding new genre-aware logic, account for case-insensitivity and `fillna('other')`.

---

## Google Sheets Integration Notes

- The sheet is written directly via `gspread`: on book addition, the entire sheet is cleared and rewritten (`sheet.clear()` + `sheet.update(...)`). This is a full replace, not an append — be careful with concurrent edits.
- `load_data()` is called once at module load (not inside a cached function). Changes to the sheet require an app rerun to reflect.
- The Google Sheet ID is hardcoded in the sidebar link: `1A534GEJJ9oWsNyHGKcUZPVPoEwfqSxez1ICupdqLWRI`.
