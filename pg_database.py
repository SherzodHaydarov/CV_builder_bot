import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, Text, Boolean, ForeignKey
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── DATABASE URL ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL topilmadi! .env faylida quyidagi formatda yozing:\n"
        "DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname"
    )

# 'postgresql://' → 'postgresql+asyncpg://' ga avtomatik o'girish
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# ── ENGINE & SESSION ─────────────────────────────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── MODELS ───────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)


# ── HELPERS ──────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """Jadvallarni yaratadi (agar mavjud bo'lmasa)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Ma'lumotlar bazasi jadvallari tayyor.")


async def get_or_create_user(tg_id: int, full_name: str | None = None) -> User:
    """Foydalanuvchini bazadan oladi yoki yangi yaratadi."""
    from sqlalchemy import select
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if user is None:
            user = User(tg_id=tg_id, full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Yangi foydalanuvchi yaratildi: tg_id={tg_id}")
        return user


async def save_resume(user_tg_id: int, content: str) -> Resume:
    """
    Resume ma'lumotlarini bazaga saqlaydi.
    Foydalanuvchi mavjud bo'lmasa, avval yaratadi.
    """
    # Foydalanuvchi bazada bo'lishini ta'minlaymiz
    await get_or_create_user(tg_id=user_tg_id)

    async with AsyncSessionLocal() as session:
        new_resume = Resume(user_tg_id=user_tg_id, content=content)
        session.add(new_resume)
        await session.commit()
        await session.refresh(new_resume)
        logger.info(f"Resume bazaga saqlandi: user_tg_id={user_tg_id}, id={new_resume.id}")
        return new_resume