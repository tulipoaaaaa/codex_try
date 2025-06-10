import re
from typing import List


class FormulaMixin:
    """Mixin providing lightweight formula extraction via regular expressions."""

    def __init__(self) -> None:
        """Compile commonly used formula patterns."""
        self._patterns = [
            # Inline or display LaTeX
            re.compile(r"\$\$(.+?)\$\$", re.DOTALL),
            re.compile(r"\$(.+?)\$", re.DOTALL),
            # LaTeX equation/align environments
            re.compile(r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}", re.DOTALL),
            re.compile(r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}", re.DOTALL),
            # Simple arithmetic expressions like 1+2=3
            re.compile(r"\b\d+(?:\s*[+\-*/]\s*\d+)+(?:\s*=\s*\d+)?\b"),
        ]

    def extract_formulas(self, text: str) -> List[str]:
        """Return a list of formulas detected in ``text``."""
        formulas: List[str] = []

        for pattern in self._patterns:
            for match in pattern.finditer(text):
                if match.groups():
                    formulas.append(match.group(1).strip())
                else:
                    formulas.append(match.group(0).strip())

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for f in formulas:
            if f not in seen:
                seen.add(f)
                unique.append(f)

        return unique
