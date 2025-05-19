import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from openai import OpenAI

# Инициализация клиента DeepSeek
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

# Загрузка промпта
with open("prompts/spirit_prompt.txt", encoding="utf-8") as f:
    PROMPT = f.read()

# Загрузка FAQ
with open("data/faq.json", encoding="utf-8") as f:
    FAQ_LIST = json.load(f)

# Состояния пользователей
user_states = {}
user_data = {}

# Главное меню
MENU = [["📅 Записаться", "📖 О практиках"], ["🌿 Совет духа", "❓ FAQ", "📍 Контакты"]]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать в Центр «Ясность» 🌿\n\n"
        "Это пространство, где ты можешь восстановить связь с собой. "
        "Я — дух-помощник. Чем могу быть полезен?",
        reply_markup=ReplyKeyboardMarkup(MENU, resize_keyboard=True)
    )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    msg = update.message.text.strip()

    # Запись
    if user_id in user_states:
        state = user_states[user_id]
        if state == "awaiting_name":
            user_data[user_id] = {"name": msg}
            user_states[user_id] = "awaiting_contact"
            await update.message.reply_text("Как с тобой связаться? Телефон или @юзернейм.")
            return
        elif state == "awaiting_contact":
            name = user_data[user_id]["name"]
            contact = msg
            await update.message.reply_text("Спасибо, я передам твой запрос ✨ Мы скоро с тобой свяжемся.")
            await context.bot.send_message(chat_id=int(os.getenv("ADMIN_CHAT_ID")), text=f"📩 Заявка на сессию:\nИмя: {name}\nКонтакт: {contact}")
            del user_states[user_id]
            del user_data[user_id]
            return

    # Команды
    text = msg.lower()
    if "записаться" in text:
        user_states[user_id] = "awaiting_name"
        await update.message.reply_text("Как тебя зовут?")
        return
    elif "практик" in text:
        await update.message.reply_text(
            "🧘 Мы проводим:\n"
            "- шаманские сессии\n- телесные практики\n- дыхательные практики\n- сновидения\n\n"
            "Расскажи, что ты чувствуешь — я помогу с выбором."
        )
        return
    elif "faq" in text or "часто" in text:
        response = "\n\n".join([f"❓ {item['question']}\n💬 {item['answer']}" for item in FAQ_LIST])
        await update.message.reply_text(response)
        return
    elif "контакт" in text:
        await update.message.reply_text(
            "📍 Центр «Ясность»:\nМосква, ул. Тишины, д. 5\n"
            "📞 +7 999 123-45-67\n📧 yasnost@center.ru"
        )
        return
    elif "совет духа" in text:
        await update.message.reply_text("🔮 Сейчас обращусь к духу...")
        await send_ai_reply(update, system_prompt=PROMPT, user_prompt="Дай образный совет для идущего по Пути.")
        return
    elif "что за центр" in text or "чем занимаетесь" in text:
        await update.message.reply_text(
            "Центр «Ясность» — это место встречи с собой. "
            "Мы помогаем восстановить контакт с телом, успокоить ум и найти опору. "
            "Работаем через дыхание, сновидения, телесность и образы. "
            "Если расскажешь, как ты себя чувствуешь — я подскажу путь."
        )
        return

    # Обращение к AI
    await send_ai_reply(update, system_prompt=PROMPT, user_prompt=msg)

async def send_ai_reply(update, system_prompt, user_prompt):
    completion = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    await update.message.reply_text(completion.choices[0].message.content)