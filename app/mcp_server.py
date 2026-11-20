"""خادم MCP لمسرد الدورة وملخصات المحاضرات في المحاضرة 06.

    uv run python -m app.mcp_agent --list-tools
    uv run python -m app.mcp_server --http

يعرض الأمر الأول الأدوات دون مفتاح API. يشغّل الأمر الثاني الخادم على
Streamable HTTP في http://127.0.0.1:8000/mcp.

ينتظر الخادم الإدخال عبر stdio افتراضيًا. يشغّله عميل MCP مثل app.mcp_agent
كعملية فرعية. إذا شغّلته مباشرةً فسيبقى بانتظار الإدخال. يمكن للوكيل
ولعملاء MCP الآخرين استخدام دوال المحاضرة 03 عبر البروتوكول نفسه.
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

# TODO(الواجب الأساسي): أتح get_lecture_summary أيضًا


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
