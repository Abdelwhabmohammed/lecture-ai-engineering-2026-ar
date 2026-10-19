"""Lecture 01: برنامج يطرح سؤالًا واحدًا على نموذج لغوي كبير دون أدوات.

Usage:
    uv run python -m app.ask "ما هو LoRA؟"
    uv run python -m app.ask            # يطرح سؤالًا خاصًا بالمقرر إذا لم يُحدَّد سؤال

استدعاء مباشر دون أدوات أو سجل للمحادثة.
تحقق مما إذا كان النموذج، عند سؤاله عن معلومات خاصة بالمقرر، يجيب «لا أعرف»
أو يعطي إجابة عامة تبدو معقولة لكنها تختلف عن واقع هذا المقرر.
(في Lecture 03 سنحسّنه ببناء وكيل يستطيع البحث في مسرد المصطلحات.)
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# سؤال خاص بالمقرر. توجد الإجابة الصحيحة في homework-levels داخل data/glossary.json
DEFAULT_QUESTION = "ما مستويات الواجب الثلاثة في مقرر AIE2026؟"


def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    # TODO(تمرين Lecture 01): استخدم response.usage_metadata لعرض
    #   عدد رموز الإدخال والإخراج (يمكنك الاستعانة بـ Copilot)

    return response.text


def main() -> None:
    parser = argparse.ArgumentParser(description="اطرح سؤالًا على نموذج لغوي كبير دون أدوات")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[السؤال] {args.question}\n")
    try:
        print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
