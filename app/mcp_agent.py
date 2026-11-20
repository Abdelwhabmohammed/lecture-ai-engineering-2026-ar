"""وكيل دعم التعلّم وعميل MCP للمحاضرة 06.

    uv run python -m app.mcp_agent --list-tools
    uv run python -m app.mcp_agent --trace "ما هو LoRA؟"

في المحاضرة 03 سُجّلت دوال tools.py مباشرةً في الوكيل. هنا يكتشف الوكيل
الأدوات التي تتيحها الخوادم المعرّفة في app/mcp_servers.json.
تبقى البنية مكوّنة من النموذج والحلقة والأدوات كما في المحاضرة 03.
"""

import argparse
import inspect
import json
from pathlib import Path

from fastmcp import Client
from mcp.shared.exceptions import MCPError
from pydantic_ai import Agent
from pydantic_ai.exceptions import AgentRunError, ModelHTTPError, UserError
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.messages import RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider

from app.config import MODEL, api_error_message, get_api_key

# وجّه الوكيل إلى استخدام المسرد والخوادم الأخرى المعرّفة في الإعدادات.
INSTRUCTIONS = """\
أنت وكيل دعم التعلّم لدورة هندسة الذكاء الاصطناعي (AIE2026). أجب بالعربية.
- تحقّق من المسرد باستخدام search_glossary قبل الإجابة عن مصطلح أو سؤال يخص الدورة.
- استخدم get_lecture_summary عند السؤال عن محتوى محاضرة.
- إذا لم تجد المصطلح في المسرد، اذكر ذلك وتجنّب التخمين.
- اذكر رقم المحاضرة ذات الصلة في نهاية الإجابة (Lecture N).
- قدّم تلميحات عن طريقة التفكير ليحل المتعلّم واجبه بنفسه.
- استخدم أداة مناسبة عند توفرها للأسئلة خارج نطاق المسرد، مثل محتوى صفحات الويب أو وثائق AWS.
"""

# إعداد الخوادم بصيغة "mcpServers" كما في Claude Desktop وCursor.
MCP_CONFIG = Path(__file__).resolve().parent / "mcp_servers.json"


class ConfigError(Exception):
    """خطأ في إعداد app/mcp_servers.json."""


def read_config(config_path: Path = MCP_CONFIG) -> dict:
    """أعد أسماء الخوادم وإعداداتها من الكائن mcpServers."""
    try:
        config = json.loads(Path(config_path).read_text(encoding="utf-8"))["mcpServers"]
    except json.JSONDecodeError as e:
        raise ConfigError(f"صياغة JSON غير صالحة قرب السطر {e.lineno} ({e.msg})") from e
    except KeyError as e:
        raise ConfigError('المفتاح "mcpServers" مفقود') from e
    for name, spec in config.items():
        if "command" not in spec and "url" not in spec:
            raise ConfigError(f'يحتاج الخادم "{name}" إلى "command" أو "url"')
    return config


def load_mcp_servers(config_path: Path = MCP_CONFIG) -> list[MCPToolset]:
    """أنشئ مجموعة أدوات MCP لكل خادم في الإعدادات.

    يبدأ command عملية فرعية عبر stdio. يصل url إلى خادم قائم عبر
    Streamable HTTP. يسبق اسم الخادم اسم الأداة لتمييز الأدوات المتشابهة.

    توفر Pydantic AI الدالة load_mcp_toolsets(). يحدّد وضع legacy طريقة
    الاتصال ويمنع تنبيهات الاكتشاف التلقائي مع SDK أقدم، مثل خادم fetch.
    """
    toolsets = []
    for name, spec in read_config(config_path).items():
        if "url" in spec:
            transport = spec["url"]
        else:
            transport = StdioTransport(spec["command"], spec.get("args", []), env=spec.get("env"))
        toolsets.append(MCPToolset(Client(transport, mode="legacy")).prefixed(name))
    return toolsets


