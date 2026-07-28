import re
import unicodedata

from typing import List, Tuple

# Remix/version suffix patterns to strip
REMIX_PATTERNS: List[Tuple[str, str]] = [
    (r'\s*[-–—–]\s*(Remaster(?:ed)?|Remix|Live|Radio Edit|Extended Mix|'
     r'Single Version|Album Version|Original Mix|Instrumental|Acoustic|'
     r'Version|Edit)\s*$', ''),
    (r'\s*\((?:Remaster(?:ed)?|Remix|Live|Radio Edit|Extended Mix|'
     r'Single Version|Album Version|Original Mix|Instrumental|Acoustic|'
     r'Version)\)\s*', ' '),
]

BRACKET_RE = re.compile(r'\([^)]*\)|\[[^\]]*\]')


class Normalizer:
    """Text normalizer for music metadata matching.

    Handles: accents, punctuation, feat/ft, remaster/remix labels,
    Indonesian/English artist patterns.
    """

    @staticmethod
    def _strip_accents(s: str) -> str:
        nfkd = unicodedata.normalize('NFKD', s)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    @staticmethod
    def _clean(s: str) -> str:
        s = s.lower().strip()
        s = re.sub(r'[^\w\s\'\-\&]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    @classmethod
    def normalize_artist(cls, artist: str) -> str:
        if not artist:
            return ""
        s = artist.lower().strip()
        s = cls._strip_accents(s)
        s = re.sub(r'^the\s+', '', s)
        s = re.sub(r'\s*/\s*', ' & ', s)
        s = re.sub(r'\s*,\s*', ' & ', s)
        s = cls._clean(s)
        return s

    @classmethod
    def normalize_title(cls, title: str) -> str:
        if not title:
            return ""
        s = title.lower().strip()
        s = cls._strip_accents(s)

        for pattern, replacement in REMIX_PATTERNS:
            s = re.sub(pattern, replacement, s, flags=re.IGNORECASE)

        # Replace feat/ft mentions for cleaner matching
        s = re.sub(r'\s*\(?feat\.?\s+[^)]*\)?', '', s, flags=re.IGNORECASE)
        s = re.sub(r'\s*\(?ft\.?\s+[^)]*\)?', '', s, flags=re.IGNORECASE)

        s = BRACKET_RE.sub(' ', s)
        s = cls._clean(s)
        return s

    @classmethod
    def get_base_title(cls, title: str) -> str:
        """Shortest meaningful title — strips suffixes for broad matching."""
        if not title:
            return ""
        s = title.lower().strip()
        s = re.sub(r'\([^)]*\)', ' ', s)
        s = re.sub(r'\[[^\]]*\]', ' ', s)
        s = re.sub(r'\s*[-–—].*$', '', s)
        s = cls._clean(s)
        return s

    @classmethod
    def normalize_album(cls, album: str) -> str:
        if not album:
            return ""
        s = album.lower().strip()
        s = cls._strip_accents(s)
        s = re.sub(
            r'\s*[-–—]\s*(Single|EP|Remaster(?:ed)?|Deluxe|Edition|Expanded).*$',
            '', s, flags=re.IGNORECASE,
        )
        s = cls._clean(s)
        return s
