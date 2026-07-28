from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class TrackRecord:
    track_id: str
    artist: str
    title: str
    album: str
    duration_ms: int
    added_at: str
    source_url: str


@dataclass
class LocalTrack:
    filepath: str
    artist: str
    title: str
    album: str
    track_number: int
    duration_ms: int
    file_format: str
    file_size: int


@dataclass
class MatchResult:
    matched: List[Tuple["TrackRecord", LocalTrack]]
    unmatched_source: List["TrackRecord"]
    unmatched_local: List[LocalTrack]

    @property
    def total_source(self) -> int:
        return len(self.matched) + len(self.unmatched_source)

    @property
    def total_local(self) -> int:
        return len(self.matched) + len(self.unmatched_local)

    @property
    def match_percentage(self) -> float:
        if self.total_source == 0:
            return 0.0
        return round(len(self.matched) / self.total_source * 100, 1)
