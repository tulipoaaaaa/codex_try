"""Simple log file parser utility."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import List, Dict


class LogFileParser:
    """Parse log files into ``dict`` entries."""

    PATTERNS = [
        # [2023-12-01 10:30:45] INFO [Component] Message
        r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(\w+)\s+\[([^\]]+)\]\s+(.*)",
        # 2023-12-01 10:30:45 - INFO - Component - Message
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+-\s+(\w+)\s+-\s+([^\s]+)\s+-\s+(.*)",
        # INFO:Component:Message
        r"(\w+):([^:]+):(.*)",
    ]

    def parse_file(self, file_path: str, max_lines: int = 1000) -> List[Dict[str, str]]:
        """Parse a log file and return list of log entries. Only reads the first max_lines lines."""
        if not os.path.exists(file_path):
            return []
        lines = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh):
                if i >= max_lines:
                    lines.append("... (truncated)")
                    break
                lines.append(line)
        return self.parse_lines(lines)

    def parse_lines(self, lines: List[str]) -> List[Dict[str, str]]:
        entries: List[Dict[str, str]] = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            entry = self._parse_line(line)
            if entry:
                entries.append(entry)
        return entries

    def _parse_line(self, line: str) -> Dict[str, str] | None:
        for pattern in self.PATTERNS:
            match = re.match(pattern, line)
            if match:
                groups = match.groups()
                if len(groups) == 4:
                    timestamp, level, component, message = groups
                elif len(groups) == 3:
                    level, component, message = groups
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    continue
                return {
                    "time": timestamp,
                    "level": level,
                    "component": component,
                    "message": message,
                    "details": "",
                }
        # Fallback for unmatched lines
        return {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": "INFO",
            "component": "Unknown",
            "message": line,
            "details": "",
        }

