import csv
import os
from typing import TYPE_CHECKING, Callable, List

import flet as ft

if TYPE_CHECKING:
    from ..models import MatchResult, TrackRecord, LocalTrack
    from .app import MusicMatcherApp

from ..theme import COLORS


PAGE_SIZE = 100


class _TableModel:
    """Data + filtering for a paginated track table, separate from Flet controls."""

    def __init__(self):
        self.data: list = []
        self.page: int = 0
        self.search: str = ""

    @property
    def filtered(self) -> list:
        if not self.search:
            return self.data
        return [t for t in self.data if self.search in str(t).lower()]

    def search_and_reset(self, term: str) -> None:
        self.search = term.lower().strip()
        self.page = 0


class _TrackTable:
    """Reusable paginated DataTable for track lists."""

    def __init__(
        self,
        app: "MusicMatcherApp",
        columns: List[ft.DataColumn],
        extract_row: Callable,
    ) -> None:
        self.app = app
        self._extract_row = extract_row
        self._model = _TableModel()

        self.info_text = ft.Text("", size=14, color=COLORS["muted"])
        self.search_field = ft.TextField(
            label="Cari...",
            prefix_icon='search',
            on_change=self._on_search,
            width=350, height=48,
            border_radius=8,
            text_size=14,
        )
        self.page_label = ft.Text("", size=13, color=COLORS["muted"])
        self.prev_btn = ft.IconButton('navigate_before', on_click=self._prev_page, disabled=True, icon_size=20)
        self.next_btn = ft.IconButton('navigate_next', on_click=self._next_page, disabled=True, icon_size=20)

        self.table = ft.DataTable(
            columns=columns,
            rows=[],
            heading_row_height=44,
            heading_row_color="#1E1E1E",
            data_row_max_height=40,
            horizontal_margin=16,
            column_spacing=24,
        )
        self.export_btn = ft.OutlinedButton(
            "Export CSV",
            icon="download",
            on_click=self._export_csv,
            height=40,
            style=ft.ButtonStyle(color=COLORS["body"]),
        )

    def build(self) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [self.info_text, ft.Container(expand=True), self.export_btn, ft.Container(width=10), self.search_field],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.Column([self.table], scroll=ft.ScrollMode.AUTO, expand=True),
                    ft.Divider(height=1, color=COLORS["surface"]),
                    ft.Container(
                        content=ft.Row(
                            [self.page_label, ft.Container(expand=True), self.prev_btn, self.next_btn],
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
        self._model.search_and_reset(e.control.value)
        self._render_page()

    def _prev_page(self, e) -> None:
        if self._model.page > 0:
            self._model.page -= 1
            self._render_page()

    def _next_page(self, e) -> None:
        if (self._model.page + 1) * PAGE_SIZE < len(self._model.filtered):
            self._model.page += 1
            self._render_page()

    def _snack(self, msg: str, is_error: bool = False) -> None:
        snack = ft.SnackBar(content=ft.Text(msg), bgcolor=ft.Colors.ERROR if is_error else None, open=True, duration=3000)
        self.app.page.overlay.append(snack)
        self.app.page.update()

    def _export_csv(self, e) -> None:
        if not self._model.data:
            self._snack("Tidak ada data untuk di-export.")
            return

        def on_save(e: ft.FilePickerResultEvent):
            if e.path:
                path = e.path
                if not path.endswith(".csv"):
                    path += ".csv"
                try:
                    self._write_csv(path)
                    self._snack(f"CSV tersimpan: {os.path.basename(path)}")
                except Exception as ex:
                    self._snack(f"Gagal: {ex}", is_error=True)

        picker = ft.FilePicker(on_result=on_save)
        self.app.page.overlay.append(picker)
        self.app.page.update()
        picker.save_file(file_name="unmatched_tracks.csv", allowed_extensions=["csv"])

    def _write_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Artist", "Title", "Album", "Duration (s)", "Source URL"])
            for item in self._model.data:
                if hasattr(item, "artist"):
                    writer.writerow([
                        item.artist,
                        item.title,
                        item.album,
                        round(item.duration_ms / 1000, 1) if item.duration_ms else "",
                        getattr(item, "source_url", ""),
                    ])

    # ── data ─────────────────────────────────────────────────────────────

    def set_data(self, data: list) -> None:
        self._model.data = data
        self._model.page = 0
        self._model.search = ""
        self.search_field.value = ""
        self._render_page()

    def _render_page(self) -> None:
        filtered = self._model.filtered
        total = len(filtered)
        start = self._model.page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total)
        page_items = filtered[start:end]

        self.table.rows.clear()
        for idx, item in enumerate(page_items):
            bg = ft.Colors.with_opacity(0.03, "#FFFFFF") if idx % 2 else None
            cells = self._extract_row(item)
            self.table.rows.append(
                ft.DataRow(color=bg, cells=[ft.DataCell(c) for c in cells])
            )

        self.info_text.value = f"{total} lagu belum ada di lokal" if total else "Semua lagu sudah cocok!"
        self.page_label.value = f"{start + 1}-{end} of {total}" if total else ""
        self.prev_btn.disabled = self._model.page == 0
        self.next_btn.disabled = end >= total
        self.export_btn.visible = total > 0
        self.app.update_ui()


class UnmatchedTab:

    def __init__(self, app: "MusicMatcherApp") -> None:
        columns = [
            ft.DataColumn(ft.Text("Artist", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Title", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Album", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Durasi", weight=ft.FontWeight.BOLD), numeric=True),
        ]

        def extract(sp_track: "TrackRecord") -> list:
            dur = f"{sp_track.duration_ms // 60000}:{(sp_track.duration_ms % 60000) // 1000:02d}" if sp_track.duration_ms else "-"
            return [
                ft.Text(sp_track.artist, no_wrap=True),
                ft.Text(sp_track.title, no_wrap=True),
                ft.Text(sp_track.album or "-", no_wrap=True, color=ft.Colors.GREY_400),
                ft.Text(dur, color=ft.Colors.GREY_400),
            ]

        self.table = _TrackTable(app, columns, extract)

    def build(self) -> ft.Container:
        return self.table.build()

    def update_table(self, result: "MatchResult") -> None:
        self.table.set_data(result.unmatched_source)

    @staticmethod
    def build_local_table(app: "MusicMatcherApp") -> ft.Container:
        columns = [
            ft.DataColumn(ft.Text("Artist", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Title", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Format", weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("Ukuran", weight=ft.FontWeight.BOLD), numeric=True),
        ]

        def extract(local: "LocalTrack") -> list:
            size_mb = local.file_size / (1024 * 1024)
            fname = local.filepath.split("\\")[-1] if "\\" in local.filepath else local.filepath.split("/")[-1]
            return [
                ft.Text(local.artist or "-", no_wrap=True),
                ft.Text(local.title or fname, no_wrap=True),
                ft.Text(local.file_format.upper(), color=ft.Colors.GREY_400),
                ft.Text(f"{size_mb:.1f} MB", color=ft.Colors.GREY_400),
            ]

        tbl = _TrackTable(app, columns, extract)
        tbl.info_text.value = "Belum ada data."
        app._local_unmatched_table = tbl
        return tbl.build()
