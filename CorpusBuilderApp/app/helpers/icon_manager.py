import os
import csv
from typing import Optional, Dict, List

ICON_CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icons', 'crypto_finance_icons_catalog.csv')
ICON_DIR = os.path.join(os.path.dirname(__file__), '..', 'resources', 'icons')

class IconManager:
    def __init__(self):
        self.icons = self._load_icons()

    def _load_icons(self) -> List[Dict[str, str]]:
        icons = []
        with open(ICON_CSV_PATH, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                icons.append(row)
        return icons

    def get_icon_path(self, key: str, by: str = 'Function') -> Optional[str]:
        """
        Get the local file path for an icon by function, description, or filename.
        by: 'Function', 'Description', or 'Filename'
        """
        for icon in self.icons:
            if icon.get(by, '').lower() == key.lower():
                filename = icon['Filename']
                path = os.path.join(ICON_DIR, filename)
                if os.path.exists(path):
                    return path
        return None

    def list_icons(self) -> List[Dict[str, str]]:
        """Return all icon metadata as a list of dicts."""
        return self.icons

# Example usage:
# icon_manager = IconManager()
# print(icon_manager.list_icons())
# print(icon_manager.get_icon_path('Main dashboard and analytics view', by='Function')) 