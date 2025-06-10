import os
import shutil
import time
import logging
from pathlib import Path
from typing import List
from PySide6.QtCore import QObject, Signal as pyqtSignal

class SignalEmitter(QObject):
    """Base class providing progress, status and completion signals."""
    progress_updated = pyqtSignal(int, str, dict)
    status_updated = pyqtSignal(str)
    operation_completed = pyqtSignal(str)  # Signal emitted when an operation is completed

class CorpusManager(SignalEmitter):
    """Backend class for common corpus file operations."""

    def __init__(self, logger: logging.Logger | None = None):
        super().__init__()
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    # Helper utilities -----------------------------------------------------
    def validate_path(self, path: str | Path, must_exist: bool = True) -> Path:
        """Return Path object and verify existence if required."""
        p = Path(path)
        if must_exist and not p.exists():
            raise FileNotFoundError(f"Path does not exist: {p}")
        return p

    def safe_overwrite(self, target: Path, overwrite: bool, rename_conflicts: bool) -> Path:
        """Handle existing target according to overwrite settings."""
        if target.exists():
            if overwrite:
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            elif rename_conflicts:
                base, ext = target.stem, target.suffix
                counter = 1
                new_target = target
                while new_target.exists():
                    new_target = target.with_name(f"{base}_{counter}{ext}")
                    counter += 1
                target = new_target
            else:
                raise FileExistsError(f"Target {target} already exists")
        return target

    def log_action(self, message: str):
        self.logger.info(message)

    # Public API -----------------------------------------------------------
    def copy_files(self, files: List[str | Path], target_dir: str | Path,
                   overwrite: bool = False, rename_conflicts: bool = True) -> List[Path]:
        dest_dir = self.validate_path(target_dir, must_exist=False)
        dest_dir.mkdir(parents=True, exist_ok=True)
        results: List[Path] = []
        total = len(files)
        for idx, file_path in enumerate(files, 1):
            src = self.validate_path(file_path)
            dest = dest_dir / src.name
            dest = self.safe_overwrite(dest, overwrite, rename_conflicts)
            shutil.copy2(src, dest)
            results.append(dest)
            self.log_action(f"Copied {src} to {dest}")
            progress = int((idx / total) * 100)
            self.progress_updated.emit(progress, f"Copying: {src.name}", {})
        self.status_updated.emit("Copy completed")
        self.operation_completed.emit("copy")
        return results

    def move_files(self, files: List[str | Path], target_dir: str | Path,
                   overwrite: bool = False, rename_conflicts: bool = True) -> List[Path]:
        dest_dir = self.validate_path(target_dir, must_exist=False)
        dest_dir.mkdir(parents=True, exist_ok=True)
        results: List[Path] = []
        total = len(files)
        for idx, file_path in enumerate(files, 1):
            src = self.validate_path(file_path)
            dest = dest_dir / src.name
            dest = self.safe_overwrite(dest, overwrite, rename_conflicts)
            shutil.move(src, dest)
            results.append(dest)
            self.log_action(f"Moved {src} to {dest}")
            progress = int((idx / total) * 100)
            self.progress_updated.emit(progress, f"Moving: {src.name}", {})
        self.status_updated.emit("Move completed")
        self.operation_completed.emit("move")
        return results

    def rename_files(self, files: List[str | Path], pattern: str,
                     overwrite: bool = False, rename_conflicts: bool = True) -> List[Path]:
        results: List[Path] = []
        total = len(files)
        for idx, file_path in enumerate(files, 1):
            src = self.validate_path(file_path)
            dir_path = src.parent
            base, ext = src.stem, src.suffix
            new_name = pattern.format(index=idx, original=base, extension=ext[1:],
                                     date=time.strftime("%Y%m%d"))
            dest = dir_path / new_name
            dest = self.safe_overwrite(dest, overwrite, rename_conflicts)
            src.rename(dest)
            results.append(dest)
            self.log_action(f"Renamed {src} to {dest}")
            progress = int((idx / total) * 100)
            self.progress_updated.emit(progress, f"Renaming: {src.name}", {})
        self.status_updated.emit("Rename completed")
        self.operation_completed.emit("rename")
        return results

    def delete_files(self, files: List[str | Path]) -> int:
        count = 0
        for file_path in files:
            path = self.validate_path(file_path)
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            count += 1
            self.log_action(f"Deleted {path}")
        self.status_updated.emit("Delete completed")
        self.operation_completed.emit("delete")
        return count

    def organize_files(self, files: List[str | Path], criteria: str = "extension",
                       overwrite: bool = False, rename_conflicts: bool = True) -> List[Path]:
        results: List[Path] = []
        total = len(files)
        for idx, file_path in enumerate(files, 1):
            src = self.validate_path(file_path)
            dir_path = src.parent
            if criteria == "extension":
                subdir = src.suffix[1:].upper() if src.suffix else "NO_EXTENSION"
            elif criteria == "date":
                mtime = src.stat().st_mtime
                subdir = time.strftime("%Y-%m", time.localtime(mtime))
            else:
                subdir = "OTHER"
            target_dir = dir_path / subdir
            target_dir.mkdir(exist_ok=True)
            dest = target_dir / src.name
            dest = self.safe_overwrite(dest, overwrite, rename_conflicts)
            shutil.move(src, dest)
            results.append(dest)
            self.log_action(f"Organized {src} into {target_dir}")
            progress = int((idx / total) * 100)
            self.progress_updated.emit(progress, f"Organizing: {src.name}", {})
        self.status_updated.emit("Organize completed")
        self.operation_completed.emit("organize")
        return results