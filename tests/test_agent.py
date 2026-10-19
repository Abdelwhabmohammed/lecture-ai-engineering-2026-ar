"""اختبارات توصيل الوكيل.

‏TestModel نموذج وهمي يستدعي جميع الأدوات المسجلة ويعيد إجابة شكلية
دون استدعاء نموذج لغوي كبير حقيقي. تحقق من تسجيل الأدوات واستدعائها وإعادة نتائجها
إلى النموذج دون استخدام مفتاح API أو استهلاك حصة الاستخدام.
"""

from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("ما هو LoRA؟")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # افحص الاحتواء حتى لا تؤدي إضافة أدوات في التمارين إلى فشل الاختبار

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    assert len(_parts(result, ToolReturnPart)) == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("ما هو RAG؟")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"
