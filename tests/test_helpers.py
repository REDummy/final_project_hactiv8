from __future__ import annotations


def test_parse_top_k_bounds(app_module):
    assert app_module.parse_top_k("abc") == app_module.settings.top_k
    assert app_module.parse_top_k(1) == 2
    assert app_module.parse_top_k(999) == 8


def test_parse_question_count_bounds(app_module):
    assert app_module.parse_question_count(None) == 5
    assert app_module.parse_question_count(0) == 1
    assert app_module.parse_question_count(30) == 10


def test_quality_label_ranges(app_module):
    assert app_module.quality_label(90) == "Excellent"
    assert app_module.quality_label(75) == "Good"
    assert app_module.quality_label(60) == "Needs Improvement"
    assert app_module.quality_label(30) == "Critical"
