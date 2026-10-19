"""اختبارات الأدوات (دون استخدام نموذج لغوي كبير أو مفتاح API)."""

import json

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"يتضمن {t['id']} مُعرّفًا غير موجود في related: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "وسم lecNN-start"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("وكيل"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "لم يُعثر" in tools.search_glossary("nonexistent-term-xyz")


def test_lecture_summary():
    assert "وكيل" in tools.get_lecture_summary(3)
    assert "غير متاحة بعد" in tools.get_lecture_summary(99)


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """يستطيع وكيل Lecture 03 الإجابة عن السؤال الافتراضي في Lecture 01 (app.ask) بالاستعانة بالمسرد."""
    from app.ask import DEFAULT_QUESTION

    assert "مستويات الواجب الثلاثة" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("مستويات الواجب الثلاثة"))
    assert hits[0]["term"] == "مستويات الواجب الثلاثة"
