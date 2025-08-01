from typing import Optional, Callable, Union
from aiogram import Router, types
from aiogram.filters import Command
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory

from chat_rag.rag.rag_agent import process_message

router = Router()


@router.message(Command("start"))
async def start_handler(
    message: types.Message,
    user_memory: Optional[
        Union[ConversationBufferMemory, ConversationBufferWindowMemory]
    ] = None,
):
    """Обработчик команды /start"""
    await message.answer(
        "Здравствуйте! Я могу ответить на вопросы по магистерским программам ИТМО: 'Искусственный интеллект' и 'Управление ИИ-продуктами/AI Product'.\n\nНапишите свой вопрос или воспользуйтесь /help."
    )


@router.message(Command("help"))
async def help_handler(
    message: types.Message,
    user_memory: Optional[
        Union[ConversationBufferMemory, ConversationBufferWindowMemory]
    ] = None,
):
    """Обработчик команды /help"""
    await message.answer(
        "Доступные команды:\n/start — начать работу\n/help — справка\n/clear — очистить историю диалога\n/stats — статистика памяти\nПросто напишите свой вопрос для получения рекомендаций."
    )


@router.message(Command("clear"))
async def clear_handler(
    message: types.Message,
    user_memory: Optional[
        Union[ConversationBufferMemory, ConversationBufferWindowMemory]
    ] = None,
):
    """Обработчик команды /clear для очистки истории диалога"""
    if user_memory:
        user_memory.clear()
        await message.answer("История диалога очищена! Можете начать новый разговор.")
    else:
        await message.answer("Не удалось очистить историю диалога.")


@router.message(Command("stats"))
async def stats_handler(message: types.Message):
    """Обработчик команды /stats для получения статистики памяти"""
    # Получаем middleware из бота для вывода статистики
    # Эта команда может быть полезна для администраторов
    await message.answer("Статистика памяти диалогов временно недоступна.")


@router.message()
async def common_messages_handler(
    message: types.Message,
    user_memory: Optional[
        Union[ConversationBufferMemory, ConversationBufferWindowMemory]
    ] = None,
    update_memory: Optional[Callable[[str, str], None]] = None,
):
    """Обработчик обычных сообщений с использованием памяти пользователя"""
    # Используем память пользователя, переданную через middleware
    if not user_memory:
        user_memory = ConversationBufferMemory()

    # Проверяем, что text не None
    user_text = message.text or ""

    response = process_message(user_text, user_memory)

    # Обновляем память пользователя после получения ответа
    if update_memory:
        update_memory(user_text, response)

    await message.answer(response)
