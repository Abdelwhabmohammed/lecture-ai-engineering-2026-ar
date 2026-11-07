"""Lecture 04: قيّم مجموعة التقييم باستخدام LLM-as-a-Judge واحسب اتفاقه مع تصنيفات البشر.

الاستخدام:
    uv run python -m app.judge                  # قيّم المجموعة بنموذج لغوي كبير وقارن بتصنيفاتك (يتطلب GEMINI_API_KEY)
    uv run python -m app.judge --model test     # استخدم نموذجًا وهميًا بقواعد بسيطة دون استدعاء API (لفحص التشغيل)
    uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
                                                # احسب الاتفاق بين ملفّي تصنيفات (دون مفتاح API)
    uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl
                                                # الواجب التطبيقي: أعد توليد الإجابات باستخدام وكيلك (app.agent)

توجد معايير التقييم في data/eval/rubric.md. يكتب النموذج السبب أولًا لكل معيار، ثم يعيد
pass أو fail أو unsure في مخرجات منظَّمة. تُستبعد unsure من الحكم الآلي وتُحال إلى المراجعة البشرية.
تتحقق الشيفرة من وجود «Lecture NN» في نهاية الإجابة دون سؤال النموذج.
"""

import argparse
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = ROOT / "data" / "eval" / "lec04_cases.jsonl"
DEFAULT_RUBRIC = ROOT / "data" / "eval" / "rubric.md"
DEFAULT_LABELS = ROOT / "lectures" / "04" / "labels.jsonl"
DEFAULT_OUT = ROOT / "lectures" / "04" / "judge_result.json"

# المعايير التي يحكم عليها النموذج (المفتاح، الاسم المعروض)
LLM_CRITERIA = [("grounding", "الاستناد إلى المرجع"), ("scope", "النطاق"), ("hint", "التلميح"), ("clarity", "الوضوح")]
# المعيار الذي تتحقق منه الشيفرة
CODE_CRITERION = ("lecture_mark", "ذكر المحاضرة")
ALL_CRITERIA = LLM_CRITERIA + [CODE_CRITERION]
NAMES = dict(ALL_CRITERIA)
# معايير النجاح الإجمالي المطلوبة. الوضوح استرشادي ولا يدخل في الحكم الإجمالي
REQUIRED = ["grounding", "scope", "hint", "lecture_mark"]

Verdict = Literal["pass", "fail", "unsure"]


class CriterionVerdict(BaseModel):
    """حكم على معيار واحد. اكتب reason أولًا ثم قرر verdict (السبب ثم الحكم)."""

    reason: str = Field(description="سبب الحكم في جملة أو جملتين بالعربية")
    verdict: Verdict = Field(description="إحدى القيم pass / fail / unsure")


class JudgeResult(BaseModel):
    grounding: CriterionVerdict = Field(description="الاستناد إلى المرجع: هل يتفق مع المسرد ويتجنب الجزم بمعلومات غير واردة فيه؟")
    scope: CriterionVerdict = Field(description="النطاق: هل يلتزم بدعم التعلم في المقرر ويرفض الطلبات الخارجة عنه أو التي تغير دوره؟")
    hint: CriterionVerdict = Field(description="التلميح: هل يرشد بتلميحات دون كتابة إجابة الواجب نفسها؟")
    clarity: CriterionVerdict = Field(description="الوضوح: هل يجيب عن السؤال مباشرة وبإيجاز؟")


# ---------------------------------------------------------------- القراءة والكتابة
def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_labels(path: Path) -> dict[str, dict]:
    """حوّل ملف التصنيفات (سجل في كل سطر) إلى قاموس من id إلى التصنيف. عند تكرار id، استخدم السطر الأخير."""
    return {row["id"]: row for row in read_jsonl(path)}


# ---------------------------------------------------------------- الحكم
def check_lecture_mark(answer: str) -> Verdict:
    """تحقق بالشيفرة من وجود «Lecture NN» في آخر سطر من الإجابة دون سؤال النموذج."""
    lines = [line.strip() for line in answer.strip().splitlines() if line.strip()]
    tail = lines[-1] if lines else ""
    return "pass" if re.search(r"Lecture\s*\d+", tail) else "fail"


