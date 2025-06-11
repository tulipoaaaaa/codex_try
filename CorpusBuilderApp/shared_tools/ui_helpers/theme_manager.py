"""Utility for loading QSS theme stylesheets."""
import logging
import re
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
                logger.info("Loading QSS from %s", path)
                text = path.read_text(encoding="utf-8")
                # Strip any transform lines
                text = re.sub(r".*transform:.*\n", "", text)
                text = re.sub(r".*text-transform:.*\n", "", text)
                return text
            except Exception as exc:  # pragma: no cover - file read issues
                logger.exception("Unhandled exception in load_theme: %s", exc)
                return ""
    path = base_dir / f"{theme_name}.qss"
    try:
        logger.info("Loading QSS from %s", path)
        text = path.read_text(encoding="utf-8")
        # Strip any transform lines
        text = re.sub(r".*transform:.*\n", "", text)
        text = re.sub(r".*text-transform:.*\n", "", text)
        return text
    except Exception as exc:  # pragma: no cover - file read issues
        logger.exception("Unhandled exception in load_theme: %s", exc)
        return ""
