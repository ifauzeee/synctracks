from typing import TYPE_CHECKING, List, Tuple

import flet as ft

if TYPE_CHECKING:
    from ..models import MatchResult, TrackRecord, LocalTrack
    from .app import MusicMatcherApp

from ..theme import COLORS

PAGE_SIZE = 100


class MatchedTab:

    def __init__(self, app: "MusicMatcherApp") -> None:
        self.app = app
        self._data: List[Tuple["TrackRecord", "LocalTrack"]] = []
        self._page = 0
        self._search = ""

        self.info_text = ft.Text("Belum ada data. Jalankan matching terlebih dahulu.", size=14, color=COLORS["muted"])

        self.search_field = ft.TextField(
            label="Cari lagu...",
            prefix_icon='search',
            on_change=self._on_search,
            width=350, height=48,
            border_radius=8,
            text_size=14,
        )

        self.page_label = ft.Text("", size=13, color=COLORS["muted"])
        self.prev_btn = ft.IconButton('navigate_before', on_click=self._prev_page, disabled=True, icon_size=20)
        self.next_btn = ft.IconButton('navigate_next', on_click=self._next_page, disabled=True, icon_size=20)

        # table
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

    def build(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [self.info_text, ft.Container(expand=True), self.search_field],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.Column(
                        [self.table],
                        scroll=ft.ScrollMode.AUTO,
                        expand=True,
                    ),
                    ft.Container(height=5),
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
                ],
                expand=True,
            ),
            padding=20,
            expand=True,
        )

    # ── handlers ────────────────────────────────────────────────────────

    def _on_search(self, e) -> None:
        self._search = e.control.value.lower().strip()
        self._page = 0
        self._render_page()

    def _prev_page(self, e) -> None:
        if self._page > 0:
            self._page -= 1
            self._render_page()

    def _next_page(self, e) -> None:
        total = len(self._filtered())
        if (self._page + 1) * PAGE_SIZE < total:
            self._page += 1
            self._render_page()

    # ── data ─────────────────────────────────────────────────────────────

    def _filtered(self) -> List[Tuple["TrackRecord", "LocalTrack"]]:
        if not self._search:
            return self._data
        return [
            (s, l) for s, l in self._data
            if self._search in s.artist.lower()
            or self._search in s.title.lower()
            or self._search in l.artist.lower()
            or self._search in l.title.lower()
        ]

    def _render_page(self) -> None:
        filtered = self._filtered()
        total = len(filtered)
        start = self._page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total)
        page_items = filtered[start:end]

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

        self.info_text.value = f"✅ {len(self._data)} lagu cocok" if self._data else "Belum ada data."
        self.page_label.value = f"{start + 1}–{end} of {total}" if total else ""
        self.prev_btn.disabled = self._page == 0
        self.next_btn.disabled = end >= total
        self.app.update_ui()

    def update_table(self, result: "MatchResult") -> None:
        self._data = result.matched
        self._page = 0
        self._search = ""
        self.search_field.value = ""
        self._render_page()