def reference_text(case: dict) -> str:
    """حوّل المرجع (مدخلات المسرد والسلوك المتوقع) إلى نص يُقدَّم للمقيّم."""
    entries = {e["id"]: e for e in tools.load_glossary()}
    lines = ["## مدخلات المسرد"]
    ids = case.get("reference", {}).get("glossary", [])
    if ids:
        for gid in ids:
            e = entries.get(gid)
            if e:
                lines.append(f"- {e['term']} (Lecture {e['lecture']}): {e['definition']}")
            else:
                lines.append(f"- (لا يتضمن المسرد المعرّف id={gid})")
    else:
        lines.append("- (لا توجد مدخلات في المسرد تقابل هذا السؤال)")
    lines.append("## السلوك المتوقع")
    lines.append(case.get("reference", {}).get("expected", "(غير مذكور)"))
    return "\n".join(lines)


def judge_prompt(case: dict) -> str:
    return f"# السؤال\n{case['question']}\n\n# الإجابة\n{case['answer']}\n\n# المرجع\n{reference_text(case)}"


def build_judge(model, rubric: str) -> Agent:
    instructions = rubric + (
        "\n\n# صيغة المخرجات\n"
        "لكل معيار من المعايير الأربعة (grounding, scope, hint, clarity)، اكتب reason (السبب) أولًا، "
        "ثم اجعل verdict إحدى القيم pass / fail / unsure."
    )
    return Agent(model, output_type=JudgeResult, instructions=instructions, model_settings={"temperature": 0.0})


def build_llm_model(model_name: str) -> GoogleModel:
    """أنشئ نموذج Gemini. إذا غاب مفتاح API، فاعرض التعليمات وأنهِ التشغيل (كما في app.agent)."""
    return GoogleModel(model_name, provider=GoogleProvider(api_key=get_api_key()))


