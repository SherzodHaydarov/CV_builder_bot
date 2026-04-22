import os
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_client: Groq | None = None


def _get_client() -> Groq:
    """Groq clientini lazy initialization bilan olish."""
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY topilmadi! .env faylini tekshiring.")
        _client = Groq(api_key=api_key)
    return _client


def improve_and_translate_resume(text: str, field_name: str) -> str:
    """
    O'zbek tilidagi matnni professional ingliz tiliga tarjima qiladi
    va CV uchun yaxshilaydi.
    
    Args:
        text: O'zbek tilidagi matn
        field_name: Maydon nomi (masalan: "Professional Experience")
    
    Returns:
        Professional ingliz tilidagi matn
    """
    if not text or not text.strip():
        return ""

    prompt = f"""You are a Professional Resume Expert and Translator.

Task: Translate the following text related to "{field_name}" into professional Business English for a resume/CV.

Instructions:
1. Use high-impact action verbs (e.g., 'Engineered', 'Orchestrated', 'Spearheaded', 'Developed', 'Led').
2. Focus on achievements and quantifiable results, not just duties.
3. Keep the tone corporate, formal, and concise.
4. Structure the content clearly with bullet points if appropriate.
5. Return ONLY the translated/improved text — no explanations, no preamble.

Input Text: {text}

Professional English Output:"""

    try:
        client = _get_client()
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        content = completion.choices[0].message.content
        result = content.strip() if content else ""
        logger.info(f"AI tarjima muvaffaqiyatli: {field_name}")
        return result

    except Exception as e:
        logger.error(f"AI xatoligi ({field_name}): {e}", exc_info=True)
        return text  # Xato bo'lsa asl matnni qaytaradi