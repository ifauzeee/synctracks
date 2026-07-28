# UI Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor 4 Flet UI files to match the approved design spec (minimalist modern, dark theme, green accent, hero+cards layout).

**Architecture:** In-place refactor — files keep their existing class/method structure but visuals are upgraded per the spec color palette and layout. No logic, no threading, no data model changes.

**Tech Stack:** Python 3.12+, Flet 0.25.0 (no tests in project)

---

### Task 1: App Bar & Color Palette

**Files:**
- Modify: `src/ui/app.py:15-44`

- [ ] **Step 1: Add color palette constants as module-level dict**

Add to the top of `src/ui/app.py`, after imports:

```python
# ── design tokens ───────────────────────────────────────────────────
COLORS = {
    "bg": "#1A1C1E",
    "surface": "#2A2D31",
    "surface_hover": "#323539",
    "green": "#4CAF50",
    "blue": "#42A5F5",
    "red": "#EF5350",
    "amber": "#FFC107",
    "text": "#FFFFFF",
    "body": "#E0E0E0",
    "muted": "#9E9E9E",
}
```

- [ ] **Step 2: Redesign app bar in _build_ui()**

Replace the existing app bar Container block (lines 60-71) with:

```python
        app_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            ft.Icon('music_note', size=22, color=COLORS["green"]),
                            ft.Container(width=10),
                            ft.Text("Local Music Matcher", size=18, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.Text("v0.1", size=11, color=COLORS["muted"]),
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        border_radius=8,
                        bgcolor="#3A3D41",
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(horizontal=24, vertical=12),
            bgcolor=COLORS["surface"],
            border=ft.border.only(bottom=ft.BorderSide(1, "#3A3D41")),
            height=56,
        )
```

- [ ] **Step 3: Add `COLORS` to references used in dashboard_tab update**

The existing `_run_matcher` and `_scan_local` don't use colors directly — they use `dashboard._set_card_value()`. No other changes needed in app.py.

- [ ] **Step 4: Verify no compile errors**

Run: `& ".venv\Scripts\python.exe" -m py_compile src/ui/app.py` from `C:\Users\Ifauze\Project\spotify-local-matcher`
Expected: no output (success)

---

### Task 2: Dashboard Tab — Full Rewrite

**Files:**
- Modify: `src/ui/dashboard_tab.py` (replace entire file)

- [ ] **Step 1: Read the current file to confirm what to replace**

Run: `Get-Content src/ui/dashboard_tab.py -Raw | Select-Object -First 5`
Expected: confirms file path and first lines

- [ ] **Step 2: Replace entire dashboard_tab.py**

Write the complete file content below. Key changes from current:
- `_stat_card` now uses icon circle container and hover scale
- `build()` has hero card (welcome), stat card grid, action bar card, progress row
- Import `COLORS` from `.app` module (add `from .app import COLORS`)

