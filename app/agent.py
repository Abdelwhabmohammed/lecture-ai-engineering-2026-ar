"""Lecture 03: وكيل لدعم التعلم مبني باستخدام Pydantic AI.

Usage:
    uv run python -m app.agent "ما وسم lecNN-start في مقرر AIE2026؟"
    uv run python -m app.agent --trace "ما الفرق بين LoRA وQLoRA؟"   # اعرض استدعاءات الأدوات
    uv run python -m app.agent --mcp --trace "ما هو LoRA؟"    # Lecture 05: تلقّ الأدوات من خوادم MCP
    uv run python -m app.agent --mcp --list-tools              # Lecture 05: اعرض الأدوات المرئية للنموذج (دون مفتاح API)

الوكيل = نموذج + حلقة + أدوات.
يستدعي النموذج دوال tools.py بوصفها «أدوات» ويستخدم نتائجها لصياغة الإجابات.
في Lecture 05 يتلقى الأدوات نفسها عبر خادم MCP (app/mcp_server.py).
"""

import argparse
import inspect
import json
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from fastmcp import Client
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

INSTRUCTIONS = """\
أنت وكيل لدعم التعلم في AI Engineering Pilot Course (AIE2026).
- افحص المسرد دائمًا باستخدام search_glossary قبل الإجابة عن المصطلحات أو المعلومات الخاصة بالمقرر.
- استخدم get_lecture_summary عند السؤال عن محتوى محاضرة.
- إذا لم ترد المعلومة في المسرد، فقل «ليست في المسرد» بدلًا من إطلاق أحكام مبنية على التخمين.
- اختم إجابتك بذكر المحاضرة المعنية (Lecture NN).
- أرشد المتعلمين إلى طريقة التفكير بتلميحات، ولا تكتب إجابات الواجبات بدلًا منهم.
"""

# مرّر النموذج وقت التشغيل (حتى تتمكن الاختبارات من استخدام TestModel دون استدعاء API)
agent = Agent(instructions=INSTRUCTIONS)
agent.tool_plain(tools.search_glossary)
agent.tool_plain(tools.get_lecture_summary)

# TODO(تمرين Lecture 03): أنشئ make_quiz في tools.py وسجّلها هنا

# Lecture 05: ملف إعداد خوادم MCP. يستخدم صيغة "mcpServers" نفسها المستخدمة في Claude Desktop وCursor
MCP_CONFIG = Path(__file__).resolve().parent / "mcp_servers.json"


def load_mcp_servers(config_path: Path = MCP_CONFIG) -> list[MCPToolset]:
    """اقرأ ملف الإعداد (بصيغة mcpServers) وأنشئ اتصالًا (MCPToolset) لكل خادم.

    - مع "command"، استخدم stdio: شغّل الخادم كعملية فرعية.
    - مع "url"، استخدم Streamable HTTP: اتصل بخادم يعمل بالفعل.
    أضف بادئة "server_name_" إلى أسماء الأدوات (مثل glossary_search_glossary)
    لتمييز الأدوات متطابقة الأسماء على الخوادم المختلفة.

    يتيح Pydantic AI أيضًا load_mcp_toolsets() للغرض نفسه. ننشئ الاتصالات هنا
    بأنفسنا لأن الكشف التلقائي عن وضع الاتصال ("auto") يصدر تحذيرات كثيرة
    مع الخوادم المبنية بحزم تطوير قديمة (مثل fetch). تحديد الوضع "legacy"
    يتيح الاتصال بالخوادم القديمة والحديثة دون تلك التحذيرات.
    """
    config = json.loads(Path(config_path).read_text(encoding="utf-8"))["mcpServers"]
    toolsets = []
    for name, spec in config.items():
        if "url" in spec:
            transport = spec["url"]
        else:
            transport = StdioTransport(spec["command"], spec.get("args", []), env=spec.get("env"))
        toolsets.append(MCPToolset(Client(transport, mode="legacy")).prefixed(name))
    return toolsets


def build_mcp_agent(config_path: Path = MCP_CONFIG) -> Agent:
    """Lecture 05: وكيل يستخدم الأدوات التي تتيحها خوادم MCP بدلًا من الدوال المسجلة مباشرة. تبقى INSTRUCTIONS كما هي."""
    return Agent(instructions=INSTRUCTIONS, toolsets=load_mcp_servers(config_path))


def build_model() -> GoogleModel:
    return GoogleModel(MODEL, provider=GoogleProvider(api_key=get_api_key()))


def print_tools(target: Agent) -> None:
    """اعرض الأدوات المرئية للنموذج (الأسماء، الأوصاف، الوسيطات). لا تستدعِ نموذجًا لغويًا كبيرًا.

    مرّر الأدوات إلى TestModel (النموذج الوهمي المستخدم للاختبار) ثم اقرأها منه.
    تظهر أدوات خادم MCP ودوال Lecture 03 بالطريقة نفسها للنموذج.
    """
    model = TestModel(call_tools=[])
    target.run_sync("قائمة الأدوات", model=model)
    tools_seen = model.last_model_request_parameters.function_tools
    print(f"الأدوات المرئية للنموذج: {len(tools_seen)}")
    for tool in tools_seen:
        print(f"\n[{tool.name}]")
        print("  " + inspect.cleandoc(tool.description or "").replace("\n", "\n  "))
        params = tool.parameters_json_schema.get("properties", {})
        print(f"  الوسيطات: {json.dumps(params, ensure_ascii=False)}")


def print_trace(result) -> None:
    """اعرض الأدوات المستدعاة ووسيطاتها وما أعادته."""
    print("\n--- trace ---")
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                print(f"[tool call]   {part.tool_name}({part.args})")
            elif isinstance(part, ToolReturnPart):
                print(f"[tool return] {part.tool_name} -> {str(part.content)[:120]}…")
    print(f"[usage] {result.usage}")


def main() -> None:
    parser = argparse.ArgumentParser(description="اطرح سؤالًا على وكيل دعم التعلم")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--trace", action="store_true", help="اعرض استدعاءات الأدوات")
    parser.add_argument("--mcp", action="store_true", help="Lecture 05: تلقّ الأدوات من خوادم MCP (app/mcp_servers.json)")
    parser.add_argument("--list-tools", action="store_true", help="اعرض الأدوات المرئية للنموذج ثم أنهِ التشغيل (دون مفتاح API)")
    args = parser.parse_args()

    target = build_mcp_agent() if args.mcp else agent
    if args.list_tools:
        print_tools(target)
        return
    if not args.question:
        parser.error("يرجى إدخال سؤال")

    print(f"[model] {MODEL}")
    if args.mcp:
        print("[الأدوات] خوادم MCP (app/mcp_servers.json)")
    try:
        result = target.run_sync(args.question, model=build_model())
    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    print(result.output)
    if args.trace:
        print_trace(result)


if __name__ == "__main__":
    main()
