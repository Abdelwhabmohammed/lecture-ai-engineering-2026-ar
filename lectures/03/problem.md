# تمارين وواجبات Lecture 03: بناء وكيل لدعم التعلم

## أهداف هذه المحاضرة

- التحقق في كودك من أن الوكيل يتكوّن من «نموذج + حلقة + أدوات»
- قراءة الأدوات التي استُدعيت والوسيطات التي استُخدمت معها
- إضافة أداة واحدة

## التمارين (30 دقيقة)

سنخصص نحو الدقائق الخمس الأولى لشرح واجب Lecture 02. خلال ذلك، اضغط Sync fork في الخطوة 1 وشغّل Codespaces، إذ يستغرق بدء التشغيل بضع دقائق.

### 1. جلب تحديثات مستودع المقرر وإنشاء الفرع lec03

أدخل تحديثات مستودع المقرر في نسختك المتفرعة قبل إنشاء فرع العمل.

1. افتح نسختك المتفرعة في GitHub، واضغط **Sync fork → Update branch** (إذا كانت محدَّثة بالفعل فلن يظهر Update branch، ولا يلزمك فعل شيء)
2. شغّل Codespaces، ثم نفّذ الأوامر التالية في الطرفية

```bash
git switch main
git pull --no-rebase
git switch -c lec03
```

- إذا توقف `git switch main`، فهذا يعني وجود تغييرات غير مثبّتة في فرع المحاضرة السابقة. ثبّتها بعمل commit في ذلك الفرع، ثم أعد المحاولة
- إذا ظهرت الرسالة `a branch named 'lec03' already exists`، فقد أنشأت `lec03` بالفعل. انتقل إليه باستخدام `git switch lec03`
- إذا أظهر `git pull --no-rebase` كلمة `CONFLICT`، فارجع إلى الحالة السابقة باستخدام `git merge --abort`، ثم ابدأ بالطريقة التالية (إلغاء الدمج يحافظ على تغييراتك)

#### إذا كان main لا يعمل أو لم تنهِ عمل المحاضرات السابقة

إذا عرض Sync fork تعارضًا واقترح إنشاء Pull Request أو اختيار «Discard commits»، **فلا تضغط هذه الخيارات**، وابدأ بالطريقة التالية. اختيار «Discard commits» يحذف عمليات commit الخاصة بك.

أنشئ فرعًا من كود البداية في مستودع المقرر (الوسم `lec03-start`).

```bash
git fetch https://github.com/matsuolab/lecture-ai-engineering-2026.git tag lec03-start
git switch -c lec03 lec03-start
```

### 2. طرح السؤال نفسه الذي طرحته في Lecture 01 على الوكيل

```bash
uv run python -m app.agent "ما مستويات الواجب الثلاثة في مقرر AIE2026؟"
```

قارن الإجابة بإجابة `app.ask` في Lecture 01. يبحث الوكيل في المسرد قبل الإجابة. توجد المعلومات الصحيحة في المدخل `homework-levels` من `data/glossary.json`.

### 3. قراءة استدعاءات الأدوات

```bash
uv run python -m app.agent --trace "ما الفرق بين LoRA وQLoRA؟"
```

تحقق في أسطر `[tool call]` من الأدوات التي استدعاها النموذج والوسيطات التي استخدمها. يبين `requests` ضمن `[usage]` عدد استدعاءات النموذج اللغوي الكبير لسؤال واحد.

توضح تعليمات النموذج سبب البحث قبل الإجابة، وسبب البحث عن مصطلح واحد في كل مرة. وتوجد التعليمات في موضعين:

- `INSTRUCTIONS` في `app/agent.py` (نحو السطر 31): تعليمات الوكيل ككل، مثل «افحص المسرد دائمًا باستخدام search_glossary» و«اختم إجابتك بذكر المحاضرة المعنية (Lecture NN)»
- سلسلة توثيق كل أداة (docstring) في `app/tools.py`: تُمرَّر إلى النموذج بوصفها وصف الأداة. توضح سلسلة توثيق `search_glossary` أن `query` يجب أن يحتوي على مصطلح واحد فقط

في المستوى الأساسي من الواجب، ستغيّر هذه التعليمات وتقارن أثر ذلك في السلوك.

### 4. كتابة أداة make_quiz وتسجيلها

اجعل الوكيل قادرًا على إنشاء سؤال من المسرد عندما يُطلب منه سؤال مراجعة من Lecture 02. يستدعي النموذج `make_quiz` مع `lecture=2`، فتختار الأداة مصطلحًا واحدًا من Lecture 02 وتعيد سؤالًا وإجابته، ثم يستخدمهما النموذج لطرح السؤال.

1. أضف الدالة `make_quiz(lecture: int) -> str` إلى `app/tools.py`
2. اكتب سلسلة توثيق تشرح متى تُستخدم الأداة ولماذا (يقرأها النموذج ليقرر هل يستخدم الأداة)
3. اجمع من المسرد (`load_glossary()`) المصطلحات التي يطابق حقل `lecture` فيها المحاضرة المطلوبة، واختر واحدًا منها (باستخدام `random.choice` مثلًا)
4. أعِد سلسلة نصية تحتوي على سؤال مثل «ما معنى هذا المصطلح؟» وإجابته (حقل `definition` للمصطلح)، باستخدام `json.dumps` مثلًا
5. سجّلها باستخدام `agent.tool_plain(tools.make_quiz)` عند `TODO(تمرين Lecture 03)` في `app/agent.py`

