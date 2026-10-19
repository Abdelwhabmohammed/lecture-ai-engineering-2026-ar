"""Lecture 05: اختبارات اتصال خادم MCP وعميله (دون استخدام نموذج لغوي كبير أو مفتاح API).

شغّل خادم المسرد فعليًا من app/mcp_servers.json (عبر stdio)، واستخدم TestModel
للتحقق من إتاحة الأدوات عبر MCP واستدعائها وإعادة نتائجها.
"""

import json

from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import MCP_CONFIG, build_mcp_agent

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
