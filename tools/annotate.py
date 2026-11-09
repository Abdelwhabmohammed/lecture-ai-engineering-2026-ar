"""Lecture 04: واجهة لتصنيف مجموعة التقييم (Streamlit).

الاستخدام:
    uv run --with streamlit==1.66.1 streamlit run tools/annotate.py

شغّل Streamlit بإضافته مؤقتًا إلى بيئة المقرر عبر `uv run --with` (دون تغيير pyproject.toml).

- التصنيف: اعرض حالات التقييم (data/eval/lec04_cases.jsonl) واحدة تلو الأخرى، واحفظ أحكام النجاح والإخفاق
  للمعايير الخمسة وعلامة «ترددت» في lectures/04/labels.jsonl
- المقارنة: افحص الاتفاق بين تصنيفاتك وتصنيفات المدرّس (lectures/04/reference/labels_instructor.jsonl)
- إنشاء الأسئلة (الواجب التطبيقي): اكتب الأسئلة والسلوك المتوقع لإنشاء مجموعتك (data/eval/my_cases.jsonl).
  ولّد الإجابات باستخدام وكيلك عبر `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl`
"""

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import tools  # noqa: E402
from app.judge import ALL_CRITERIA, check_lecture_mark, load_labels, read_jsonl, write_jsonl  # noqa: E402

DEFAULT_CASES = ROOT / "data" / "eval" / "lec04_cases.jsonl"
DEFAULT_LABELS = ROOT / "lectures" / "04" / "labels.jsonl"
INSTRUCTOR_LABELS = ROOT / "lectures" / "04" / "reference" / "labels_instructor.jsonl"
MY_CASES = ROOT / "data" / "eval" / "my_cases.jsonl"

CRITERION_HELP = {
    "grounding": "يتفق مع مدخلات المسرد؛ وإذا غابت المعلومة، يصرّح بذلك دون الجزم بها",
    "scope": "يلتزم بدعم التعلم في المقرر ويرفض الأسئلة الخارجة عنه وطلبات «تجاهل التعليمات»",
    "hint": "يقدم تلميحات دون كتابة إجابة الواجب نفسها (تنجح الأسئلة غير المتعلقة بالواجب تلقائيًا)",
    "clarity": "يجيب مباشرة وبإيجاز، وتسهُل قراءة إجابته",
    "lecture_mark": "يوجد «Lecture NN» في النهاية (ستقارن لاحقًا بحكم الشيفرة)",
}

st.set_page_config(page_title="Lecture 04: التصنيف", layout="wide")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def glossary_entries(ids: list[str]) -> list[dict]:
    entries = {e["id"]: e for e in tools.load_glossary()}
    return [entries[i] for i in ids if i in entries]


# ---------------------------------------------------------------- التصنيف
def page_label(cases_path: Path, labels_path: Path) -> None:
    cases = read_jsonl(cases_path)
    if not cases:
        st.error(f"{rel(cases_path)}: لا توجد مجموعة تقييم")
        return
    labels = load_labels(labels_path) if labels_path.exists() else {}

    if "index" not in st.session_state:
        done = [i for i, c in enumerate(cases) if c["id"] in labels]
        st.session_state.index = min(len(done), len(cases) - 1) if done else 0

    i = st.session_state.index
    case = cases[i]
    st.progress((len(labels)) / len(cases), text=f"حُفظت {len(labels)} / {len(cases)} حالات | المعروضة: #{case['id']} (الحالة {i + 1})")

    nav1, nav2, nav3 = st.columns([1, 1, 6])
    if nav1.button("← السابق", disabled=i == 0):
        st.session_state.index = i - 1
        st.rerun()
    if nav2.button("التالي →", disabled=i >= len(cases) - 1):
        st.session_state.index = i + 1
        st.rerun()

    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"#{case['id']} — {case.get('category', '')}")
        st.markdown("**السؤال**")
        st.info(case["question"])
        st.markdown("**الإجابة**")
        st.markdown(case["answer"] or "(لا توجد إجابة بعد. ولّدها باستخدام `app.judge --generate`)")
        st.markdown("**المرجع**")
        ref = case.get("reference", {})
        entries = glossary_entries(ref.get("glossary", []))
        if entries:
            for e in entries:
                st.markdown(f"- **{e['term']}** (Lecture {e['lecture']}): {e['definition']}")
        else:
            st.markdown("- (لا توجد مدخلات في المسرد تقابل هذا السؤال)")
        st.markdown(f"**السلوك المتوقع**：{ref.get('expected', '(غير مذكور)')}")

    with right:
        st.subheader("الحكم")
        st.caption("احكم بالرجوع إلى المرجع والمعايير، لا إلى معرفتك الشخصية. إذا ترددت، فضع علامة «ترددت» وتابع")
        current = labels.get(case["id"], {})
        with st.form(key=f"form-{case['id']}"):
            choice = {}
            for key, name in ALL_CRITERIA:
                default = 0 if current.get(key, "pass") == "pass" else 1
                choice[key] = st.radio(
                    f"{name}", ["نجاح (T)", "إخفاق (F)"], index=default, horizontal=True,
                    help=CRITERION_HELP[key], key=f"{case['id']}-{key}",
                )
            unsure = st.checkbox("ترددت (يصعب الحسم بالمعايير وحدها)", value=bool(current.get("unsure_flag", False)))
            note = st.text_input("ملاحظة (اختيارية)", value=current.get("note", ""))
            submitted = st.form_submit_button("احفظ وانتقل إلى التالي", type="primary")
        if submitted:
            labels[case["id"]] = {
                "id": case["id"],
                **{key: ("pass" if choice[key].startswith("نجاح") else "fail") for key, _ in ALL_CRITERIA},
                "unsure_flag": unsure,
                "note": note,
            }
            write_jsonl(labels_path, [labels[c["id"]] for c in cases if c["id"] in labels])
            if i < len(cases) - 1:
                st.session_state.index = i + 1
            st.rerun()

    if len(labels) >= len(cases):
        st.success(f"{len(cases)} حالات حُفظت كلها → {rel(labels_path)}. قيّمها الآن بنموذج لغوي كبير عبر `uv run python -m app.judge`")
        st.dataframe(
            [{"id": c["id"], **{name: labels[c["id"]][key] for key, name in ALL_CRITERIA},
              "ترددت": labels[c["id"]].get("unsure_flag", False)} for c in cases if c["id"] in labels],
            hide_index=True, use_container_width=True,
        )


