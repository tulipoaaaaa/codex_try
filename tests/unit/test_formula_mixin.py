import pytest

from shared_tools.processors.mixins.formula_mixin import FormulaMixin


def test_extracts_latex_and_arithmetic():
    mixin = FormulaMixin()
    text = "The energy formula is $E=mc^2$ while 2+2=4 is trivial."
    formulas = mixin.extract_formulas(text)
    assert "E=mc^2" in formulas
    assert any(f.startswith("2+2") for f in formulas)


def test_deduplicates_results():
    mixin = FormulaMixin()
    text = "$a=b$ and also $a=b$ again"
    formulas = mixin.extract_formulas(text)
    assert formulas.count("a=b") == 1