مثال للقيمة التي تعيدها `make_quiz(2)`:

```text
{"question": "ما معنى PEFT؟", "answer": "بدلًا من جميع معلمات النموذج، …"}
```

### 5. التحقق من استدعاء make_quiz

```bash
uv run python -m app.agent --list-tools    # الأدوات التي يراها النموذج (لا تحتاج إلى مفتاح API)
uv run python -m app.agent --trace "اطرح سؤال مراجعة واحدًا من محتوى Lecture 02"
uv run pytest -q
```

تكون قد نجحت إذا ظهرت `make_quiz` وسلسلة التوثيق التي كتبتها في القائمة، وظهر سطر مثل `[tool call] make_quiz({'lecture': 2})`.

يستدعي `uv run pytest -q` جميع الأدوات، بما فيها `make_quiz` التي أضفتها، بوسيطات وهمية (مثل `lecture=0`) للتحقق من أنها لا تتوقف بخطأ، دون استخدام مفتاح API. لا توجد Lecture 0، لذلك يفشل الاختبار إذا لم تعالج حالة عدم العثور على مصطلحات. عندئذ اجعل الأداة تعيد رسالة واضحة عندما لا توجد مصطلحات.

- لا تظهر في القائمة ← لم تُسجَّل في `app/agent.py`
- تظهر ولكن لا تُستدعى ← اكتب حالة استخدام محددة في سلسلة التوثيق، وأضف إلى `INSTRUCTIONS` تعليمات مثل «استخدم make_quiz عند طلب سؤال مراجعة»

### 6. التسليم وإيقاف Codespaces

املأ `lectures/03/answer.md`، وأنشئ Pull Request من `lec03` إلى `main` داخل نسختك المتفرعة. **تحقق من أن base repository هو نسختك المتفرعة.**

```bash
git add -A
git commit -m "تمارين Lecture 03"
git push -u origin lec03
```

إذا لم تنهِ الخطوة 4، يمكنك تسليم النتائج حتى الخطوة 3. ادفع بقية العمل إلى الفرع نفسه لتحديث Pull Request.

أخيرًا، اختر «Codespaces» أسفل اليسار ← **Stop Current Codespace**.

## الواجب (يكفي العمل على مستوى واحد)

اختر واحدًا من المستويات الثلاثة: أساسي أو تطبيقي أو متقدم. يكفي العمل على أحدها لإتمام الواجب.

| المستوى | المهمة |
|---|---|
| أساسي | غيّر `INSTRUCTIONS` في `app/agent.py` أو سلاسل توثيق الأدوات في `app/tools.py` التي رأيتها في التمارين. شغّل السؤال نفسه مع `--trace`، ثم قارن التغييرات في استدعاء الأدوات والإجابات وسجّلها |
| تطبيقي | أنشئ أداة `save_learning_log` لحفظ سجلات التعلم في `learning_log/`. الحفظ عملية يصعب التراجع عنها، لذا اطلب تأكيد المستخدم قبل الحفظ (`requires_approval=True` في Pydantic AI) |
| متقدم | اختر أحد الخيارين: (a) احتفظ بتعليمات وكيل التمارين وأدواته، وأعِد كتابة الجزء المسؤول عن بناء الوكيل فقط باستخدام ADK من Google، وشغّله بـ `adk run`، ثم قارن الكود والإجابات. (b) شغّل وكيل البرمجة Pi في Codespaces، وقارن موجّه النظام المنشور له مع `INSTRUCTIONS` لوكيلك |

اكتب التسليم في قسم «الواجب» في ملف `lectures/03/answer.md` نفسه المستخدم للتمارين.

### طريقة العمل على المستوى الأساسي

غيّر موضعًا واحدًا فقط من الموضعين اللذين رأيتهما في الخطوة 3 في كل مرة. شغّل السؤال نفسه مع `--trace` وقارن النتائج.

- `INSTRUCTIONS` في `app/agent.py` (نحو السطر 31): تعليمات الوكيل ككل
- سلسلة توثيق كل أداة في `app/tools.py`: تُمرَّر إلى النموذج بوصفها وصف الأداة

يمكنك مثلًا تجربة التغييرات التالية. سجّل كيف تتغير الأدوات المستدعاة وعدد الاستدعاءات والوسيطات والإجابات.

- إذا حذفت من `INSTRUCTIONS` تعليمات فحص المسرد دائمًا باستخدام `search_glossary`، فهل يجيب الوكيل دون بحث؟
- إذا غيّرت سلسلة توثيق `search_glossary` من «ضع مصطلحًا واحدًا فقط في query» إلى «ضع عدة مصطلحات معًا»، فكيف يتغير عدد عمليات البحث والوسيطات؟
- إذا استبدلت تعليمات «اختم إجابتك بذكر المحاضرة المعنية (Lecture NN)» في `INSTRUCTIONS` بتعليمات أخرى (مثل «اختم بسؤال مراجعة واحد»)، فكيف تتغير الإجابة؟

