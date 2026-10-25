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
import time

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# سؤال خاص بالمقرر. توجد الإجابة الصحيحة في homework-levels داخل data/glossary.json
DEFAULT_QUESTION = "ما مستويات الواجب الثلاثة في مقرر AIE2026؟"

def response_info(response, start_time: float) -> str:
    # معلومات عن عدد الرموز و وقت توليدهم
    return (f"\n[رموز الادخال]{response.usage_metadata.prompt_token_count} "
            f"\n[رموز الاخراج]{response.usage_metadata.candidates_token_count} "
            f"\n[رموز التفكير]{response.usage_metadata.thoughts_token_count} "
            f"\n[عدد الرموز الكلي]{response.usage_metadata.total_token_count} "
            f"\n[الوقت]{(time.time() - start_time) * 1000}ms")

def ask(question: str) -> str:
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(model=MODEL, contents=question)

    # TODO(تمرين Lecture 01): استخدم response.usage_metadata لعرض
    #   عدد رموز الإدخال والإخراج (يمكنك الاستعانة بـ Copilot)
    start_time = time.time()
    return response.text + response_info(response, start_time)

def chat_switch(chat, question: str) -> str:
    start_time = time.time()
    response = chat.send_message(question)
    return response.text + response_info(response, start_time)

def main() -> None:
    parser = argparse.ArgumentParser(description="اطرح سؤالًا على نموذج لغوي كبير دون أدوات")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("--chat", action="store_true", help="ابدأ محادثة مع النموذج")
    args = parser.parse_args()

    print(f"[model] {MODEL}")
    print(f"[السؤال] {args.question}\n")
    try:
        if args.chat:
            client = genai.Client(api_key=get_api_key())
            chat = client.chats.create(model=MODEL)
            print("تم بدء المحادثة. اكتب 'exit' أو 'quit' او 'انهاء' للخروج.")
            print(chat_switch(chat, args.question))
            while True:
                question = input("> ").strip()
                if question in {"", "exit", "quit", "انهاء"}:
                    print("تم إنهاء المحادثة.")
                    break
                print(chat_switch(chat, question))
        else:
            print(ask(args.question))
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