```python
from typing import TYPE_CHECKING, Optional

import flet as ft

if TYPE_CHECKING:
    from ..models import MatchResult
    from .app import MusicMatcherApp, COLORS


class DashboardTab:

    CARD_COLORS = {
        "imported": COLORS["green"],
        "local": COLORS["blue"],
        "matched": COLORS["green"],
        "unmatched": COLORS["red"],
        "rate": COLORS["amber"],
    }

    def __init__(self, app: "MusicMatcherApp") -> None:
        self.app = app

        self.imported_card = self._stat_card("Imported", "—", "queue_music", self.CARD_COLORS["imported"])
        self.local_card = self._stat_card("Lokal", "—", "folder", self.CARD_COLORS["local"])
        self.matched_card = self._stat_card("Matched", "—", "check_circle", self.CARD_COLORS["matched"])
        self.unmatched_card = self._stat_card("Belum Ada", "—", "error", self.CARD_COLORS["unmatched"])
        self.rate_card = self._stat_card("Match Rate", "—", "percent", self.CARD_COLORS["rate"])

        self.import_btn = ft.OutlinedButton(
            "Import CSV/JSON",
            icon="upload_file",
            on_click=lambda e: self.app.import_tracks(),
            height=44,
            style=ft.ButtonStyle(color=COLORS["body"]),
        )
        self.folder_btn = ft.OutlinedButton(
            "Pilih Folder Musik",
            icon="folder_open",
            on_click=self.app.select_folder,
            height=44,
            style=ft.ButtonStyle(color=COLORS["body"]),
        )
        self.match_btn = ft.FilledButton(
            "Mulai Matching",
            icon="sync_alt",
            on_click=self.app.start_matching,
            disabled=True,
            height=44,
            style=ft.ButtonStyle(bgcolor=COLORS["green"], color=COLORS["text"]),
        )
        self.local_import_btn = ft.OutlinedButton(
            "Import Local CSV/JSON",
            icon="library_music",
            on_click=lambda e: self.app.import_local_tracks(),
            height=44,
            style=ft.ButtonStyle(color=COLORS["body"]),
        )

        self.progress_bar = ft.ProgressBar(
            value=0, visible=False, color=COLORS["green"],
            bar_height=6, border_radius=3,
        )
        self.progress_text = ft.Text("", size=13, color=COLORS["muted"])
        self._progress_section = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=8),
                    ft.Row(
                        [self.progress_bar, ft.Container(width=12), self.progress_text],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
            ),
            visible=False,
        )
        self.folder_label = ft.Text("", size=12, color=COLORS["muted"], italic=True)

    def build(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    # ── Hero welcome ──
                    self._build_hero(),
                    ft.Container(height=12),
                    # ── Stat cards ──
                    ft.ResponsiveRow(
                        [
                            ft.Container(self.imported_card, col={"sm": 6, "md": 4, "lg": 2}),
                            ft.Container(self.local_card, col={"sm": 6, "md": 4, "lg": 2}),
                            ft.Container(self.matched_card, col={"sm": 6, "md": 4, "lg": 2}),
                            ft.Container(self.unmatched_card, col={"sm": 6, "md": 4, "lg": 2}),
                            ft.Container(self.rate_card, col={"sm": 6, "md": 4, "lg": 2}),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        run_spacing=12,
                    ),
                    ft.Container(height=12),
                    # ── Action bar ──
                    self._build_action_bar(),
                    # ── Progress ──
                    self._progress_section,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.START,
                spacing=0,
            ),
            padding=ft.padding.symmetric(horizontal=40, vertical=28),
            expand=True,
        )

    # ── sub-builders ─────────────────────────────────────────────────

    def _build_hero(self) -> ft.Container:
        return ft.Container(
            content=ft.Stack(
                [
                    ft.Column(
                        [
                            ft.Text("Selamat Datang", size=22, weight=ft.FontWeight.BOLD, color=COLORS["text"]),
                            ft.Container(height=4),
                            ft.Text(
                                "Import daftar lagu dari CSV/JSON dan cocokkan dengan file musik lokal.",
                                size=14, color=COLORS["body"],
                            ),
                        ],
                    ),
                    ft.Container(
                        content=ft.Icon("queue_music", size=64, color=COLORS["green"]),
                        right=0, bottom=0, opacity=0.08,
                    ),
                ],
            ),
            padding=32,
            border_radius=16,
            bgcolor=COLORS["surface"],
            width=1100,
        )

    def _build_action_bar(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [self.import_btn, self.local_import_btn, self.folder_btn, self.match_btn],
                        alignment=ft.MainAxisAlignment.CENTER, spacing=12,
                        wrap=True,
                    ),
                    self.folder_label,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=20,
            border_radius=12,
            bgcolor=COLORS["surface"],
            width=1100,
        )

    # ── stat card ────────────────────────────────────────────────────

    @staticmethod
    def _stat_card(label: str, value: str, icon: str, color: str) -> ft.Container:
        icon_ctrl = ft.Container(
            content=ft.Icon(icon, size=22, color=color),
            width=40, height=40,
            border_radius=20,
            bgcolor=ft.Colors.with_opacity(0.08, "#FFFFFF"),
            alignment=ft.alignment.center,
        )
        value_text = ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color=color)
        label_text = ft.Text(label, size=12, color=COLORS["muted"])

        container = ft.Container(
            content=ft.Column(
                [icon_ctrl, ft.Container(height=4), value_text, ft.Container(height=2), label_text],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=20,
            border_radius=12,
            bgcolor=COLORS["surface"],
            ink=True,
        )
        container.value_text = value_text
        container.icon_ctrl = icon_ctrl
        return container

    # ── updaters ─────────────────────────────────────────────────────

    def _set_card_value(self, card: ft.Container, value: str) -> None:
        card.value_text.value = value

    def _set_card_color(self, card: ft.Container, color: str) -> None:
        card.icon_ctrl.content.color = color
        card.value_text.color = color

    def update_folder_button(self) -> None:
        if self.app.selected_folder:
            parts = self.app.selected_folder.replace("\\", "/").rstrip("/")
            short = "..." + parts[-40:] if len(parts) > 40 else parts
            self.folder_btn.text = short
            self.folder_label.value = f"Folder: {self.app.selected_folder}"
            self.app._check_match_ready()

    def update_stats(self, result: "MatchResult") -> None:
        self._set_card_value(self.imported_card, str(result.total_source))
        self._set_card_value(self.local_card, str(result.total_local))
        self._set_card_value(self.matched_card, str(len(result.matched)))
        self._set_card_value(self.unmatched_card, str(len(result.unmatched_source)))

        rate = result.match_percentage
        self._set_card_value(self.rate_card, f"{rate}%")
        if rate >= 95:
            c = COLORS["green"]
        elif rate >= 80:
            c = COLORS["amber"]
        else:
            c = COLORS["red"]
        self._set_card_color(self.rate_card, c)

    def update_progress(self, current: int, total: int, status: str) -> None:
        if total > 0:
            self.progress_bar.value = current / total
            self.progress_bar.visible = True
        else:
            self.progress_bar.value = 0
            self.progress_bar.visible = False
        self.progress_text.value = f"{status}  ({current}/{total})" if status else ""
        self._progress_section.visible = total > 0

    def update_buttons(self) -> None:
        has_data = bool(self.app.imported_tracks)
        has_local = bool(self.app.local_tracks)
        self.match_btn.disabled = not (has_data and has_local)
```

