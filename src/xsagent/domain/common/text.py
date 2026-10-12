import re

_BIBLE_SECTIONS = frozenset({"characters", "plot", "world", "notes", "timeline"})


def is_valid_bible_section(section: str) -> bool:
    return section in _BIBLE_SECTIONS


def bible_sections() -> list[str]:
    return sorted(_BIBLE_SECTIONS)


def count_words(text: str) -> int:
    """中文字数统计：去除空白后的字符数。"""
    stripped = re.sub(r"\s+", "", text)
    return len(stripped)


def chapter_id_from_filename(filename: str) -> str:
    return filename.removesuffix(".md")


def parse_chapter_title(content_md: str, fallback: str) -> str:
    for line in content_md.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback
