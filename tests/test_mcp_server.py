"""Lecture 06: اختبارات اتصال خادم MCP وعميله (دون استخدام نموذج لغوي كبير أو مفتاح API).

شغّل خادم المسرد فعليًا من app/mcp_servers.json (عبر stdio)، واستخدم TestModel
للتحقق من إتاحة الأدوات عبر MCP واستدعائها وإعادة نتائجها.
"""

import json

import pytest
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.mcp_agent import MCP_CONFIG, ConfigError, build_mcp_agent, describe_servers, read_config

GLOSSARY_TOOL = "glossary_search_glossary"  # يبدأ باسم الخادم "glossary" الوارد في ملف الإعداد


def _glossary_only_config(tmp_path):
    """استخدم خادم المسرد وحده من ملف الإعداد (لا تشغّل خوادم خارجية مثل fetch التي قد تُضاف في التمارين)."""
    config = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
    assert "glossary" in config["mcpServers"], "يجب أن يحتوي app/mcp_servers.json على خادم للمسرد"
    path = tmp_path / "mcp_servers.json"
    path.write_text(
        json.dumps({"mcpServers": {"glossary": config["mcpServers"]["glossary"]}}), encoding="utf-8"
    )
    return path


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_glossary_server_exposes_search_tool(tmp_path):
    model = TestModel(call_tools=[])
    build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("قائمة الأدوات", model=model)

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert GLOSSARY_TOOL in offered  # افحص الاحتواء حتى لا تؤدي إضافة أدوات في التمارين إلى فشل الاختبار


def test_glossary_result_comes_back_through_mcp(tmp_path):
    model = TestModel(call_tools=[GLOSSARY_TOOL])
    result = build_mcp_agent(_glossary_only_config(tmp_path)).run_sync("ما هو LoRA؟", model=model)

    assert [p.tool_name for p in _parts(result, ToolCallPart)] == [GLOSSARY_TOOL]
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == GLOSSARY_TOOL
    assert str(returns[0].content).strip()  # أُعيدت نتيجة بحث (أو رسالة تفيد بعدم العثور)
    assert result.output


def test_describe_servers_tells_command_from_url(tmp_path):
    path = tmp_path / "mcp_servers.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "glossary": {"command": "uv", "args": ["run", "python", "-m", "app.mcp_server"]},
                    "aws": {"url": "https://knowledge-mcp.global.api.aws"},
                }
            }
        ),
        encoding="utf-8",
    )
    assert describe_servers(path) == [
        '[server] glossary: التشغيل بالأمر (uv run python -m app.mcp_server)',
        '[server] aws: الاتصال بعنوان URL (https://knowledge-mcp.global.api.aws)',
    ]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ('{"mcpServers": {"a": {"command": "uv"} "b": {"url": "https://example.com"}}}', 'صياغة\\ JSON\\ غير\\ صالحة\\ قرب\\ السطر\\ 1'),
        ('{"servers": {}}', 'المفتاح\\ "mcpServers"\\ مفقود'),
        ('{"mcpServers": {"a": {"args": []}}}', 'يحتاج\\ الخادم\\ "a"\\ إلى\\ "command"\\ أو\\ "url"'),
    ],
)
def test_config_mistakes_are_reported_in_words(tmp_path, text, expected):
    path = tmp_path / "mcp_servers.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match=expected):
        read_config(path)