### طريقة العمل على المستوى التطبيقي

1. أنشئ `save_learning_log` في `app/tools.py`، وسجّلها في `app/agent.py` مع `requires_approval=True`
2. عندما يستدعي النموذج هذه الأداة، يتوقف التنفيذ مؤقتًا بانتظار الموافقة، ويُعاد `DeferredToolRequests` كنتيجة (`result.output`). لذلك أضف `DeferredToolRequests` إلى `output_type` للوكيل (وإلا حدث خطأ)

   ```python
   from pydantic_ai import Agent, DeferredToolRequests

   agent = Agent(instructions=INSTRUCTIONS,
                 output_type=[str, DeferredToolRequests])
   ```

3. في CLI، اسأل المستخدم هل يسمح بالحفظ لكل استدعاء في `result.output.approvals`. مرّر هذه القرارات (`DeferredToolResults`) والمحادثة حتى تلك اللحظة (`message_history=result.all_messages()`) إلى استدعاء جديد لـ `run_sync`

للتفاصيل، راجع Human-in-the-Loop Tool Approval ضمن وثائق Pydantic AI الرسمية «Deferred Tools»: https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/

### طريقة العمل على الخيار المتقدم (a): إعادة البناء باستخدام ADK

احتفظ بتعليمات وكيل التمارين وأدواته، وأعِد كتابة الجزء المسؤول عن بناء الوكيل فقط باستخدام ADK.

| النطاق | التفاصيل |
|---|---|
| إعادة الاستخدام | `INSTRUCTIONS` من `app/agent.py`، و`search_glossary` و`get_lecture_summary` من `app/tools.py` (و`make_quiz` أيضًا إذا أنشأتها في التمارين) |
| كتابة ملفات جديدة | أنشئ `agent.py` (الكود أدناه) و`__init__.py` (بسطر واحد هو `from . import agent`) داخل `adk_agent/glossary_agent/` |
| غير مطلوب | خصائص الأوامر مثل `--trace`، أو الاختبارات، أو الأدوات التي تتطلب الموافقة. لا تغيّر ملفات `app/` |
| المقارنة | الكود (كيفية تمرير التعليمات والأدوات) والإجابات عن الأسئلة نفسها المستخدمة في التمارين |

بنية `adk_agent/glossary_agent/agent.py`:

```python
from google.adk.agents import Agent
from app import tools
from app.agent import INSTRUCTIONS

root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[...],  # الأدوات المستخدمة في التمارين
)
```

للتشغيل، نفّذ الأمر التالي من جذر المستودع:

```bash
PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
```

- يتيح `adk run` الحوار في الطرفية. اكتب سؤالًا واضغط Enter لتلقي إجابة. لإنهاء الحوار، اكتب `exit`
- يضيف `uv run --with google-adk` مكتبة ADK مؤقتًا إلى بيئة المقرر لهذا التشغيل. لا يغيّر `pyproject.toml` أو `uv.lock`
- يلزم `PYTHONPATH=.` لاستيراد مجلد `app` من جذر المستودع
- يُستخدم مفتاح API من سر Codespaces الحالي `GEMINI_API_KEY`
- يستغرق تنزيل ADK نحو دقيقة في أول تشغيل

اطرح الأسئلة نفسها المستخدمة في التمارين، وسجّل الاختلافات في الكود والإجابات مقارنة بنسخة Pydantic AI.

أدخل الإصدار 2.0 من ADK تغييرات كبيرة. قد تتضمن المقالات على الويب معلومات قديمة لا تراعي هذه التغييرات، لذا تساعد الاستعانة بالوثائق الرسمية على تجنّب أخطاء التنفيذ.

- الوثائق الرسمية: https://adk.dev/

### طريقة العمل على الخيار المتقدم (b): تشغيل Pi في Codespaces

Pi وكيل برمجة يعدّل الملفات وينفّذ الأوامر دون طلب التأكيد. جرّبه داخل Codespaces بدلًا من حاسوبك الشخصي.

1. **التثبيت**: نفّذ ما يلي في طرفية Codespaces

   ```bash
   npm install -g --ignore-scripts @earendil-works/pi-coding-agent
   ```

2. **التشغيل**: اكتب `pi` في الطرفية
3. **إعداد النموذج**: اكتب `/model` داخل Pi، واختر نموذج Gemini. يُستخدم مفتاح API من سر Codespaces الحالي `GEMINI_API_KEY`
4. **المقارنة**: يوجد موجّه النظام الخاص بـ Pi في `packages/coding-agent/src/core/system-prompt.ts` ضمن المستودع العام https://github.com/earendil-works/pi. قارنه مع `INSTRUCTIONS` لوكيلك لتعرف ما يتضمنه وما يغيب عنه

- وثائق Pi الرسمية: https://github.com/earendil-works/pi/tree/main/packages/coding-agent/docs

## المراجع

- Pydantic AI: https://pydantic.dev/docs/ai/
- ADK: https://adk.dev/
