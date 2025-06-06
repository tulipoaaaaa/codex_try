from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtCore import QFile, QTextStream, QUrl
from PySide6.QtMultimedia import QSoundEffect
import os
from pathlib import Path

class ThemeManager:
    @staticmethod
    def get_theme_file(theme_name):
        """Get the path to the theme file."""
        # Try both naming conventions
        base_dir = Path(__file__).parent.parent / "resources" / "styles"
        
        # First try theme_name.qss (e.g., dark.qss)
        theme_file = base_dir / f"{theme_name}.qss"
        if theme_file.exists():
            return theme_file
        
        # Then try theme_theme_name.qss (e.g., theme_dark.qss)
        theme_file = base_dir / f"theme_{theme_name}.qss"
        if theme_file.exists():
            return theme_file
            
        # Default fallback
        return base_dir / f"{theme_name}.qss"

    @staticmethod
    def apply_theme(theme_name):
        """Apply the specified theme to the application."""
        app = QApplication.instance()
        if not app:
            print("DEBUG: No QApplication instance found")
            return
            
        print(f"DEBUG: Applying theme: {theme_name}")
        
        # Get the theme file path
        theme_file = ThemeManager.get_theme_file(theme_name)
        print(f"DEBUG: Theme file path: {theme_file}")
        
        if not theme_file.exists():
            print(f"DEBUG: Theme file does not exist: {theme_file}")
            return
            
        try:
            # Read the stylesheet
            with open(theme_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                
            print(f"DEBUG: Read stylesheet, length: {len(stylesheet)}")
            
            # Clear any existing stylesheet first
            app.setStyleSheet("")
            app.processEvents()
            
            # Apply the new stylesheet
            app.setStyleSheet(stylesheet)
            print(f"DEBUG: Stylesheet applied to application")
            
            # Force aggressive refresh
            app.processEvents()
            
            # Force all top-level widgets to refresh
            for widget in app.topLevelWidgets():
                if hasattr(widget, 'setStyleSheet'):
                    # Re-trigger stylesheet processing
                    current_style = widget.styleSheet()
                    widget.setStyleSheet("")
                    widget.setStyleSheet(current_style)
                widget.update()
                widget.repaint()
                    
            print(f"DEBUG: Theme application completed")
            
        except Exception as e:
            print(f"DEBUG: Error applying theme: {e}")
            import traceback
            traceback.print_exc()