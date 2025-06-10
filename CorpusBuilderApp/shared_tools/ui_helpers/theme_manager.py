"""Utility for loading QSS theme stylesheets."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_theme(theme_name: str) -> str:
    """Return the stylesheet string for the given theme name."""
    base_dir = Path(__file__).resolve().parents[2] / "app" / "resources" / "styles"
    candidates = [
        base_dir / f"{theme_name}.qss",
        base_dir / f"theme_{theme_name}.qss",
    ]
    for path in candidates:
        if path.exists():
            try:
                return path.read_text(encoding="utf-8")
            except Exception as exc:  # pragma: no cover - file read issues
                logger.exception("Unhandled exception in load_theme: %s", exc)
                return ""
    path = base_dir / f"{theme_name}.qss"
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:  # pragma: no cover - file read issues
        logger.exception("Unhandled exception in load_theme: %s", exc)
        return ""
