"""
Telegram Price Bot — всё в одном файле.
Автор: @Troudam
Запуск: python bot.py
"""

import asyncio
import logging
import os
from urllib.parse import quote

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web  # Добавлено для Render

# ═══════════════════════════════════════════════════════════
#  НАСТРОЙКИ — меняй здесь
# ═══════════════════════════════════════════════════════════
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН_ОТ_BOTFATHER")
ADMIN_USERNAME = "Troudam"  # твой аккаунт без @
# ═══════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ─────────────── Данные услуг ───────────────
SERVICES = {
    "slideshow": {
        "name": "Слайдшоу",
        "emoji": "🎬",
        "price": "15 ⭐",
        "desc": "Красивое слайдшоу с переходами, музыкой и эффектами из твоих фото и видео.",
        "order": "Хочу заказать слайдшоу!",
    },
    "edit_easy": {
        "name": "Лёгкий эдит",
        "emoji": "✂️",
        "price": "25 ⭐",
        "desc": "Быстрый монтаж: обрезка, базовые переходы, музыка.",
        "order": "Хочу заказать лёгкий эдит!",
    },
    "edit_medium": {
        "name": "Средний эдит",
        "emoji": "🎞️",
        "price": "35 ⭐",
        "desc": "Стильный монтаж: эффекты, синхронизация с музыкой, цветокоррекция.",
        "order": "Хочу заказать средний эдит!",
    },
    "edit_hard": {
        "name": "Сложный эдит",
        "emoji": "🎥",
        "price": "50 ⭐",
        "desc": "Профессиональный монтаж: сложные эффекты, анимации, уникальная стилистика.",
        "order": "Хочу заказать сложный эдит!",
    },
    "avatar": {
        "name": "Аватарка",
        "emoji": "🖼️",
        "price": "15 ⭐",
        "desc": "Индивидуальная аватарка в твоём стиле.",
        "order": "Хочу заказать аватарку!",
    },
    "quality": {
        "name": "Улучшение качества",
        "emoji": "✨",
        "price": "0 ⭐ (бесплатно)",
        "desc": "Улучшу качество твоего фото или видео абсолютно бесплатно.",
        "order": "Хочу улучшить качество!",
    },
    "watermark": {
        "name": "Убрать водяной знак",
        "emoji": "🧼",
        "price": "от 25 ⭐",
        "desc": "Удаление водяных знаков. Итоговая цена зависит от сложности — уточняй в ЛС.",
        "order": "Хочу убрать ватермарк!",
    },
}

MENU_TEXT = (
    "🌟 *ПРАЙС-ЛИСТ УСЛУГ* 🌟\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "Выбери услугу, чтобы узнать цену и оформить заказ 👇"
)


# ─────────────── Клавиатуры ───────────────
def main_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, s in SERVICES.items():
        kb.button(
            text=f"{s['emoji']} {s['name']} — {s['price']}",
            callback_data=f"svc:{key}",
        )
    kb.adjust(1)
    kb.row(
        InlineKeyboardButton(
            text="💬 Связаться с админом",
            url=f"https://t.me/{ADMIN_USERNAME}",
        )
    )
    return kb.as_markup()


def service_kb(order_text: str) -> InlineKeyboardMarkup:
    order_url = f"https://t.me/{ADMIN_USERNAME}?text={quote(order_text)}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Оформить заказ", url=order_url)],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back")],
        ]
    )


# ─────────────── Анимация прогресс-бара ───────────────
async def animate_progress(
    msg: Message,
    final_text: str,
    kb: InlineKeyboardMarkup,
    steps: int = 5,
    delay: float = 0.13,
):
    try:
        await bot.send_chat_action(chat_id=msg.chat.id, action="upload_photo")
    except Exception:
        pass

    bar = ["⬜"] * steps
    for i in range(steps):
        bar[i] = "🟦"
        try:
            await msg.edit_text(
                f"⚡ Загрузка...\n{''.join(bar)}",
                parse_mode=None,
            )
        except Exception:
            pass
        await asyncio.sleep(delay)

    try:
        await msg.edit_text(
            final_text,
            reply_markup=kb,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.warning(f"edit_text final failed: {e}")
        try:
            await msg.answer(final_text, reply_markup=kb, parse_mode="Markdown")
        except Exception:
            pass


# ─────────────── Хэндлеры ───────────────
@dp.message(CommandStart())
async def cmd_start(msg: Message):
    loading = await msg.answer("⚡ Загрузка меню...\n⬜⬜⬜⬜⬜")
    await animate_progress(loading, MENU_TEXT, main_menu_kb())


@dp.message(Command("price", "menu", "help"))
async def cmd_price(msg: Message):
    loading = await msg.answer("⚡ Загрузка меню...\n⬜⬜⬜⬜⬜")
    await animate_progress(loading, MENU_TEXT, main_menu_kb())


@dp.callback_query(F.data == "back")
async def cb_back(call: CallbackQuery):
    await call.answer("↩️ Возврат в меню")
    await animate_progress(
        call.message, MENU_TEXT, main_menu_kb(), steps=4, delay=0.08
    )


@dp.callback_query(F.data.startswith("svc:"))
async def cb_service(call: CallbackQuery):
    await call.answer("⏳ Открываю...")
    key = call.data.split(":", 1)[1]
    svc = SERVICES.get(key)
    if not svc:
        await call.answer("Услуга не найдена", show_alert=True)
        return

    text = (
        f"{svc['emoji']} *{svc['name']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *Цена:* {svc['price']}\n\n"
        f"📝 {svc['desc']}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Нажми кнопку ниже — откроется чат с @{ADMIN_USERNAME} "
        f"с уже готовым сообщением 🚀"
    )
    await animate_progress(
        call.message, text, service_kb(svc["order"]), steps=4, delay=0.1
    )


# ─────────────── Запуск ───────────────
async def main():
    if not BOT_TOKEN or "ВСТАВЬ_СЮДА" in BOT_TOKEN:
        raise SystemExit("❌ Токен не установлен!")
    
    # --- Фейковый веб-сервер для Render ---
    async def handle(request):
        return web.Response(text="Bot is alive")

    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    # --------------------------------------

    logger.info("🚀 Бот запущен. Нажми Ctrl+C для остановки.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit) as e:
        if str(e):
            print(e)
        logger.info("👋 Бот остановлен.")
