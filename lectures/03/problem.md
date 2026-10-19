# تمارين وواجبات Lecture 03: بناء وكيل لدعم التعلم

## أهداف هذه المحاضرة

- تحقق في شيفرتك من أن الوكيل يتكون من «نموذج + حلقة + أدوات»
- اقرأ الأدوات المستدعاة والوسيطات التي استُخدمت معها
- أضف أداة واحدة

## التحضير

إذا أكملت أعمال المحاضرات السابقة، فأنشئ الفرع `lec03` من `main`.

```bash
git switch main && git switch -c lec03
```

وإلا فيمكنك إنشاء فرع من شيفرة البداية في مستودع المقرر (الوسم `lec03-start`).

```bash
git remote -v                     # إذا لم يكن upstream موجودًا، فأضفه بالسطر التالي
git remote add upstream https://github.com/matsuolab/lecture-ai-engineering-2026.git
git fetch upstream --tags
git switch -c lec03 lec03-start
```

## التمارين (30 دقيقة)

### 1. اسأل الوكيل السؤال نفسه المستخدم في Lecture 01

```bash
uv run python -m app.agent "ما وسم lecNN-start في مقرر AIE2026؟"
```

قارن الإجابة بإجابة `app.ask` في Lecture 01.

### 2. اقرأ استدعاءات الأدوات

```bash
uv run python -m app.agent --trace "ما الفرق بين LoRA وQLoRA؟"
```

في أسطر `[tool call]`، افحص الأدوات التي استدعاها النموذج والوسيطات المستخدمة. تعرض `requests` ضمن `[usage]` عدد استدعاءات النموذج اللغوي الكبير للسؤال الواحد.

### 3. أضف أداة واحدة

أضف `make_quiz` إلى `app/tools.py` وسجّلها عند `TODO(تمرين Lecture 03)` في `app/agent.py`.

- مثال: اختر مصطلحًا واحدًا من المحاضرة المحددة (`lecture: int`) وأعِد سؤالًا من نوع «ما معنى هذا المصطلح؟» وإجابته
- في سلسلة توثيق الدالة، اشرح «متى تُستخدم هذه الأداة ولماذا» (يقرأ النموذج هذا الوصف ليقرر استخدام الأداة)

```bash
uv run python -m app.agent --trace "أعطني سؤال مراجعة واحدًا من Lecture 02"
uv run pytest -q
```

### 4. سلّم العمل

املأ `lectures/03/answer.md` وافتح Pull Request من `lec03` إلى `main` داخل نسختك المتفرعة.

## الواجب (أكمل أي مستوى واحد)

| المستوى | المهمة |
|---|---|
| أساسي | أعد صياغة `INSTRUCTIONS` أو سلاسل توثيق الأدوات، واستخدم `--trace` لمقارنة التغيرات في استدعاءات الأدوات والإجابات وتسجيلها |
| تطبيقي | أنشئ أداة `save_learning_log` تحفظ سجلات التعلم في `learning_log/`. اطلب تأكيد المستخدم قبل الحفظ (`requires_approval=True` في Pydantic AI). واكتب اختبارات باستخدام TestModel أيضًا |
| متقدم | اختر أحدهما: (أ) أعد بناء الوكيل نفسه باستخدام ADK من Google، وقارن طريقة كتابة الشيفرة وطريقة عرضها في `adk web`. (ب) شغّل Pi، المقدَّم في المحاضرة، داخل Codespaces وقارن موجّه النظام العلني لـ Pi مع `INSTRUCTIONS` الخاص بوكيلك |

### طريقة تنفيذ الخيار المتقدم (ب)

‏Pi وكيل برمجي يستطيع قراءة الملفات وكتابتها وتشغيل الأوامر. لا يطلب تأكيدًا لكل استدعاء أداة. جرّبه داخل Codespaces بدلًا من حاسوبك الشخصي.

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
pi
```

- يقرأ Gemini متغير البيئة `GEMINI_API_KEY`، لذا يعمل سر Codespaces كما هو. اكتب `/model` في Pi واختر نموذج Gemini
- اسم حزمة npm هو `@earendil-works/pi-coding-agent` (الاسم `@mariozechner/...` الوارد في مقالات قديمة اسم سابق)
- موجّه النظام لـ Pi موجود في `packages/coding-agent/src/core/system-prompt.ts` في مستودعه العام، https://github.com/earendil-works/pi. قارنه بـ `INSTRUCTIONS` ولاحظ ما يتضمنه وما يغفله
- التوثيق الرسمي: https://github.com/earendil-works/pi/tree/main/packages/coding-agent/docs

## مراجع

- Pydantic AI: https://ai.pydantic.dev/
- ADK: https://google.github.io/adk-docs/
