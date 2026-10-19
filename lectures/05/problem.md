# تمارين وواجبات Lecture 05: إتاحة الأدوات واستخدامها عبر خادم MCP

## أهداف هذه المحاضرة

- انقل الأدوات المبنية في Lecture 03 إلى **خادم MCP** واستخدمها **عبر MCP** من الوكيل نفسه
- اقرأ «أسماء الأدوات وأوصافها ووسيطاتها» التي يراها النموذج
- أضف أدوات خارجية جاهزة **بتعديل ملف الإعداد وحده**

## التحضير

إذا أكملت أعمال المحاضرات السابقة، فأنشئ الفرع `lec05` من `main`.
تضيف هذه المحاضرة تبعيات، لذا نفّذ `uv sync --frozen` مرة واحدة.

```bash
git switch main && git switch -c lec05
uv sync --frozen
```

وإلا فيمكنك إنشاء فرع من شيفرة البداية في مستودع المقرر (الوسم `lec05-start`).

```bash
git remote -v                     # إذا لم يكن upstream موجودًا، فأضفه بالسطر التالي
git remote add upstream https://github.com/matsuolab/lecture-ai-engineering-2026.git
git fetch upstream --tags
git switch -c lec05 lec05-start
uv sync --frozen
```

## التمارين (30 دقيقة)

### 1. اعرض الأدوات المرئية للنموذج

```bash
uv run python -m app.agent --list-tools          # Lecture 03: أدوات مسجلة مباشرة كدوال
uv run python -m app.agent --mcp --list-tools    # Lecture 05: أدوات يتلقاها الوكيل من خوادم MCP
```

لا يستدعي أيّ من الأمرين نموذجًا لغويًا كبيرًا، لذا يعمل كلاهما دون مفتاح API.
يشغّل الأمر الثاني الخادم (`app/mcp_server.py`) المحدد في `app/mcp_servers.json` كعملية فرعية، ويعرض أسماء أدواته المتاحة وأوصافها ووسيطاتها.

- تحقق من وجود **البادئة "server_name_"** في الأسماء، كما في `glossary_search_glossary`. تميّز هذه البادئة الأدوات متطابقة الأسماء على خوادم مختلفة
- تأتي الأوصاف مباشرة من سلاسل توثيق الدوال في `app/tools.py`. **تظهر أدوات الدوال وأدوات MCP بالطريقة نفسها للنموذج**

### 2. استخدمها عبر MCP من الوكيل

```bash
uv run python -m app.agent --mcp --trace "ما مستويات الواجب الثلاثة في مقرر AIE2026؟"
```

قارن الإجابة وأسماء الأدوات وعدد `requests` مع Lecture 03 (دون `--mcp`).
داخليًا، تقرأ `build_mcp_agent()` في `app/agent.py` ملف الإعداد، وتبدأ الخوادم، وتمرّر أدواتها إلى الوكيل.

### 3. أتح أداة أخرى

عند `TODO(تمرين Lecture 05)` في `app/mcp_server.py`، أتح `get_lecture_summary` عبر MCP أيضًا (بسطر واحد على غرار سطر `search_glossary`).

```bash
uv run python -m app.agent --mcp --list-tools
uv run python -m app.agent --mcp --trace "ماذا سنتعلم في Lecture 02؟"
uv run pytest -q
```

تحقق من ظهور `glossary_get_lecture_summary` في `--list-tools` واستدعائها في `--trace`.
إذا أنشأت `make_quiz` في Lecture 03، فيمكنك إتاحتها بالطريقة نفسها.

### 4. أضف أداة خارجية جاهزة عبر الإعداد وحده

أضف **خادم fetch** المتاح للجميع (يجلب صفحة من URL ويعيدها بصيغة Markdown) إلى `app/mcp_servers.json`. لا حاجة إلى كتابة شيفرة.

```json
{
  "mcpServers": {
    "glossary": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    },
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    }
  }
}
```

```bash
uv run python -m app.agent --mcp --list-tools
uv run python -m app.agent --mcp --trace "لخّص مقدمة https://modelcontextprotocol.io/ في ثلاثة أسطر بالعربية"
```

- يستغرق التشغيل الأول نحو 10 ثوانٍ لأن `uvx` ينزّل الخادم
- إذا ظهر `fetch_fetch({'url': ...})` في `--trace`، فهذا يعني أن **Codespace يتصل فعليًا بعنوان URL الذي اختاره النموذج**. قبل إضافة أداة خارجية، افهم أين ترسل البيانات وما الذي ترسله
- تفترض `INSTRUCTIONS` استخدام المسرد. إذا لم يُستدعَ fetch لسؤال يتضمن URL، فجرّب إضافة سطر مثل «عند إعطائك URL، استخدم fetch لقراءة محتواه» إلى `INSTRUCTIONS`

