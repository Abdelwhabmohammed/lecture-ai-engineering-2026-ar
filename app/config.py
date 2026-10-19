"""إعدادات مشتركة في أنحاء المقرر.

اقرأ مفاتيح API وأسماء النماذج من متغيرات البيئة بدلًا من تضمينها في الشيفرة.
"""

import os

# النموذج الافتراضي. اضبط متغير البيئة AIE_MODEL لتغييره.
#   مثال: export AIE_MODEL=gemini-3.5-flash
DEFAULT_MODEL = "gemini-3.5-flash-lite"
MODEL = os.getenv("AIE_MODEL", DEFAULT_MODEL)


def api_error_message(status: int, detail: str = "") -> str:
    """حوّل رمز حالة HTTP إلى شرح واضح للمتعلم (تستخدمه ask.py و agent.py)."""
    if status == 429:
        return "بلغت حد معدل الطلبات. انتظر دقيقة تقريبًا ثم حاول مجددًا."
    if status == 503:
        return "النموذج مشغول (503). انتظر قليلًا ثم حاول مجددًا."
    if status in (400, 401, 403, 404):
        return f"توجد مشكلة في مفتاح API أو اسم النموذج ({status}): {detail}"
    return f"خطأ في API ({status}): {detail}"


def get_api_key() -> str:
    """أعِد قيمة متغير البيئة GEMINI_API_KEY؛ وإن لم يكن مضبوطًا فاعرض التعليمات وأنهِ التشغيل."""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise SystemExit(
            "لم يُعثر على متغير البيئة GEMINI_API_KEY.\n"
            "1. سجّل GEMINI_API_KEY في GitHub Settings → Codespaces → Secrets،\n"
            "   واختر نسختك المتفرعة ضمن المستودعات المسموح لها باستخدام السرّ.\n"
            "2. إذا سجلته بعد تشغيل Codespaces، فأعد تشغيل Codespace.\n"
            "   (من أسفل اليسار: 'Codespaces' → 'Stop Current Codespace' → افتحه مجددًا)"
        )
    return key
