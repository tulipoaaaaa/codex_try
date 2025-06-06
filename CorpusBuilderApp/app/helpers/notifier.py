import os
from PySide6.QtWidgets import QSystemTrayIcon
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl

class Notifier:
    success_sound_path = os.path.join("app", "resources", "audio", "success.wav")
    error_sound_path = os.path.join("app", "resources", "audio", "error.wav")

    @staticmethod
    def notify(title: str, message: str, level: str = "info"):
        # System Tray Message
        tray = QSystemTrayIcon()
        tray.setVisible(True)
        icon = QSystemTrayIcon.MessageIcon.Information
        if level == "error":
            icon = QSystemTrayIcon.MessageIcon.Critical
        elif level == "success":
            icon = QSystemTrayIcon.MessageIcon.Information
        elif level == "warning":
            icon = QSystemTrayIcon.MessageIcon.Warning
        tray.showMessage(title, message, icon)

        # Sound Effect
        sound = QSoundEffect()
        if level == "success":
            sound.setSource(QUrl.fromLocalFile(Notifier.success_sound_path))
        elif level == "error":
            sound.setSource(QUrl.fromLocalFile(Notifier.error_sound_path))
        else:
            return
        sound.setVolume(0.8)
        sound.play()


# --- Audio Placeholders ---
# Place these files in:
# app/resources/audio/success.wav
# app/resources/audio/error.wav
# You may replace them with custom audio clips of your choice.
