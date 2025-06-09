from datetime import datetime

import pytest

from CorpusBuilderApp.shared_tools.utils import log_file_parser


class DummyDateTime:
    const_dt = datetime(2023, 1, 1, 12, 0, 0)

    @classmethod
    def now(cls):
        return cls.const_dt


def test_parse_lines_empty():
    parser = log_file_parser.LogFileParser()
    assert parser.parse_lines([]) == []
    assert parser.parse_lines(["", "   "]) == []


def test_parse_lines_valid_formats(monkeypatch):
    parser = log_file_parser.LogFileParser()
    monkeypatch.setattr(log_file_parser, "datetime", DummyDateTime)
    lines = [
        "[2023-12-01 10:30:45] INFO [Comp] hello",
        "2023-12-02 11:31:46 - WARNING - Mod - world",
        "ERROR:Bad:boom",
    ]
    entries = parser.parse_lines(lines)
    assert entries[0] == {
        "time": "2023-12-01 10:30:45",
        "level": "INFO",
        "component": "Comp",
        "message": "hello",
        "details": "",
    }
    assert entries[1] == {
        "time": "2023-12-02 11:31:46",
        "level": "WARNING",
        "component": "Mod",
        "message": "world",
        "details": "",
    }
    assert entries[2]["level"] == "ERROR"
    assert entries[2]["component"] == "Bad"
    assert entries[2]["message"] == "boom"
    assert entries[2]["time"] == DummyDateTime.const_dt.strftime("%Y-%m-%d %H:%M:%S")


def test_parse_lines_malformed(monkeypatch):
    parser = log_file_parser.LogFileParser()
    monkeypatch.setattr(log_file_parser, "datetime", DummyDateTime)
    entries = parser.parse_lines(["not a log line"])
    assert len(entries) == 1
    assert entries[0]["component"] == "Unknown"
    assert entries[0]["message"] == "not a log line"


def test_parse_file_missing(tmp_path):
    parser = log_file_parser.LogFileParser()
    path = tmp_path / "nonexist.log"
    assert parser.parse_file(str(path)) == []
