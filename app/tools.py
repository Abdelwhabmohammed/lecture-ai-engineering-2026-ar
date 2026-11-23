"""Lecture 03: أدوات الوكيل.

تتحول سلاسل توثيق الدوال وتلميحات أنواعها هنا إلى «أوصاف الأدوات» التي تُعرض على النموذج.
تغيير هذه الأوصاف قد يغير قرار النموذج بشأن استخدام الأداة والوسيطات التي يمررها.
"""

import json
import random
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from uuid import uuid4

from app.config import api_error_message

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_DIR = Path(__file__).resolve().parent.parent / "learning_log"
MAX_RESULTS = 3


@cache
def load_glossary() -> list[dict]:
    with open(DATA_DIR / "glossary.json", encoding="utf-8") as f:
        return json.load(f)["terms"]


def _normalize(text: str) -> str:
    return text.casefold().replace(" ", "").replace("　", "")


def _names(entry: dict) -> list[str]:
    return [_normalize(entry["term"]), _normalize(entry["id"])] + [
        _normalize(a) for a in entry["aliases"]
    ]


def search_glossary(query: str) -> str:
    """ابحث في مسرد المقرر وأعِد التعريفات والمحاضرات التي تتناول المصطلحات.

    استخدمها قبل الإجابة عن مصطلحات هندسة الذكاء الاصطناعي أو الكلمات الخاصة بهذا المقرر (AIE2026).
    عند المقارنة بين مصطلحين، اذكرهما معًا في query (مثل «LoRA وQLoRA»).
    """
    q = _normalize(query)
    if not q:
        return "استعلام البحث فارغ. حدد مصطلحًا واحدًا للبحث عنه."
    glossary = load_glossary()

    exact = [e for e in glossary if q in _names(e)]
    # استبعد الأسماء القصيرة حتى لا تطابق الأسماء البديلة مثل "r" كل شيء
    partial = [
        e for e in glossary
        if e not in exact and any(q in n or (len(n) >= 3 and n in q) for n in _names(e))
    ]
    in_definition = [
        e for e in glossary
        if e not in exact and e not in partial and q in _normalize(e["definition"])
    ]
    hits = (exact + partial + in_definition)[:MAX_RESULTS]

    if not hits:
        return f"لم يُعثر على المصطلح '{query}' في المسرد."
    return json.dumps(
        [
            {
                "term": e["term"],
                "lecture": e["lecture"],
                "definition": e["definition"],
                "related": e["related"],
            }
            for e in hits
        ],
        ensure_ascii=False,
    )


def get_lecture_summary(lecture: int) -> str:
    """أعِد النقاط الرئيسة للمحاضرة المحددة (عدد صحيح يبدأ من 1).

    استخدمها عند السؤال عن محتوى المحاضرة أو الصلات بين المحاضرات، مثل «ماذا سنتعلم في Lecture 03؟».
    """
    path = DATA_DIR / "lectures" / f"{lecture:02d}.md"
    if not path.exists():
        available = sorted(p.stem for p in (DATA_DIR / "lectures").glob("*.md"))
        return f"النقاط الرئيسة لـ Lecture {lecture:02d} غير متاحة بعد. المحاضرات المتاحة: {', '.join(available)}"
    return path.read_text(encoding="utf-8")


def search_materials(query: str) -> str:
    """ابحث في مواد المحاضرات الرئيسة من Lecture 01 إلى Lecture 03، وأعِد نصوص الصفحات ذات الصلة وعناوينها وأرقام صفحاتها.

    حدّد المحتوى الذي تريد البحث عنه في query.
    """
    from google.genai.errors import APIError
    import sqlite3
    from app.retrieval import search

    try:
        return json.dumps({"results": search(query)}, ensure_ascii=False)
    except (ValueError, FileNotFoundError, sqlite3.Error) as e:
        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code), "results": []}, ensure_ascii=False)


def browse_tree(node_id: str | None = None) -> str:
    """أعِد فهرس المحتويات والجملة الأولى من كل صفحة. عند تحديد معرّف صفحة، أعِد نصها الكامل.

    اترك node_id دون تحديد في البداية، ثم تتبّع الفهرس باستخدام المعرّفات المُعادة.
    """
    from app.retrieval import browse_tree as browse

    try:
        return json.dumps(browse(node_id), ensure_ascii=False)
    except (ValueError, OSError) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def search_graph(query: str) -> str:
    """ابحث في المواد، وتتبّع الصفحات السابقة واللاحقة والمصطلحات المشتركة لإعادة نصوص الصفحات ذات الصلة ومعلومات الاستشهاد بها.

    حدّد المحتوى الذي تريد البحث عنه في query.
    """
    import sqlite3
    from google.genai.errors import APIError
    from app.retrieval import search_graph as search

    try:
        return json.dumps(search(query), ensure_ascii=False)
    except (ValueError, OSError, sqlite3.Error) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code)}, ensure_ascii=False)