### 5. سلّم العمل

املأ `lectures/05/answer.md` وافتح Pull Request من `lec05` إلى `main` داخل نسختك المتفرعة.

## الواجب (أكمل أي مستوى واحد)

| المستوى | المهمة |
|---|---|
| أساسي | ابدأ الخادم بالأمر `uv run python -m app.mcp_server --http`، واستبدل إدخال `glossary` في ملف الإعداد بـ `{"url": "http://127.0.0.1:8000/mcp"}`، ثم اطرح السؤال نفسه. سجّل الفروق في بدء التشغيل والعمليات والمنافذ بين stdio وStreamable HTTP. أعد أيضًا صياغة سلسلة توثيق أداة وقارن التغيرات في `--list-tools` واستدعاءات الأدوات |
| تطبيقي | أضف `make_quiz` من Lecture 03 (أو أداة جديدة إذا لم تنشئها) إلى خادم MCP، وأضف اختبارات باستخدام TestModel في `tests/test_mcp_server.py`. تحقق من مجال قيم الوسيطات (مثل إعادة رسالة واضحة لمحاضرة غير موجودة)، واستخدم `--trace` لفحص كيفية ظهور أخطاء MCP للنموذج |
| متقدم | استخدم خادم المسرد نفسه من **Copilot Chat** (عميل MCP في VS Code؛ التعليمات أدناه). تحقق من أن «خادمًا واحدًا يمكن استخدامه من عدة عملاء» وقارن ذلك باستخدامه من الوكيل (`app/agent.py`). سجّل الفروق في الخطوات المؤدية إلى استدعاء الأداة (من يشغّل الخادم، وهل يوافق شخص على الاستدعاءات مسبقًا، وكيف تظهر النتائج) |

### طريقة تنفيذ الواجب المتقدم

يعمل Copilot Chat كعميل MCP في VS Code. ضع `.vscode/mcp.json` في المستودع لاستخدام أدوات الخادم في وضع **Agent** ضمن Chat (تستخدم الصيغة `servers` بدلًا من `mcpServers` كما في `app/mcp_servers.json`. تُنفَّذ الأوامر في مجلد العمل، وهو جذر المستودع).

```json
{
  "servers": {
    "aie-glossary": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"]
    }
  }
}
```

1. أنشئ الملف أعلاه في VS Code داخل Codespaces. انقر **Start** إذا ظهر فوق `servers` (وإلا فاستخدم لوحة الأوامر: **MCP: List Servers** → `aie-glossary` → Start). يبدأ الخادم داخل Codespace
2. افتح Copilot Chat وانتقل إلى وضع **Agent**. تحقق من ظهور `search_glossary` من `aie-glossary` في قائمة الأدوات (🔧) (وكذلك `get_lecture_summary` إذا أكملت التمرين 3)
3. اسأل «ما مستويات الواجب الثلاثة في AIE2026؟». إذا طُلب التأكيد (**Continue**) قبل تنفيذ الأداة، فاسمح به، وتحقق من استدعاء أداة المسرد واستخدامها في الإجابة
4. في `answer.md`، سجّل استدعاء الأداة الظاهر في Chat إلى جانب مخرجات `uv run python -m app.agent --mcp --trace`
5. يمكنك إضافة `.vscode/mcp.json` إلى Pull Request (لا تضع فيه أسرارًا مثل مفاتيح API)

- تدعم خطة Copilot Free وضع Agent وMCP. لكن للمحادثة حدًا شهريًا، لذا اكتفِ بمحاولات قليلة
- قد تمنع سياسة المؤسسة استخدام MCP في Copilot الذي تديره شركة أو مؤسسة تعليمية (Business / Enterprise). جرّب حسابًا شخصيًا

## ملاحظات

- خادم MCP **برنامج ينفّذ شيفرة**. لا تضف خوادم من مصادر مجهولة إلى ملف الإعداد
- يتصل خادم fetch بعناوين URL يختارها النموذج. لا تمرر عناوين داخلية لشركتك أو عناوين تتضمن معلومات شخصية
- زيادة الأدوات تعني إرسال أوصاف أكثر إلى النموذج، ما يزيد عدد الرموز في الاستدعاء ويصعّب اختيار الأداة. استخدم `--list-tools` لمتابعة عدد الأدوات المتاحة

## مراجع

- موقع MCP الرسمي: https://modelcontextprotocol.io/
- عميل MCP في Pydantic AI: https://pydantic.dev/docs/ai/mcp/client/
- حزمة تطوير MCP لـ Python (كتابة الخوادم): https://github.com/modelcontextprotocol/python-sdk
- خوادم MCP العامة: https://github.com/modelcontextprotocol/servers
- استخدام خوادم MCP في VS Code: https://code.visualstudio.com/docs/copilot/customization/mcp-servers
