from typing import Dict, List, Optional, Tuple

from rapidfuzz import fuzz

from .models import LocalTrack, MatchResult, TrackRecord
from .normalizer import Normalizer

# ── matching thresholds ─────────────────────────────────────────────────

# Level 3 (fuzzy artist + title)
ARTIST_SIMILARITY_MIN = 80       # minimum artist token_sort_ratio
TITLE_SIMILARITY_MIN = 75        # minimum title similarity (whichever of ratio/token_sort is higher)
ARTIST_WEIGHT = 0.4              # artist score contribution to combined
TITLE_WEIGHT = 0.4               # title score contribution to combined
COMBINED_MIN = 70.0              # minimum combined score to accept

# duration bonus / penalty (seconds of difference)
DUR_BONUS_EXACT = 10.0           # diff <= 3 s
DUR_BONUS_CLOSE = 5.0            # diff <= 8 s
DUR_PENALTY_MISMATCH = -20.0    # diff > 30 s

# Level 4 (title-only cover version fallback)
COVER_TITLE_MIN = 85.0           # minimum base-title ratio
COVER_DURATION_DIFF_MAX = 30    # max seconds diff to avoid penalty
COVER_COMBINED_MIN = 80.0       # minimum combined score to accept


class Matcher:
    """Multi-level matcher: exact → base-title → fuzzy, with duration verification."""

    def __init__(self) -> None:
        self.norm = Normalizer()

    def _match_levels_1_3(
        self, tr: TrackRecord, used_local: set, remaining_local: List[LocalTrack],
        exact_index: Dict, base_index: Dict,
    ) -> Optional[LocalTrack]:
        """Try Levels 1-3 for a single source track."""
        na = self.norm.normalize_artist(tr.artist)
        nt = self.norm.normalize_title(tr.title)
        bt = self.norm.get_base_title(tr.title)

        # Level 1: exact (normalised)
        key = (na, nt)
        if key in exact_index:
            for cand in exact_index[key]:
                if cand.filepath not in used_local:
                    return cand

        # Level 2: base-title match
        bkey = (na, bt)
        if bkey in base_index:
            for cand in base_index[bkey]:
                if cand.filepath not in used_local:
                    return cand

        # Level 3: fuzzy artist + title
        best_score = 0.0
        best_track: Optional[LocalTrack] = None
        for lt in remaining_local:
            if lt.filepath in used_local:
                continue
            lna = self.norm.normalize_artist(lt.artist)
            lnt = self.norm.normalize_title(lt.title)
            lbt = self.norm.get_base_title(lt.title)

            a_score = fuzz.token_sort_ratio(na, lna)
            if a_score < ARTIST_SIMILARITY_MIN:
                continue

            t_score = fuzz.token_sort_ratio(nt, lnt)
            bt_score = fuzz.ratio(bt, lbt)
            best_t = max(t_score, bt_score)

            if best_t < TITLE_SIMILARITY_MIN:
                continue

            dur_bonus = 0.0
            if tr.duration_ms > 0 and lt.duration_ms > 0:
                diff = abs(tr.duration_ms - lt.duration_ms) / 1000.0
                if diff <= 3:
                    dur_bonus = DUR_BONUS_EXACT
                elif diff <= 8:
                    dur_bonus = DUR_BONUS_CLOSE
                elif diff > 30:
                    dur_bonus = DUR_PENALTY_MISMATCH

            combined = a_score * ARTIST_WEIGHT + best_t * TITLE_WEIGHT + dur_bonus
            if combined > best_score and combined >= COMBINED_MIN:
                best_score = combined
                best_track = lt

        return best_track

    def _match_level_4(
        self, tr: TrackRecord, used_local: set, remaining_local: List[LocalTrack],
    ) -> Optional[LocalTrack]:
        """Level 4: title-only fuzzy matching (cover versions)."""
        bt = self.norm.get_base_title(tr.title)
        best_score = 0.0
        best_track: Optional[LocalTrack] = None

        for lt in remaining_local:
            if lt.filepath in used_local:
                continue
            lbt = self.norm.get_base_title(lt.title)
            t_score = fuzz.ratio(bt, lbt)
            if t_score < COVER_TITLE_MIN:
                continue
            dur_ok = True
            if tr.duration_ms > 0 and lt.duration_ms > 0:
                diff = abs(tr.duration_ms - lt.duration_ms) / 1000.0
                if diff > COVER_DURATION_DIFF_MAX:
                    dur_ok = False
            score = t_score + (5 if dur_ok else -10)
            if score > best_score and score >= COVER_COMBINED_MIN:
                best_score = score
                best_track = lt

        return best_track

    def match(
        self,
        source_tracks: List[TrackRecord],
        local_tracks: List[LocalTrack],
        progress_callback=None,
    ) -> MatchResult:
        # ── build indices ────────────────────────────────────────────────
        exact_index: Dict[Tuple[str, str], List[LocalTrack]] = {}
        base_index: Dict[Tuple[str, str], List[LocalTrack]] = {}

        for lt in local_tracks:
            na = self.norm.normalize_artist(lt.artist)
            nt = self.norm.normalize_title(lt.title)
            bt = self.norm.get_base_title(lt.title)

            exact_index.setdefault((na, nt), []).append(lt)
            base_index.setdefault((na, bt), []).append(lt)

        used_local: set = set()
        remaining_local: List[LocalTrack] = list(local_tracks)
        matched: List[Tuple[TrackRecord, LocalTrack]] = []
        unmatched_source: List[TrackRecord] = []

        total_steps = len(source_tracks) + len(source_tracks)  # Pass 1 + Pass 2 estimate

        # ── Pass 1: Levels 1-3 for ALL source tracks ──
        # Higher-priority matches take local tracks first; Level 4 (cover
        # version fallback) runs separately so it never steals a local track
        # that an earlier-exact-track needs later.
        for i, tr in enumerate(source_tracks):
            if progress_callback:
                progress_callback(i + 1, total_steps)
            match = self._match_levels_1_3(tr, used_local, remaining_local,
                                           exact_index, base_index)
            if match is not None:
                matched.append((tr, match))
                used_local.add(match.filepath)
            else:
                unmatched_source.append(tr)

        # ── Pass 2: Level 4 only for remaining unmatched tracks ──
        still_unmatched: List[TrackRecord] = []
        for i, tr in enumerate(unmatched_source):
            if progress_callback:
                progress_callback(len(source_tracks) + i + 1, total_steps)
            match = self._match_level_4(tr, used_local, remaining_local)
            if match is not None:
                matched.append((tr, match))
                used_local.add(match.filepath)
            else:
                still_unmatched.append(tr)

        # remaining local tracks
        unmatched_local = [lt for lt in local_tracks if lt.filepath not in used_local]

        return MatchResult(
            matched=matched,
            unmatched_source=still_unmatched,
            unmatched_local=unmatched_local,
        )
