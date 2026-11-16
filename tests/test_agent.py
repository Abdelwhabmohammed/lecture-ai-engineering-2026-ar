"""اختبارات توصيل الوكيل.

‏TestModel نموذج وهمي يستدعي جميع الأدوات المسجلة ويعيد إجابة شكلية
دون استدعاء نموذج لغوي كبير حقيقي. تحقق من تسجيل الأدوات واستدعائها وإعادة نتائجها
إلى النموذج دون استخدام مفتاح API أو استهلاك حصة الاستخدام.
"""

from pydantic_ai import DeferredToolRequests, DeferredToolResults
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app.agent import agent

BASE_TOOLS = {
    "search_glossary",
    "get_lecture_summary",
    "make_quiz",
    "save_learning_log",
}


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
    # الأدوات التي تتطلب الموافقة (requires_approval=True) تنتظر دون تنفيذ، لذا لا تكون لها قيمة إرجاع
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("ما هو RAG؟")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


def test_learning_log_waits_for_approval_then_saves(tmp_path, monkeypatch):
    from app import tools

    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    model = TestModel(call_tools=["save_learning_log"])
    with agent.override(model=model):
        pending = agent.run_sync("احفظ ما تعلمته عن LoRA")

        assert isinstance(pending.output, DeferredToolRequests)
        call = pending.output.approvals[0]
        completed = agent.run_sync(
            None,
            message_history=pending.all_messages(),
            deferred_tool_results=DeferredToolResults(
                approvals={call.tool_call_id: True}
            ),
        )

    assert completed.output
    assert list(tools.LOG_DIR.glob("*.json"))
