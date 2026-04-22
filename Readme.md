# AI CV Builder Pro

FastAPI veb-sayt + Aiogram Telegram bot — bitta serverda.

## O'rnatish

```bash
# 1. Virtual muhit yarating (Python 3.10+)
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 2. Kutubxonalarni o'rnating
pip install -r requirements.txt

# 3. .env fayl yarating
cp .env.example .env
# .env faylini oching va qiymatlarni to'ldiring

# 4. Dasturni ishga tushiring
python main.py
```

Dastur `http://localhost:8000` da ishlaydi.

## Loyiha tuzilmasi

```
cv_builder/
├── main.py          ← FastAPI app + lifespan (bot + web birlashgan)
├── bot.py           ← Aiogram bot, FSM holatlari, handlerlar
├── ai_service.py    ← Groq AI: tarjima va yaxshilash
├── pdf.py           ← fpdf2 bilan PDF yaratish
├── pg_database.py   ← SQLAlchemy async + PostgreSQL modellari
├── models.py        ← Pydantic sxemalari
├── templates/
│   ├── index.html       ← CV forma
│   └── cv_result.html   ← Tayyor CV ko'rinishi
├── static/          ← CSS, favicon va boshqalar
├── requirements.txt
└── .env.example
```

## Bitta serverda ishlash tartibi

`main.py` da `lifespan` kontekst menejeri ishlatiladi:
- **Startup**: `init_db()` bazani tayyorlaydi, keyin `asyncio.create_task(dp.start_polling(bot))` bilan bot alohida task sifatida ishlaydi
- **Shutdown**: bot polling bekor qilinadi, bot sessiyasi yopiladi

Natijada `uvicorn` bitta portda (8000) ham HTTP so'rovlarini, ham Telegram bot'ni boshqaradi.