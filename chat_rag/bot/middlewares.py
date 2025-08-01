import logging
import os
from typing import Any, Awaitable, Callable, Dict, Optional, Union
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory

logger = logging.getLogger(__name__)


class DialogHistoryMiddleware(BaseMiddleware):
    """
    Middleware для хранения и управления историями диалогов пользователей.
    """

    def __init__(
        self, max_tokens: Optional[int] = None, memory_window: Optional[int] = None
    ):
        # Словарь для хранения памяти каждого пользователя
        self.user_memories: Dict[
            int, Union[ConversationBufferMemory, ConversationBufferWindowMemory]
        ] = {}

        # Настройки памяти из переменных окружения или параметров
        self.max_tokens = max_tokens or int(os.getenv("MEMORY_MAX_TOKENS", "2000"))
        self.memory_window = memory_window or int(os.getenv("MEMORY_WINDOW", "10"))
        self.return_messages = (
            os.getenv("MEMORY_RETURN_MESSAGES", "true").lower() == "true"
        )

        logger.info(
            "DialogHistoryMiddleware initialized: max_tokens=%d, memory_window=%d, return_messages=%s",
            self.max_tokens,
            self.memory_window,
            self.return_messages,
        )

    def _create_memory(
        self,
    ) -> Union[ConversationBufferMemory, ConversationBufferWindowMemory]:
        """Создает новую память для пользователя"""
        if self.memory_window > 0:
            logger.debug(
                "Creating ConversationBufferWindowMemory with window size: %d",
                self.memory_window,
            )
            return ConversationBufferWindowMemory(
                k=self.memory_window,
                return_messages=self.return_messages,
                memory_key="chat_history",
            )
        else:
            logger.debug("Creating ConversationBufferMemory")
            return ConversationBufferMemory(
                return_messages=self.return_messages, memory_key="chat_history"
            )

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Основной метод middleware.
        Добавляет память пользователя в данные обработчика.
        """
        # Проверяем, что это сообщение и у него есть пользователь
        if not isinstance(event, Message) or not event.from_user:
            logger.debug("Event is not a Message or has no user, skipping middleware")
            return await handler(event, data)

        user_id = event.from_user.id
        logger.debug("Processing message from user_id: %d", user_id)

        # Получаем или создаем память для пользователя
        if user_id not in self.user_memories:
            logger.info("Creating new memory for user_id: %d", user_id)
            self.user_memories[user_id] = self._create_memory()
        else:
            logger.debug("Using existing memory for user_id: %d", user_id)

        # Добавляем память пользователя в данные
        data["user_memory"] = self.user_memories[user_id]
        data["update_memory"] = self._create_memory_updater(user_id)

        logger.debug("Memory data added to handler for user_id: %d", user_id)
        return await handler(event, data)

    def _create_memory_updater(self, user_id: int):
        """
        Создает функцию для обновления памяти пользователя.
        """

        def update_memory(human_message: str, ai_message: str):
            """
            Обновляет память пользователя новыми сообщениями.

            Args:
                human_message: Сообщение пользователя
                ai_message: Ответ бота
            """
            try:
                memory = self.user_memories[user_id]
                memory.save_context({"input": human_message}, {"output": ai_message})
                logger.debug(
                    "Memory updated for user_id: %d, human_msg_len: %d, ai_msg_len: %d",
                    user_id,
                    len(human_message),
                    len(ai_message),
                )
            except Exception as e:
                logger.error(
                    "Error updating memory for user_id: %d - %s",
                    user_id,
                    str(e),
                    exc_info=True,
                )

        return update_memory

    def clear_user_memory(self, user_id: int):
        """
        Очищает память указанного пользователя.

        Args:
            user_id: ID пользователя
        """
        if user_id in self.user_memories:
            self.user_memories[user_id].clear()
            logger.info("Memory cleared for user_id: %d", user_id)
        else:
            logger.warning(
                "Attempted to clear memory for non-existent user_id: %d", user_id
            )

    def get_user_memory(
        self, user_id: int
    ) -> Union[ConversationBufferMemory, ConversationBufferWindowMemory]:
        """
        Возвращает память пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            ConversationBufferMemory или ConversationBufferWindowMemory: Память пользователя
        """
        if user_id not in self.user_memories:
            logger.info(
                "Creating new memory for user_id: %d (via get_user_memory)", user_id
            )
            self.user_memories[user_id] = self._create_memory()
        else:
            logger.debug("Retrieved existing memory for user_id: %d", user_id)
        return self.user_memories[user_id]

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику использования памяти.

        Returns:
            Словарь со статистикой
        """
        stats = {
            "total_users": len(self.user_memories),
            "max_tokens": self.max_tokens,
            "memory_window": self.memory_window,
            "return_messages": self.return_messages,
        }
        logger.debug("Memory stats requested: %s", stats)
        return stats
