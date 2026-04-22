import os
import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from bot import dp, bot, router
from ai_service import improve_and_translate_resume
from pg_database import init_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup va shutdown hodisalarini boshqarish."""
    # --- STARTUP ---
    logger.info("Dastur ishga tushmoqda...")
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor.")

    polling_task = asyncio.create_task(dp.start_polling(bot))
    logger.info("Telegram bot polling boshlandi.")

    yield  # Dastur bu yerda ishlaydi

    # --- SHUTDOWN ---
    logger.info("Dastur to'xtatilmoqda...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        logger.info("Bot polling to'xtatildi.")
    await bot.session.close()


app = FastAPI(title="AI CV Builder Pro", lifespan=lifespan)

# Static fayllar va templatelar
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ===================== WEB ROUTES =====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Asosiy sahifa - CV forma."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/generate", response_class=HTMLResponse)
async def generate_cv(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    contacts: str = Form(""),
    skills: str = Form(""),
    experience: str = Form(""),
):
    """Foydalanuvchi ma'lumotlarini qabul qilib, AI bilan CV yaratadi."""
    logger.info(f"Yangi CV so'rovi: {full_name}")

    # AI bilan tajribani yaxshilash va tarjima qilish
    improved_experience = improve_and_translate_resume(experience, "Professional Experience")

    cv_data = {
        "full_name": full_name,
        "email": email,
        "contacts": contacts,
        "skills": [s.strip() for s in skills.split(",") if s.strip()],
        "experience": improved_experience,
        "education": "",
    }

    return templates.TemplateResponse("cv_result.html", {"request": request, "cv": cv_data})


@app.get("/health")
async def health_check():
    return {"status": "running", "service": "CV Builder AI"}


# ===================== ENTRYPOINT =====================

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)