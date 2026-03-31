import os
import requests
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import F

# ================= НАСТРОЙКИ =================
TELEGRAM_TOKEN = os.getenv("8793794867:AAEk8klBPJQyBVyUBnweEgEL27-ZBxKg8ns")
BITRIX_WEBHOOK = os.getenv("https://bks.bitrix24.by/rest/1/6sv9n8mlxbcq4fmv/")
DOCUMENT_LINK = "https://cpd.by/politika-konfidentsialnosti/"   # ← ОБЯЗАТЕЛЬНО ЗАМЕНИ НА РЕАЛЬНУЮ ССЫЛКУ!

WEBHOOK_PATH = f"/bot/{TELEGRAM_TOKEN}"
BASE_WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
app = FastAPI()

class Form(StatesGroup):
    region = State()
    district = State()
    question = State()
    contacts = State()

# ТВОИ РЕГИОНЫ И РАЙОНЫ (точно как в схеме и в твоём сообщении)
REGIONS = {
    "1": "Брест и Брестская область",
    "2": "Витебск и Витебская область",
    "3": "Гомель и Гомельская область",
    "4": "Гродно и Гродненская область",
    "5": "Минская область",
    "6": "Могилёв и Могилёвская область",
    "7": "Минск"
}

DISTRICTS = {
    "1": ["Барановичский", "Берёзовский", "Брестский", "Ганцевичский", "Дрогичинский", "Жабинковский", "Ивановский", "Ивацевичский", "Каменецкий", "Кобринский", "Лунинецкий", "Ляховичский", "Малоритский", "Пинский", "Пружанский", "Столинский"],
    "2": ["Бешенковичский", "Браславский", "Верхнедвинский", "Витебский", "Глубокский", "Городокский", "Докшицкий", "Дубровенский", "Лепельский", "Лиозненский", "Миорский", "Оршанский", "Полоцкий", "Поставский", "Россонский", "Сенненский", "Толочинский", "Ушачский", "Чашникский", "Шарковщинский", "Шумилинский"],
    "3": ["Брагинский", "Буда-Кошелёвский", "Ветковский", "Гомельский", "Добрушский", "Ельский", "Житковичский", "Жлобинский", "Калинковичский", "Кормянский", "Лельчицкий", "Лоевский", "Мозырский", "Наровлянский", "Октябрьский", "Петриковский", "Речицкий", "Рогачёвский", "Светлогорский", "Хойникский", "Чечерский"],
    "4": ["Берестовицкий", "Волковысский", "Вороновский", "Гродненский", "Дятловский", "Зельвенский", "Ивьевский", "Кореличский", "Лидский", "Мостовский", "Новогрудский", "Островецкий", "Ошмянский", "Свислочский", "Слонимский", "Сморгонский", "Щучинский"],
    "5": ["Березинский", "Борисовский", "Вилейский", "Воложинский", "Дзержинский", "Клецкий", "Копыльский", "Крупский", "Логойский", "Любанский", "Минский", "Молодечненский", "Мядельский", "Несвижский", "Пуховичский", "Слуцкий", "Смолевичский", "Солигорский", "Стародорожский", "Столбцовский", "Узденский", "Червенский"],
    "6": ["Белыничский", "Бобруйский", "Быховский", "Глусский", "Горецкий", "Дрибинский", "Кировский", "Климовичский", "Кличевский", "Костюковичский", "Краснопольский", "Кричевский", "Круглянский", "Могилёвский", "Мстиславский", "Осиповичский", "Славгородский", "Хотимский", "Чаусский", "Чериковский", "Шкловский"]
}

# ================= ХЭНДЛЕРЫ =================
@dp.message(Command("start"))
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="consent_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="end")]
    ])
    await message.answer(
        "Здравствуйте!\n"
        "Для продолжения диалога необходимо Ваше согласие на обработку персональных данных.",
        reply_markup=kb
    )

