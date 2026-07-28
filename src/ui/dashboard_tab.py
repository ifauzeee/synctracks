from typing import TYPE_CHECKING, Optional

import flet as ft

if TYPE_CHECKING:
    from ..models import MatchResult
    from .app import MusicMatcherApp

from ..theme import COLORS


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
        self.match_btn = ft.ElevatedButton(
            "Mulai Matching",
            icon="sync_alt",
            on_click=lambda e: self.app.start_matching(),
            disabled=True,
            height=44,
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
