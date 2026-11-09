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


def test_make_quiz_uses_a_term_from_the_requested_lecture():
    quiz = json.loads(tools.make_quiz(2))
    matching_terms = [
        term for term in tools.load_glossary() if term["lecture"] == 2
    ]

    assert quiz["question"].startswith("ما معنى ")
    assert any(
        quiz["question"] == f"ما معنى {term['term']}؟"
        and quiz["answer"] == term["definition"]
        for term in matching_terms
    )


def test_make_quiz_handles_a_lecture_without_terms():
    assert "لا توجد مصطلحات" in tools.make_quiz(0)


def test_save_learning_log_writes_json_under_log_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")

    result = tools.save_learning_log("LoRA", "تُبقي الأوزان الأساسية ثابتة.")

    saved_files = list(tools.LOG_DIR.glob("*.json"))
    assert len(saved_files) == 1
    saved = json.loads(saved_files[0].read_text(encoding="utf-8"))
    assert saved["topic"] == "LoRA"
    assert saved["learning"] == "تُبقي الأوزان الأساسية ثابتة."
    assert "learning_log/" in result
