import json
from pathlib import Path

import pytest
from shared_tools.storage.corpus_manager import CorpusManager


class SimpleCorpusManager(CorpusManager):
    """Extend CorpusManager with minimal helpers for testing."""

    def add_document(self, doc_path: Path, corpus_dir: Path) -> Path:
        """Copy a document to the corpus and create a .meta file."""
        dest = self.copy_files([doc_path], corpus_dir)[0]
        meta_path = dest.with_suffix(dest.suffix + ".meta")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump({"filename": dest.name}, fh)
        return dest

    def get_corpus_stats(self, corpus_dir: Path) -> dict:
        """Return simple corpus statistics for PDF files."""
        stats = {"domains": {}, "total_files": 0, "total_size_mb": 0.0}
        for domain_dir in corpus_dir.iterdir():
            if domain_dir.is_dir():
                pdf_files = list(domain_dir.glob("*.pdf"))
                size = sum(f.stat().st_size for f in pdf_files)
                stats["domains"][domain_dir.name] = {
                    "pdf_files": len(pdf_files),
                    "size_mb": round(size / (1024 * 1024), 2),
                }
                stats["total_files"] += len(pdf_files)
                stats["total_size_mb"] += size / (1024 * 1024)
        stats["total_size_mb"] = round(stats["total_size_mb"], 2)
        return stats

def test_add_document_with_sample_metadata(tmp_path):
    """Ensure documents are added and metadata updated."""
    # Create a sample PDF file
    sample = tmp_path / "doc.pdf"
    sample.write_text("dummy")

    manager = SimpleCorpusManager()
    domain_dir = tmp_path / "domain"
    domain_dir.mkdir()

    dest = manager.add_document(sample, domain_dir)

    assert dest.exists()
    meta = dest.with_suffix(dest.suffix + ".meta")
    assert meta.exists()
    with open(meta, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data.get("filename") == dest.name

def test_get_corpus_stats_empty(tmp_path):
    """Verify stats structure when corpus is empty."""
    manager = SimpleCorpusManager()
    stats = manager.get_corpus_stats(tmp_path)

    assert stats == {"domains": {}, "total_files": 0, "total_size_mb": 0.0}