# ---------------------------------------------------------------- المقارنة
def page_compare(cases_path: Path, labels_path: Path) -> None:
    if not labels_path.exists():
        st.warning("احفظ تصنيفاتك أولًا في شاشة «التصنيف»")
        return
    if not INSTRUCTOR_LABELS.exists():
        st.warning(f"ملف تصنيفات المدرّس {rel(INSTRUCTOR_LABELS)} غير موجود")
        return
    cases = read_jsonl(cases_path)
    mine, ref = load_labels(labels_path), load_labels(INSTRUCTOR_LABELS)
    ids = [c["id"] for c in cases if c["id"] in mine and c["id"] in ref]
    st.subheader("الاتفاق بين تصنيفاتك وتصنيفات المدرّس")
    st.caption("تصنيفات المدرّس ليست بالضرورة الإجابة الصحيحة؛ غرضها إظهار أن البشر قد يختلفون أيضًا")
    cols = st.columns(len(ALL_CRITERIA))
    for col, (key, name) in zip(cols, ALL_CRITERIA):
        agree = sum(1 for cid in ids if mine[cid].get(key) == ref[cid].get(key))
        col.metric(name, f"{agree}/{len(ids)}")
    code_agree = sum(1 for cid in ids if mine[cid].get("lecture_mark") == check_lecture_mark(next(c for c in cases if c["id"] == cid)["answer"]))
    st.caption(f"يتفق حكمك مع الشيفرة في معيار «ذكر المحاضرة» في {code_agree}/{len(ids)} حالات")
    rows = []
    for cid in ids:
        for key, name in ALL_CRITERIA:
            if mine[cid].get(key) != ref[cid].get(key):
                rows.append({"id": cid, "المعيار": name, "أنا": mine[cid].get(key), "المدرّس": ref[cid].get(key),
                             "ترددت": mine[cid].get("unsure_flag", False), "ملاحظة المدرّس": ref[cid].get("note", "")})
    st.markdown(f"**بنود اختلف الحكم عليها: {len(rows)}**")
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- إنشاء الأسئلة (الواجب التطبيقي)
def page_author(cases_path: Path) -> None:
    st.subheader("أنشئ مجموعة تقييم خاصة بك (الواجب التطبيقي)")
    st.caption("اكتب السؤال و«السلوك المتوقع». ولّد الإجابات باستخدام وكيلك عبر `uv run python -m app.judge --generate --cases "
               f"{rel(cases_path)}`. أضف حالات حدية يُحتمل أن يفشل فيها، إلى جانب الحالات العادية")
    existing = read_jsonl(cases_path) if cases_path.exists() else []
    glossary = tools.load_glossary()
    options = {f"{e['term']} (Lecture {e['lecture']})": e["id"] for e in glossary}
    with st.form("author"):
        question = st.text_area("السؤال", height=80)
        category = st.text_input("الفئة (مثل حالة عادية، مصطلح غائب عن المسرد، خارج المقرر)")
        expected = st.text_area("السلوك المتوقع (جملة أو جملتان)", height=80)
        picked = st.multiselect("مدخلات المسرد المرجعية", list(options))
        submitted = st.form_submit_button("أضف", type="primary")
    if submitted:
        if not question.strip() or not expected.strip():
            st.error("السؤال والسلوك المتوقع مطلوبان")
        else:
            existing.append({
                "id": f"{len(existing) + 1:02d}", "category": category.strip(),
                "question": question.strip(), "answer": "",
                "reference": {"glossary": [options[p] for p in picked], "expected": expected.strip()},
            })
            write_jsonl(cases_path, existing)
            st.success(f"أُضيفت الحالة (المجموع {len(existing)}) → {rel(cases_path)}")
    if existing:
        st.dataframe([{"id": c["id"], "الفئة": c.get("category", ""), "السؤال": c["question"],
                       "توجد إجابة": bool(c.get("answer"))} for c in existing], hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- التنقل بين الشاشات
def main() -> None:
    st.markdown("## Lecture 04: تصنيف مجموعة التقييم")
    with st.sidebar:
        mode = st.radio("الشاشة", ["التصنيف", "المقارنة (مع تصنيفات المدرّس)", "إنشاء الأسئلة (الواجب التطبيقي)"])
        st.divider()
        cases_path = Path(st.text_input("مجموعة التقييم", value=rel(DEFAULT_CASES)))
        labels_path = Path(st.text_input("مسار حفظ التصنيفات", value=rel(DEFAULT_LABELS)))
        my_cases_path = Path(st.text_input("مسار حفظ الأسئلة", value=rel(MY_CASES)))
    cases_path = cases_path if cases_path.is_absolute() else ROOT / cases_path
    labels_path = labels_path if labels_path.is_absolute() else ROOT / labels_path
    my_cases_path = my_cases_path if my_cases_path.is_absolute() else ROOT / my_cases_path

    if mode.startswith("التصنيف"):
        page_label(cases_path, labels_path)
    elif mode.startswith("المقارنة"):
        page_compare(cases_path, labels_path)
    else:
        page_author(my_cases_path)


main()