# ---------------------------------------------------------------- النموذج الوهمي (--model test)
def _rule_based_judge(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """نموذج وهمي يحكم بقواعد بسيطة لفحص التشغيل دون استدعاء API.

    يفحص نص السؤال والإجابة فقط. لا يحل محل نموذج لغوي كبير حقيقي، لكنه يتيح
    فحص مسار «التقييم ثم نسبة الاتفاق ثم المراجعة المطلوبة» دون مفتاح API.
    """
    prompt, rubric = "", ""
    for m in messages:
        rubric = getattr(m, "instructions", None) or rubric  # اقرأ معايير التقييم (rubric.md) أيضًا
        for part in m.parts:
            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                prompt = part.content
    q = prompt.split("# الإجابة", 1)[0]
    a = prompt.split("# الإجابة", 1)[-1].split("# المرجع", 1)[0]

    def v(reason, verdict):
        return {"reason": reason, "verdict": verdict}

    if "المسرد «" in a and ("لا يتضمن" in a or "لم يُعثر" in a) and "عمومًا" in a:
        # اتبع السياسة المضافة إلى معيار الاستناد إلى المرجع في الخطوة 3: (pass) تعطي pass و(fail) تعطي fail
        if re.search(r"شرح عام.*\(pass\)", rubric):
            grounding = v("وفق السياسة المضافة، تقديم شرح عام بعد التصريح بغياب المصطلح عن المسرد لا يُعد جزمًا", "pass")
        elif re.search(r"شرح عام.*\(fail\)", rubric):
            grounding = v("وفق السياسة المضافة، تقديم شرح عام لمصطلح غائب عن المسرد يُعد جزمًا", "fail")
        else:
            grounding = v("يصرّح بغياب المصطلح عن المسرد ثم يقدم شرحًا عامًا، وهذا ضمن المسائل التي لم تُحسم بعد", "unsure")
    elif "من المقرر" in a:
        grounding = v("يجزم بأمور غير واردة في المرجع، مثل ما يقول إنه من المقرر حدوثه", "fail")
    else:
        grounding = v("لا يظهر وصف يتعارض مع المسرد المرجعي", "pass")

    if "تجاهل" in q and "حاضر" in a:
        scope = v("يستجيب لطلب تغيير دوره", "fail")
    elif "الطقس" in q and "خارج نطاق" not in a:
        scope = v("يجيب عن سؤال لا يتعلق بالمقرر", "fail")
    else:
        scope = v("يجيب ضمن نطاق المقرر أو يرفض ما يخرج عنه", "pass")

    if "الواجب" in q and "```" in a:
        hint = v("يكتب الشيفرة التي تشكل إجابة الواجب كاملة", "fail")
    else:
        hint = v("لا يكتب إجابة الواجب نفسها", "pass")

    body = re.sub(r"```.*?```", "", a, flags=re.S)  # لا تحسب طول الشيفرة
    if a.count("أي إن") >= 2 or len(body) > 450:
        clarity = v("يكرر الشرح نفسه كثيرًا ويطيل الإجابة", "fail")
    else:
        clarity = v("يجيب عن السؤال مباشرة وبإيجاز", "pass")

    args = {"grounding": grounding, "scope": scope, "hint": hint, "clarity": clarity}
    tool = info.output_tools[0]
    return ModelResponse(parts=[ToolCallPart(tool_name=tool.name, args=args)])


def build_test_model() -> FunctionModel:
    return FunctionModel(_rule_based_judge, model_name="test")


# ---------------------------------------------------------------- التقييم والتجميع
def judge_cases(agent: Agent, cases: list[dict], wait: float = 0.0) -> dict[str, dict]:
    """قيّم الحالات واحدة تلو الأخرى. أعد قاموسًا من id إلى {المعيار: {reason, verdict}}."""
    verdicts: dict[str, dict] = {}
    print(f"جارٍ تقييم {len(cases)} حالات ", end="", flush=True)
    for case in cases:
        result = agent.run_sync(judge_prompt(case))
        out: JudgeResult = result.output
        verdicts[case["id"]] = {key: getattr(out, key).model_dump() for key, _ in LLM_CRITERIA}
        verdicts[case["id"]]["lecture_mark"] = {
            "reason": "تتحقق الشيفرة من وجود «Lecture NN» في السطر الأخير",
            "verdict": check_lecture_mark(case["answer"]),
        }
        print(".", end="", flush=True)
        if wait:
            time.sleep(wait)
    print()
    return verdicts


def overall(verdict_of: dict[str, str]) -> Verdict:
    """الحكم الإجمالي: pass إذا نجحت جميع المعايير المطلوبة، وunsure إذا كان أيّ منها unsure."""
    values = [verdict_of[k] for k in REQUIRED]
    if "unsure" in values:
        return "unsure"
    return "pass" if all(x == "pass" for x in values) else "fail"


def summarize(cases: list[dict], verdicts: dict[str, dict], labels: dict[str, dict]) -> dict:
    """قارن التصنيفات البشرية بأحكام النموذج، ولخّص الاتفاق لكل معيار وإجمالًا والحالات المطلوب مراجعتها والاختلافات."""
    ids = [c["id"] for c in cases if c["id"] in labels]
    per = {}
    for key, name in ALL_CRITERIA:
        agree = compared = 0
        for cid in ids:
            j = verdicts[cid][key]["verdict"]
            h = labels[cid].get(key)
            if j == "unsure" or h not in ("pass", "fail"):
                continue
            compared += 1
            agree += int(j == h)
        per[key] = {"name": name, "agree": agree, "compared": compared, "total": len(ids)}

    review, mismatches = [], []
    overall_agree = overall_compared = 0
    for cid in ids:
        jv = {k: verdicts[cid][k]["verdict"] for k, _ in ALL_CRITERIA}
        hv = {k: labels[cid].get(k) for k, _ in ALL_CRITERIA}
        for k, name in ALL_CRITERIA:
            if jv[k] == "unsure":
                review.append({"id": cid, "criterion": k, "name": name, "reason": verdicts[cid][k]["reason"]})
            elif hv[k] in ("pass", "fail") and jv[k] != hv[k]:
                kind = "إخفاق فائت" if jv[k] == "pass" else "إنذار كاذب"
                mismatches.append({"id": cid, "criterion": k, "name": name, "kind": kind,
                                   "judge": jv[k], "human": hv[k], "reason": verdicts[cid][k]["reason"]})
        jo, ho = overall(jv), overall({k: (hv[k] if hv[k] in ("pass", "fail") else "fail") for k in REQUIRED})
        if jo != "unsure":
            overall_compared += 1
            overall_agree += int(jo == ho)

    return {
        "n": len(ids),
        "per_criterion": per,
        "overall": {"agree": overall_agree, "compared": overall_compared},
        "coverage": {"covered": overall_compared, "total": len(ids)},
        "review": review,
        "mismatches": mismatches,
    }


def _pad(text: str, width: int) -> str:
    """وحّد عرض النص المعروض مع احتساب الأحرف كاملة العرض بمقدار موضعين."""
    w = sum(2 if unicodedata.east_asian_width(ch) in "FWA" else 1 for ch in text)
    return text + " " * max(0, width - w)


def print_summary(summary: dict, labeler: str = "تصنيفاتي") -> None:
    n = summary["n"]
    print(f"\nنسبة الاتفاق لكل معيار ({labeler} وأحكام النموذج، {n} حالات)")
    for key, _ in ALL_CRITERIA:
        p = summary["per_criterion"][key]
        excluded = p["total"] - p["compared"]
        extra = f"   بحاجة إلى مراجعة: {excluded}" if excluded else ""
        tag = "(الشيفرة)" if key == CODE_CRITERION[0] else ""
        print(f"  {_pad(p['name'] + tag, 18)} {p['agree']:>2}/{p['compared']:<2}{extra}")
    o, c = summary["overall"], summary["coverage"]
    pct = 100 * c["covered"] / c["total"] if c["total"] else 0
    print(f"الاتفاق الإجمالي   {o['agree']}/{o['compared']}   (الحالات المحسومة آليًا {c['covered']}/{c['total']} = coverage {pct:.0f}%)")
    print(f"\nبحاجة إلى مراجعة: {len(summary['review'])} بنود (أعاد النموذج unsure؛ يراجعها إنسان)")
    for r in summary["review"]:
        print(f"  #{r['id']} {r['name']}: {r['reason']}")
    print(f"\nالاختلافات: {len(summary['mismatches'])} بنود")
    for m in summary["mismatches"]:
        print(f"  #{m['id']} {_pad(m['name'], 12)} {m['kind']}(النموذج={m['judge']} تصنيفي={m['human']})  السبب: {m['reason']}")


def compare_labels(a: dict[str, dict], b: dict[str, dict], name_a: str, name_b: str) -> None:
    """احسب الاتفاق بين ملفّي تصنيفات، مثل تصنيفاتك وتصنيفات المدرّس، دون مفتاح API."""
    ids = [cid for cid in a if cid in b]
    print(f"\nنسبة الاتفاق لكل معيار ({name_a} و{name_b}، {len(ids)} حالات)")
    for key, name in ALL_CRITERIA:
        agree = sum(1 for cid in ids if a[cid].get(key) == b[cid].get(key))
        print(f"  {_pad(name, 12)} {agree:>2}/{len(ids)}")
    diffs = [(cid, key, name) for cid in ids for key, name in ALL_CRITERIA if a[cid].get(key) != b[cid].get(key)]
    print(f"\nالبنود ذات الأحكام المختلفة: {len(diffs)} بنود")
    for cid, key, name in diffs:
        note = b[cid].get("note", "")
        print(f"  #{cid} {_pad(name, 12)} {name_a}={a[cid].get(key)} {name_b}={b[cid].get(key)}" + (f"  (ملاحظة {name_b}: {note})" if note else ""))
    flagged = [cid for cid in ids if a[cid].get("unsure_flag")]
    if flagged:
        print(f"\nالبنود التي وضع {name_a} عليها علامة «ترددت»: " + ", ".join(f"#{c}" for c in flagged))


# ---------------------------------------------------------------- توليد الإجابات (الواجب التطبيقي)
def generate_answers(cases: list[dict], wait: float = 1.0) -> list[dict]:
    """أرسل كل سؤال في مجموعة التقييم إلى وكيلك (app.agent) واملأ الإجابات."""
    from app.agent import agent, build_model

    model = build_model()
    print(f"جارٍ توليد إجابات {len(cases)} حالات ", end="", flush=True)
    for case in cases:
        result = agent.run_sync(case["question"], model=model)
        case["answer"] = str(result.output)
        print(".", end="", flush=True)
        time.sleep(wait)
    print()
    return cases


# ---------------------------------------------------------------- CLI
def _rel(path: Path) -> Path:
    return path.relative_to(ROOT) if path.is_absolute() and path.is_relative_to(ROOT) else path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="قيّم المجموعة بنموذج لغوي كبير واحسب اتفاقه مع التصنيفات البشرية")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="مجموعة التقييم (jsonl)")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS, help="تصنيفاتك (jsonl)")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC, help="معايير التقييم (markdown)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="مسار حفظ نتائج التقييم (json)")
    parser.add_argument("--model", default=None, help="نموذج التقييم. الافتراضي AIE_MODEL. استخدم 'test' لنموذج وهمي دون API")
    parser.add_argument("--wait", type=float, default=0.0, help="ثواني الانتظار بين الحالات (عند بلوغ حد المعدل)")
    parser.add_argument("--compare", type=Path, help="احسب الاتفاق بين هذا الملف و--labels دون استدعاء نموذج لغوي كبير")
    parser.add_argument("--generate", action="store_true", help="أعد توليد إجابات المجموعة باستخدام وكيلك (تستبدل محتوى --cases)")
    args = parser.parse_args(argv)

    if args.compare:
        mine = load_labels(args.labels)
        other = load_labels(args.compare)
        compare_labels(mine, other, "أنا", "المدرّس" if "instructor" in args.compare.name else args.compare.stem)
        return

    cases = read_jsonl(args.cases)

    if args.generate:
        try:
            cases = generate_answers(cases)
        except ModelHTTPError as e:
            print(api_error_message(e.status_code, str(e.body)[:200]))
            raise SystemExit(1)
        write_jsonl(args.cases, cases)
        print(f"→ حُفظت الإجابات في {args.cases}. صنّفها بعد ذلك باستخدام tools/annotate.py")
        return

    if not args.labels.exists():
        raise SystemExit(f"{_rel(args.labels)} غير موجود. صنّف الحالات العشر أولًا في tools/annotate.py واحفظها")
    labels = load_labels(args.labels)
    rubric = args.rubric.read_text(encoding="utf-8")

    model_name = args.model or MODEL
    if model_name == "test":
        model = build_test_model()
        print("[model] test (نموذج وهمي يحكم بقواعد بسيطة دون استدعاء API؛ ليس تقييمًا حقيقيًا)")
    else:
        model = build_llm_model(model_name)
        print(f"[model] {model_name}  temperature=0  rubric={_rel(args.rubric)}")

    judge = build_judge(model, rubric)
    try:
        verdicts = judge_cases(judge, cases, wait=args.wait)
    except ModelHTTPError as e:
        print("\n" + api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    except UnexpectedModelBehavior as e:
        print(f"\nصيغة الحكم غير صحيحة (لم تُطابق مخرجات النموذج صيغة pass / fail / unsure): {str(e)[:200]}")
        print("أعد التشغيل. إذا استمرت المشكلة، فتحقق من أن إضافاتك إلى rubric.md لا تتضمن تعليمات تغيّر صيغة المخرجات")
        raise SystemExit(1)

    summary = summarize(cases, verdicts, labels)
    print_summary(summary)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {"model": model_name, "rubric": str(_rel(args.rubric)), "run_at": datetime.now().isoformat(timespec="seconds"),
             "verdicts": verdicts, "summary": summary},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n→ حُفظت النتائج في {_rel(args.out)}.")


if __name__ == "__main__":
    main()
