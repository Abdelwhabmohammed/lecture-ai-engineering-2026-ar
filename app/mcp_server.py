"""Lecture 05: إتاحة المسرد والنقاط الرئيسة للمحاضرات عبر خادم MCP.

Usage:
    uv run python -m app.agent --mcp --list-tools   # اعرض الأدوات التي يتيحها هذا الخادم (دون مفتاح API)
    uv run python -m app.mcp_server --http          # شغّله باستخدام Streamable HTTP (http://127.0.0.1:8000/mcp)

دون وسيطات، يستمع الخادم عبر stdio (الإدخال والإخراج القياسيين). هذا الوضع مخصص لعميل MCP
(مثل app.agent مع --mcp أو Copilot Chat) كي يشغّل الخادم كعملية فرعية. إذا شغّلته يدويًا
فسيبدو كأنه توقف بينما ينتظر الإدخال.

في Lecture 03 سجّلنا دوال tools.py مباشرة في agent.py. يتيح خادم MCP لعملاء
غير Pydantic AI، مثل Copilot Chat، استخدام الدوال نفسها عبر بروتوكول مشترك.
"""

import argparse

from mcp.server.mcpserver import MCPServer

from app import tools

# اسم الخادم ووصفه المعروضان للعملاء (يختلف عن المفتاح "glossary" في ملف الإعداد)
server = MCPServer(
    "aie2026-glossary",
    instructions="يتيح المسرد والنقاط الرئيسة لمحاضرات AIE2026 (AI Engineering Pilot Course).",
)

# أتح الدالة نفسها المستخدمة في Lecture 03 كأداة MCP؛ تتحول سلسلة توثيقها وتلميحات أنواعها إلى وصف الأداة
server.tool()(tools.search_glossary)

# TODO(تمرين Lecture 05): أتح tools.get_lecture_summary أيضًا (بنفس صيغة السطر أعلاه)
# إذا أنشأت make_quiz في Lecture 03 فيمكنك إتاحتها أيضًا


def main() -> None:
    parser = argparse.ArgumentParser(description="خادم MCP للمسرد")
    parser.add_argument("--http", action="store_true", help="ابدأ باستخدام Streamable HTTP (الافتراضي: stdio)")
    args = parser.parse_args()
    if args.http:
        print("بدء تشغيل خادم MCP على http://127.0.0.1:8000/mcp (اضغط Ctrl+C للإيقاف)")
        server.run(transport="streamable-http")
    else:
        # في وضع stdio، يحمل الإخراج القياسي رسائل البروتوكول؛ لا تطبع عليه
        server.run()


if __name__ == "__main__":
    main()