def describe_servers(config_path: Path = MCP_CONFIG) -> list[str]:
    """صف طريقة تشغيل كل خادم أو الاتصال به."""
    lines = []
    for name, spec in read_config(config_path).items():
        if "url" in spec:
            lines.append(f"[server] {name}: الاتصال بعنوان URL ({spec['url']})")
        else:
            command = " ".join([spec["command"], *spec.get("args", [])])
            lines.append(f"[server] {name}: التشغيل بالأمر ({command})")
    return lines


def build_mcp_agent(config_path: Path = MCP_CONFIG) -> Agent:
    """أنشئ وكيلًا يستخدم أدوات MCP. مرّر النموذج وقت التنفيذ."""
    return Agent(instructions=INSTRUCTIONS, toolsets=load_mcp_servers(config_path))


def build_model() -> GoogleModel:
    return GoogleModel(MODEL, provider=GoogleProvider(api_key=get_api_key()))


def print_tools(target: Agent) -> None:
    """اعرض أسماء الأدوات وأوصافها ووسيطاتها باستخدام نموذج اختباري.

    يتيح TestModel قراءة تعريفات الأدوات دون استدعاء نموذج لغوي.
    """
    model = TestModel(call_tools=[])
    target.run_sync("قائمة الأدوات", model=model)
    tools_seen = model.last_model_request_parameters.function_tools
    print(f"الأدوات التي يراها النموذج: {len(tools_seen)}")
    for tool in tools_seen:
        print(f"\n[{tool.name}]")
        print("  " + inspect.cleandoc(tool.description or "").replace("\n", "\n  "))
        params = tool.parameters_json_schema.get("properties", {})
        print(f"  الوسيطات: {json.dumps(params, ensure_ascii=False)}")


def print_trace(result) -> None:
    """اعرض استدعاءات الأدوات ووسيطاتها والنتائج التي تعيدها."""
    print("\n--- trace ---")
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                print(f"[tool call]   {part.tool_name}({part.args})")
            elif isinstance(part, ToolReturnPart):
                print(f"[tool return] {part.tool_name} -> {str(part.content)[:120]}…")
            elif isinstance(part, RetryPromptPart) and part.tool_name:
                # يمكن للنموذج استخدام الخطأ ليقرر ما إذا كان سيعيد الاستدعاء.
                print(f"[tool error]  {part.tool_name} -> {str(part.content)[:120]}")
    usage = result.usage
    print(f"[usage] الإدخال {usage.input_tokens:,} رمز / الإخراج {usage.output_tokens:,} رمز / ردود النموذج {usage.requests}")


def main() -> None:
    parser = argparse.ArgumentParser(description="اطرح سؤالًا على وكيل دعم التعلّم الذي يستخدم أدوات MCP")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--trace", action="store_true", help="اعرض استدعاءات الأدوات")
    parser.add_argument("--list-tools", action="store_true", help="اعرض الأدوات التي يراها النموذج ثم اخرج (دون مفتاح API)")
    args = parser.parse_args()
    if not args.list_tools and not args.question:
        parser.error("أدخل سؤالًا")

    try:
        target = build_mcp_agent()
        print("\n".join(describe_servers()))
    except ConfigError as e:
        print(f"تعذّرت قراءة app/mcp_servers.json: {e}")
        print("تحقّق من وجود فاصلة بين الخوادم ومن خلو ما بعد الخادم الأخير من فاصلة زائدة.")
        raise SystemExit(1)
    try:
        if args.list_tools:
            print_tools(target)
            return
        model = build_model()
        print(f"[model] {MODEL}")
        print(f"[tools] خوادم MCP ({MCP_CONFIG.relative_to(MCP_CONFIG.parent.parent)})")
        result = target.run_sync(args.question, model=model)
    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    except (AgentRunError, UserError):
        raise  # اعرض خطأ تنفيذ الوكيل كما ورد.
    except (MCPError, RuntimeError, OSError) as e:
        # تعذّر تشغيل الخادم أو الاتصال به.
        print(f"تعذّر الاتصال بخادم MCP: {e}")
        print("تحقّق من أمر الخادم أو عنوان URL في app/mcp_servers.json.")
        raise SystemExit(1)
    print(result.output)
    if args.trace:
        print_trace(result)


if __name__ == "__main__":
    main()
