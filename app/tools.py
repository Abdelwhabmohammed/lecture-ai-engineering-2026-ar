"""Lecture 03: أدوات الوكيل.

تتحول سلاسل توثيق الدوال وتلميحات أنواعها هنا إلى «أوصاف الأدوات» التي تُعرض على النموذج.
تغيير هذه الأوصاف قد يغير قرار النموذج بشأن استخدام الأداة والوسيطات التي يمررها.
"""

import json
from functools import cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
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
    ضع مصطلحًا واحدًا فقط في query (مثل «LoRA»).
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
