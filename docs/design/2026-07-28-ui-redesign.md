# UI Redesign — Local Music Matcher

**Date:** 2026-07-28
**Status:** Approved
**Approach:** Hybrid (dashboard rewrite + tab polish + app bar upgrade)

## Color Palette

| Role | Value | Usage |
|---|---|---|
| Background | `#1A1C1E` | Page background |
| Surface | `#2A2D31` | Card / panel backgrounds |
| Surface Hover | `#323539` | Card hover state |
| Accent Green | `#4CAF50` | Primary actions, matched state |
| Accent Blue | `#42A5F5` | Local / folder related |
| Accent Red | `#EF5350` | Unmatched / error state |
| Accent Amber | `#FFC107` | Warning / rate indicator |
| Text Primary | `#FFFFFF` | Headings, bold values |
| Text Body | `#E0E0E0` | Body text |
| Text Muted | `#9E9E9E` | Labels, secondary info |

## App Bar

- Background solid `#2A2D31` with bottom border `1px #3A3D41`
- Left: `music_note` icon (20px, `#4CAF50`) + "Local Music Matcher" (Bold, 18px)
- Right: mini chip `v0.1` (`#3A3D41` bg, `#9E9E9E` text, border-radius 8px)
- Height: 52px, horizontal padding 24px

## Dashboard — Hero Section

- Full-width card (`bgcolor=surface`, `border_radius=16`, padding 32px)
- Background: no gradient, clean surface
- Content: heading "Selamat Datang" (22px Bold, `#FFFFFF`), subtitle (14px, `#E0E0E0`)
- Decorative: large 64px `queue_music` icon in bottom-right corner with low opacity (0.08) as watermark
- Bottom margin 24px

## Dashboard — Stat Cards

- 5 cards in `ResponsiveRow`: col `{"sm": 6, "md": 4, "lg": 2}`
- Card structure: centered Column
  - Icon in circle container (40×40, bg `#FFFFFF` at 8% opacity, border-radius 20px)
  - Value text (28px Bold)
  - Label text (12px, `#9E9E9E`)
- Card container: `bgcolor=surface`, `border_radius=12`, padding 20px, no border
- Hover: slight scale transform (1.02) via `animate_scale` + bg changes to `#323539`
- Colors: Imported=#4CAF50, Lokal=#42A5F5, Matched=#4CAF50, Belum Ada=#EF5350, Match Rate=#FFC107
- Between cards: `run_spacing=12`

## Dashboard — Action Bar

- Section card (`bgcolor=surface`, `border_radius=12`, padding 20px)
- Row of 4 buttons, centered, wrap enabled, spacing 12px
- **Mulai Matching**: `FilledButton` (`bgcolor=#4CAF50`, `color=#FFFFFF`, icon `sync_alt`, height 44px)
- **Import CSV/JSON**: `OutlinedButton` (icon `upload_file`, height 44px)
- **Import Local CSV/JSON**: `OutlinedButton` (icon `library_music`, height 44px)
- **Pilih Folder**: `OutlinedButton` (icon `folder_open`, height 44px)
- Folder label below buttons: italic, 12px, `#9E9E9E`, center-aligned
- Margin above 20px

## Dashboard — Progress

- Row: progress bar (flex=1) + status text
- ProgressBar: `bar_height=6`, `border_radius=3`, `color=#4CAF50`, thumb color `#66BB6A`
- Text: 13px, `#9E9E9E`, min-width 200px for status
- Only visible during scanning/matching; hidden when idle

## Tabs

- `Tabs` with `animation_duration=300`
- Tab labels: "Dashboard", "Matched", "Unmatched Source", "Unmatched Local"
- Indicator color: `#4CAF50`
- Unselected tab text: `#9E9E9E`, selected: `#FFFFFF`
- Label style: 14px medium weight

## Matched & Unmatched Tables

- All tables use `DataTable` inside scroll Container
- Header row: `bgcolor=#1E1E1E`, height 44px, bold 13px headers, sorting icons hidden
- Data rows: alternating — even `bgcolor=transparent`, odd `bgcolor=#FFFFFF` at 3% opacity
- Cells: 13px body, `no_wrap=True`, horizontal_margin=16px
- Hover highlight: row bg changes to `#FFFFFF` at 6% opacity
- Row height: `data_row_max_height=40`

### Pagination
- Bar below table: horizontal divider + row with count on left, navigation on right
- Count: "1–100 of 947" (13px, `#9E9E9E`)
- Navigation: `navigate_before` / `navigate_next` IconButtons, disabled state at bounds
- Margin top 8px

### Search
- `TextField` (350px, label "Cari lagu...", prefix_icon `search`, border radius 8px)
- Right-aligned in top bar row alongside export button (unmatched only)

### Export (Unmatched Source)
- `OutlinedButton` "Export CSV" with `download` icon, height 40px
- Visible only when data exists
- Opens `FilePicker` save dialog

## Empty States

- No data: centered Column with large icon (64px, opacity 0.15) + text "Belum ada data" (14px, `#9E9E9E`) + optional subtitle
- Matched no results after search: icon `search_off` + "Tidak ditemukan"

## Files to Change

| File | Change |
|---|---|
| `src/ui/app.py` | App bar redesign, minor refs update |
| `src/ui/dashboard_tab.py` | Full rewrite: hero, stat cards, action bar, progress |
| `src/ui/matched_tab.py` | Table styling, pagination layout, alternating rows |
| `src/ui/unmatched_tab.py` | Table styling, pagination layout, alternating rows |