- [ ] **Step 3: Fix — remove COLORS import from .app to avoid circular import**

The `TYPE_CHECKING` block lets us import `COLORS` only at type-check time. But `COLORS` is used at runtime in `CARD_COLORS` and throughout the file. We need it at runtime.

Better approach: **move `COLORS` dict to its own module** to avoid circular import.

Create `src/theme.py`:

```python
"""Design tokens shared across UI components."""

# ── color palette ───────────────────────────────────────────────────
COLORS = {
    "bg": "#1A1C1E",
    "surface": "#2A2D31",
    "surface_hover": "#323539",
    "green": "#4CAF50",
    "blue": "#42A5F5",
    "red": "#EF5350",
    "amber": "#FFC107",
    "text": "#FFFFFF",
    "body": "#E0E0E0",
    "muted": "#9E9E9E",
}
```

- [ ] **Step 4: Update imports in app.py**

In `src/ui/app.py`, replace the COLORS inline dict with:

```python
from ..theme import COLORS
```

Remove the inline `COLORS = { ... }` dict that was added in Task 1.

- [ ] **Step 5: Update imports in dashboard_tab.py**

Replace `from .app import MusicMatcherApp, COLORS` with:

```python
from ..theme import COLORS
```

- [ ] **Step 6: Verify compile**

Run: `& ".venv\Scripts\python.exe" -m py_compile src/ui/dashboard_tab.py`
Expected: no output

---

### Task 3: Matched Tab — Table Styling