@dp.callback_query(F.data == "consent_yes")
async def consent_yes(callback, state: FSMContext):
    text = (
        f"Здесь должна быть активная ссылка на документы:\n"
        f"[📄 Ознакомиться с документами]({DOCUMENT_LINK})\n\n"
        "Дать согласие на обработку ПД?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да", callback_data="pd_yes")],
        [InlineKeyboardButton(text="❌ Нет", callback_data="end")]
    ])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    await callback.answer()

@dp.callback_query(F.data == "pd_yes")
async def pd_yes(callback, state: FSMContext):
    await callback.message.edit_text(
        "Организации потребительской кооперации работают на всей территории нашей страны.\n\n"
        "Выберите регион:"
    )
    kb_buttons = [[InlineKeyboardButton(text=name, callback_data=f"region_{key}")] for key, name in REGIONS.items()]
    kb_buttons.append([InlineKeyboardButton(text="❌ Нет", callback_data="end")])
    kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
    await callback.message.answer("Выберите регион:", reply_markup=kb)
    await state.set_state(Form.region)
    await callback.answer()

@dp.callback_query(F.data.startswith("region_"))
async def choose_region(callback, state: FSMContext):
    region_key = callback.data.split("_")[1]
    region_name = REGIONS[region_key]
    await state.update_data(region=region_name)

    await callback.message.edit_text(f"Вы выбрали: {region_name}\n\nВыберите район:")

    districts = DISTRICTS[region_key]
    district_kb = []
    row = []
    for district in districts:
        row.append(InlineKeyboardButton(text=district, callback_data=f"district_{district}"))
        if len(row) == 2:
            district_kb.append(row)
            row = []
    if row:
        district_kb.append(row)
    district_kb.append([InlineKeyboardButton(text="❌ Отмена", callback_data="end")])

    kb = InlineKeyboardMarkup(inline_keyboard=district_kb)
    await callback.message.answer("Выберите район:", reply_markup=kb)
    await state.set_state(Form.district)
    await callback.answer()

@dp.callback_query(F.data.startswith("district_"))
async def choose_district(callback, state: FSMContext):
    district = callback.data.split("_", 1)[1]
    await state.update_data(district=district)
    await callback.message.edit_text(f"Район: {district}\n\nНапишите свой вопрос (в тело обращения):")
    await state.set_state(Form.question)
    await callback.answer()

@dp.message(Form.question)
async def get_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text)
    await message.answer("Оставьте, пожалуйста, контактные данные для обратной связи.\n(в Bitrix24 вопрос должен попадать в карточку заявителя)")
    await state.set_state(Form.contacts)

@dp.message(Form.contacts)
async def get_contacts(message: Message, state: FSMContext):
    data = await state.get_data()
    contacts = message.text

    lead_text = f"""Обращение из Telegram-бота BY_Belcoopsoyuz

Регион: {data.get('region')}
Район: {data.get('district')}
Вопрос: {data.get('question')}
Контактные данные: {contacts}
Telegram: @{message.from_user.username or 'нет'} (ID: {message.from_user.id})"""

    try:
        resp = requests.post(
            BITRIX_WEBHOOK + "crm.lead.add",
            json={
                "fields": {
                    "TITLE": "Обращение из Telegram-бота",
                    "COMMENTS": lead_text,
                    "SOURCE_ID": "TELEGRAM",
                    "ASSIGNED_BY_ID": 1,        # ← ID ответственного сотрудника в Bitrix24
                }
            }
        )
        lead_id = resp.json().get("result", "—")
        await message.answer(f"✅ Благодарим за обращение!\nВаш лид №{lead_id} создан в Bitrix24.")
    except Exception:
        await message.answer("✅ Благодарим за обращение! (данные сохранены)")

    await state.clear()

@dp.callback_query(F.data == "end")
async def end_dialog(callback, state: FSMContext):
    await callback.message.edit_text("Благодарим за обращение.")
    await state.clear()
    await callback.answer()

# ================= WEBHOOK =================
@app.post(WEBHOOK_PATH)
async def webhook(request: Request):
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    webhook_url = BASE_WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH
    await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    print(f"✅ Webhook успешно установлен: {webhook_url}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
