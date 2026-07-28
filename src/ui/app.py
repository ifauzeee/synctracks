import threading
from typing import Any, List, Optional

import flet as ft

from ..importer import import_file, import_local_file
from ..local_scanner import LocalScanner
from ..matcher import Matcher
from ..models import LocalTrack, MatchResult, TrackRecord
from ..theme import COLORS
from .dashboard_tab import DashboardTab
from .matched_tab import MatchedTab
from .unmatched_tab import UnmatchedTab


class MusicMatcherApp:
    """Main Flet application — owns state, wires tabs together."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page

        # ── state ────────────────────────────────────────────────────────
        self.imported_tracks: List[TrackRecord] = []
        self.local_tracks: List[LocalTrack] = []
        self.match_result: Optional[MatchResult] = None

        self.selected_folder: str = ""

        self._local_unmatched_table: Any = None

        self._setup_page()
        self._build_ui()

    # ── page setup ──────────────────────────────────────────────────────

    def _setup_page(self) -> None:
        self.page.title = "Local Music Matcher"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window.width = 1400
        self.page.window.height = 900
        self.page.window.min_width = 1000
        self.page.window.min_height = 700
        self.page.padding = 0
        self.page.spacing = 0

    # ── helpers ─────────────────────────────────────────────────────────

    def _snack(self, message: str, is_error: bool = False) -> None:
        snack = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=ft.Colors.ERROR if is_error else None,
            open=True,
            duration=4000,
        )
        self.page.overlay.append(snack)
        self.page.update()

    # ── UI build ────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
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

        self.dashboard = DashboardTab(self)
        self.matched_tab = MatchedTab(self)
        self.unmatched_tab = UnmatchedTab(self)

        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Dashboard",         content=self.dashboard.build()),
                ft.Tab(text="Matched",           content=self.matched_tab.build()),
                ft.Tab(text="Unmatched Source",  content=self.unmatched_tab.build()),
                ft.Tab(text="Unmatched Local",   content=UnmatchedTab.build_local_table(self)),
            ],
            expand=True,
        )

        self.page.add(app_bar, ft.Divider(height=0, thickness=0), self.tabs)

    def update_ui(self) -> None:
        self.page.update()

    def _check_match_ready(self) -> None:
        """Enable match button when both data sources are available."""
        self.dashboard.match_btn.disabled = not (
            bool(self.imported_tracks) and bool(self.local_tracks)
        )

    # ── actions ─────────────────────────────────────────────────────────

    def select_folder(self, e=None) -> None:
        def on_result(e: ft.FilePickerResultEvent):
            if e.path:
                self.selected_folder = e.path
                self.dashboard.update_folder_button()
                self.update_ui()
                self._scan_local()

        picker = ft.FilePicker(on_result=on_result)
        self.page.overlay.append(picker)
        self.page.update()
        picker.get_directory_path()

    def import_tracks(self, e=None) -> None:
        """Open file picker for CSV/JSON and import tracks."""
        def on_result(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                path = e.files[0].path
                try:
                    tracks = import_file(path)
                    if not tracks:
                        self._snack("Tidak ada lagu yang bisa di-import dari file tersebut.", is_error=True)
                        return
                    self.imported_tracks = tracks
                    self.dashboard._set_card_value(self.dashboard.imported_card, str(len(tracks)))
                    self._snack(f"{len(tracks)} lagu berhasil di-import!")
                    self._check_match_ready()
                    self.update_ui()
                except Exception as ex:
                    self._snack(f"Gagal import: {ex}", is_error=True)

        picker = ft.FilePicker(on_result=on_result)
        self.page.overlay.append(picker)
        self.page.update()
        picker.pick_files(allowed_extensions=["csv", "json"], allow_multiple=False)

    def import_local_tracks(self, e=None) -> None:
        """Open file picker for CSV/JSON and import as local tracks."""
        def on_result(e: ft.FilePickerResultEvent):
            if e.files and len(e.files) > 0:
                path = e.files[0].path
                try:
                    tracks = import_local_file(path)
                    if not tracks:
                        self._snack("Tidak ada lagu yang bisa di-import dari file tersebut.", is_error=True)
                        return
                    self.local_tracks = tracks
                    self.dashboard._set_card_value(self.dashboard.local_card, str(len(tracks)))
                    self._snack(f"{len(tracks)} lagu lokal berhasil di-import!")
                    self._check_match_ready()
                    self.update_ui()
                except Exception as ex:
                    self._snack(f"Gagal import: {ex}", is_error=True)

        picker = ft.FilePicker(on_result=on_result)
        self.page.overlay.append(picker)
        self.page.update()
        picker.pick_files(allowed_extensions=["csv", "json"], allow_multiple=False)

    def start_matching(self, e=None) -> None:
        print("start_matching called")
        print(f"  imported_tracks={len(self.imported_tracks) if self.imported_tracks else 0}")
        print(f"  local_tracks={len(self.local_tracks) if self.local_tracks else 0}")
        if self.imported_tracks and self.local_tracks:
            self._run_matcher()

    def _scan_local(self) -> None:
        def progress(curr, total, msg):
            self.dashboard.update_progress(curr, total, f"Scan: {msg}")
            self.update_ui()

        def _scan():
            try:
                self.local_tracks = LocalScanner.scan(self.selected_folder, progress_callback=progress)
                self.dashboard.update_progress(0, 0, "")
                self._snack(f"{len(self.local_tracks)} file musik lokal")
                self.dashboard._set_card_value(self.dashboard.local_card, str(len(self.local_tracks)))
                if self.imported_tracks:
                    self._run_matcher()
            except Exception as ex:
                self.dashboard.update_progress(0, 0, "")
                self._snack(f"Gagal scan: {ex}", is_error=True)
            self.dashboard.update_buttons()
            self.update_ui()

        threading.Thread(target=_scan, daemon=True).start()

    def _run_matcher(self) -> None:
        def progress(curr, total, msg):
            self.dashboard.update_progress(curr, total, msg)
            self.update_ui()

        def _match():
            try:
                progress(0, 1, "Matching...")
                matcher = Matcher()
                result = matcher.match(self.imported_tracks, self.local_tracks)
                self.match_result = result

                self.dashboard.update_stats(result)
                self.matched_tab.update_table(result)
                self.unmatched_tab.update_table(result)
                if self._local_unmatched_table:
                    self._local_unmatched_table.set_data(result.unmatched_local)

                self.dashboard.update_progress(0, 0, "")
                self.dashboard._set_card_value(self.dashboard.matched_card, str(len(result.matched)))
                self.dashboard._set_card_value(self.dashboard.unmatched_card, str(len(result.unmatched_source)))

                self._snack(
                    f"Matching selesai! {len(result.matched)} cocok, "
                    f"{len(result.unmatched_source)} belum ada di lokal."
                )
                if result.unmatched_source:
                    self.tabs.selected_index = 2
            except Exception as ex:
                import traceback
                traceback.print_exc()
                self.dashboard.update_progress(0, 0, "")
                self._snack(f"Matching gagal: {ex}", is_error=True)
            self.update_ui()

        threading.Thread(target=_match, daemon=True).start()
