from aiogram import Router, types
from aiogram.filters import Command
from langchain.memory import ConversationBufferMemory

from chat_rag.rag.rag_agent import process_message

router = Router()


@router.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Здравствуйте! Я могу ответить на вопросы по магистерским программам ИТМО: 'Искусственный интеллект' и 'Управление ИИ-продуктами/AI Product'.\n\nНапишите свой вопрос или воспользуйтесь /help."
    )


@router.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        "Доступные команды:\n/start — начать работу\n/help — справка\nПросто напишите свой вопрос для получения рекомендаций."
    )


@router.message()
async def common_messages_handler(message: types.Message):
    # Можно использовать user_id для индивидуальной памяти, если потребуется
    memory = ConversationBufferMemory()
    response = process_message(message.text, memory)
    await message.answer(response)
