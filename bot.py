import os
import logging
from io import BytesIO

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BufferedInputFile
from dotenv import load_dotenv

from ai_service import improve_and_translate_resume
from pdf import create_pdf
from pg_database import save_resume

load_dotenv()

logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN topilmadi! .env faylini tekshiring.")

# Bot va Dispatcher — MemoryStorage FSM uchun
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

class CVForm(StatesGroup):
    fullname = State()
    contacts = State()
    education = State()
    skills = State()
    experience = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "<b>Xush kelibsiz!</b>\n\n"
        "Men sizga professional ingliz tilidagi CV yaratishda yordam beraman.\n\n"
        "<b>1-qadam:</b> To'liq ism va familiyangizni kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(CVForm.fullname)


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Hozir faol jarayon yo'q.")
        return
    await state.clear()
    await message.answer("Jarayon bekor qilindi. Qaytadan boshlash uchun /start yuboring.")


@router.message(CVForm.fullname)
async def process_name(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, ismingizni matn ko'rinishida kiriting.")
        return
    await state.update_data(fullname=message.text.strip())
    await message.answer(
        "Ajoyib!\n\n"
        "<b>2-qadam:</b> Aloqa ma'lumotlarini kiriting:\n"
        "<i>(Telefon, LinkedIn, GitHub va h.k.)</i>",
        parse_mode="HTML"
    )
    await state.set_state(CVForm.contacts)


@router.message(CVForm.contacts)
async def process_contacts(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, aloqa ma'lumotlarini kiriting.")
        return
    await state.update_data(contacts=message.text.strip())
    await message.answer(
        "Yaxshi!\n\n"
        "<b>3-qadam:</b> Ta'limingiz haqida yozing:\n"
        "<i>(Universitet, yo'nalish, bitirgan yili)</i>",
        parse_mode="HTML"
    )
    await state.set_state(CVForm.education)


@router.message(CVForm.education)
async def process_education(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, ta'lim ma'lumotlarini kiriting.")
        return
    await state.update_data(education=message.text.strip())
    await message.answer(
        "Zo'r!\n\n"
        "<b>4-qadam:</b> Texnik ko'nikmalaringizni yozing:\n"
        "<i>(masalan: Python, FastAPI, Docker, PostgreSQL)</i>",
        parse_mode="HTML"
    )
    await state.set_state(CVForm.skills)


@router.message(CVForm.skills)
async def process_skills(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, ko'nikmalaringizni kiriting.")
        return
    await state.update_data(skills=message.text.strip())
    await message.answer(
        "Juda yaxshi!\n\n"
        "<b>5-qadam (oxirgi):</b> Ish tajribangizni yozing:\n"
        "<i>O'zbek tilida yozishingiz mumkin — men professional inglizchaga o'giraman.</i>",
        parse_mode="HTML"
    )
    await state.set_state(CVForm.experience)


@router.message(CVForm.experience)
async def process_final(message: types.Message, state: FSMContext):
    if not message.text:
        await message.answer("Iltimos, tajribangizni kiriting.")
        return

    data = await state.get_data()
    user_exp = message.text.strip()
    user_edu = data.get("education", "")

    status_msg = await message.answer(
        "⏳ <b>AI ma'lumotlarni tahlil qilyapti...</b>\n"
        "Bu bir necha soniya vaqt olishi mumkin.",
        parse_mode="HTML"
    )

    try:
        # AI Translate & Improve (ikkalasini ham yaxshilaymiz)
        eng_exp = improve_and_translate_resume(user_exp, "Professional Experience")
        eng_edu = improve_and_translate_resume(user_edu, "Education")

        cv_data = {
            "full_name": data.get("fullname", ""),
            "contacts": data.get("contacts", ""),
            "education": eng_edu,
            "skills": data.get("skills", ""),
            "experience": eng_exp,
        }

        # PDF yaratish
        pdf_buffer: BytesIO = create_pdf(cv_data)
        pdf_buffer.seek(0)

        # Bazaga saqlash (foydalanuvchi ID bilan)
        assert message.from_user is not None, "Foydalanuvchi aniqlanmadi"
        
        await save_resume(
            user_tg_id=message.from_user.id,
            content=str(cv_data)
        )

        filename = f"{data.get('fullname', 'Resume').replace(' ', '_')}_Resume.pdf"
        document = BufferedInputFile(pdf_buffer.read(), filename=filename)

        await message.answer_document(
            document,
            caption=(
                "<b>Sizning professional CV-ngiz tayyor!</b>\n\n"
                "Fayl ingliz tilida tayyorlandi.\n"
                "Yangi CV yaratish uchun /start yuboring."
            ),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"CV yaratishda xatolik: {e}", exc_info=True)
        await message.answer(
            "Kechirasiz, jarayonda xatolik yuz berdi.\n"
            "Qaytadan urinib ko'rish uchun /start yuboring."
        )
    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass
        await state.clear()