**Files:**
- Modify: `src/ui/matched_tab.py`

- [ ] **Step 1: Redesign table with alternating rows and styled pagination**

Replace the `DataTable` creation (lines 34-45) with:

```python
        self.table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Artist", weight=ft.FontWeight.BOLD, size=13, color=COLORS["body"])),
                ft.DataColumn(ft.Text("Title", weight=ft.FontWeight.BOLD, size=13, color=COLORS["body"])),
                ft.DataColumn(ft.Text("Album", weight=ft.FontWeight.BOLD, size=13, color=COLORS["body"])),
                ft.DataColumn(ft.Text("File", weight=ft.FontWeight.BOLD, size=13, color=COLORS["body"]), numeric=True),
            ],
            rows=[],
            heading_row_height=44,
            heading_row_color="#1E1E1E",
            data_row_max_height=40,
            horizontal_margin=16,
            column_spacing=24,
        )
```

- [ ] **Step 2: Add COLORS import**

Add `from ..theme import COLORS` after the existing imports at the top.

- [ ] **Step 3: Update _render_page() to add alternating rows**

Replace the row-building block inside `_render_page()` (lines 113-124):

```python
        self.table.rows.clear()
        for idx, (sp, local) in enumerate(page_items):
            bg = ft.Colors.with_opacity(0.03, "#FFFFFF") if idx % 2 else None
            fname = local.filepath.split("\\")[-1] if "\\" in local.filepath else local.filepath.split("/")[-1]
            self.table.rows.append(
                ft.DataRow(
                    color=bg,
                    cells=[
                        ft.DataCell(ft.Text(sp.artist, no_wrap=True, size=13)),
                        ft.DataCell(ft.Text(sp.title, no_wrap=True, size=13)),
                        ft.DataCell(ft.Text(sp.album or "—", no_wrap=True, size=13, color=COLORS["muted"])),
                        ft.DataCell(ft.Text(fname, size=12, color=COLORS["muted"], no_wrap=True)),
                    ]
                )
            )
```

- [ ] **Step 4: Restyle info_text and pagination**

Replace the info_text creation (line 20) with:

```python
        self.info_text = ft.Text("Belum ada data. Jalankan matching terlebih dahulu.", size=14, color=COLORS["muted"])
```

Replace the pagination bar in `build()` (lines 63-66) with:

```python
                    ft.Divider(height=1, color=COLORS["surface"]),
                    ft.Container(
                        content=ft.Row(
                            [
                                self.page_label,
                                ft.Container(expand=True),
                                self.prev_btn,
                                self.next_btn,
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ),
```

Replace `page_label.value` in `_render_page()` (line 127):

```python
        self.page_label.value = f"{start + 1}–{end} of {total}" if total else ""
```

- [ ] **Step 5: Style prev/next buttons**

Replace the button creation (line 30-31):

```python
        self.prev_btn = ft.IconButton('navigate_before', on_click=self._prev_page, disabled=True, icon_size=20)
        self.next_btn = ft.IconButton('navigate_next', on_click=self._next_page, disabled=True, icon_size=20)
```

- [ ] **Step 6: Style search_field**

Update (line 22):

```python
        self.search_field = ft.TextField(
            label="Cari lagu...",
            prefix_icon='search',
            on_change=self._on_search,
            width=350, height=48,
            border_radius=8,
            text_size=14,
        )
```

- [ ] **Step 7: Verify compile**

Run: `& ".venv\Scripts\python.exe" -m py_compile src/ui/matched_tab.py`
Expected: no output

---

### Task 4: Unmatched Tab — Table Styling

**Files:**
- Modify: `src/ui/unmatched_tab.py`

- [ ] **Step 1: Add COLORS import and update _TrackTable**

Add to the top: `from ..theme import COLORS`

- [ ] **Step 2: Update DataTable columns and styling**

Replace the `self.table = ft.DataTable(...)` block (lines 57-63) inside `_TrackTable.__init__`:

```python
        self.table = ft.DataTable(
            columns=columns,
            rows=[],
            heading_row_height=44,
            heading_row_color="#1E1E1E",
            data_row_max_height=40,
            horizontal_margin=16,
            column_spacing=24,
        )
```

- [ ] **Step 3: Update search_field style in _TrackTable.__init__**

Replace (lines 47-52):

```python
        self.search_field = ft.TextField(
            label="Cari...",
            prefix_icon='search',
            on_change=self._on_search,
            width=350, height=48,
            border_radius=8,
            text_size=14,
        )
```

- [ ] **Step 4: Update export button style**

Replace (lines 64-68):

```python
        self.export_btn = ft.OutlinedButton(
            "Export CSV",
            icon="download",
            on_click=self._export_csv,
            height=40,
            style=ft.ButtonStyle(color=COLORS["body"]),
        )
```

- [ ] **Step 5: Update pagination nav style**

Replace (lines 53-55):

```python
        self.page_label = ft.Text("", size=13, color=COLORS["muted"])
        self.prev_btn = ft.IconButton('navigate_before', on_click=self._prev_page, disabled=True, icon_size=20)
        self.next_btn = ft.IconButton('navigate_next', on_click=self._next_page, disabled=True, icon_size=20)
```

- [ ] **Step 6: Update _render_page for alternating rows and styled pagination bar**

In `_render_page()` (around line 153), update the row-building loop:

```python
        self.table.rows.clear()
        for idx, item in enumerate(page_items):
            bg = ft.Colors.with_opacity(0.03, "#FFFFFF") if idx % 2 else None
            cells = self._extract_row(item)
            self.table.rows.append(
                ft.DataRow(color=bg, cells=[ft.DataCell(c) for c in cells])
            )
```

Replace the pagination layout in `build()` (around line 80-81) — update to: divider + left/right bar:

```python
                    ft.Divider(height=1, color=COLORS["surface"]),
                    ft.Container(
                        content=ft.Row(
                            [self.page_label, ft.Container(expand=True), self.prev_btn, self.next_btn],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    ),
```

- [ ] **Step 7: Update matches for `COLORS` reference in info_text**

Replace `info_text` init (line 46) with:

```python
        self.info_text = ft.Text("", size=14, color=COLORS["muted"])
```

Leave `_render_page`'s `.value` assignment as-is.

- [ ] **Step 8: Verify compile**

Run: `& ".venv\Scripts\python.exe" -m py_compile src/ui/unmatched_tab.py`
Expected: no output

---

### Task 5: Full Verification

**Files:** (none — just run the app)

- [ ] **Step 1: Verify all imports resolve**

Run from `C:\Users\Ifauze\Project\spotify-local-matcher`:

```bash
& ".venv\Scripts\python.exe" -c "import sys; sys.path.insert(0, '.'); from src.ui.app import MusicMatcherApp; print('ALL IMPORTS OK')"
```

Expected: `ALL IMPORTS OK`

- [ ] **Step 2: Launch and visually inspect**

Run: `& ".venv\Scripts\python.exe" main.py`

Expected: Window opens with:
- Dark app bar with `music_note` icon + "Local Music Matcher" + "v0.1" chip
- Hero welcome card with subtle watermark icon
- 5 stat cards with icon circles: Imported (green), Lokal (blue), Matched (green), Belum Ada (red), Match Rate (amber)
- Action bar card with 4 buttons
- Tabs with green indicator

- [ ] **Step 3: Clean up temp files**

```bash
Remove-Item "C:\Users\Ifauze\AppData\Local\Temp\opencode\_*.py" -ErrorAction SilentlyContinue
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: UI redesign - minimalist modern dark theme with green accent

- Extract COLORS design tokens to src/theme.py
- Dashboard: hero welcome card, stat cards with icon circles, action bar card
- Matched/Unmatched tabs: alternating rows, styled pagination, improved spacing
- App bar: higher, version chip, proper spacing"
```
