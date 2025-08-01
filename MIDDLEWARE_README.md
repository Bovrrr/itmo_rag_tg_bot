# Dialog History Middleware

## Описание

`DialogHistoryMiddleware` - это middleware для aiogram, который автоматически сохраняет и управляет историями диалогов пользователей.

## Возможности

- **Индивидуальная память для каждого пользователя**: Каждый пользователь имеет свою собственную историю диалога
- **Автоматическое сохранение контекста**: Все сообщения пользователя и ответы бота автоматически сохраняются
- **Настраиваемые типы памяти**: Поддержка `ConversationBufferMemory` и `ConversationBufferWindowMemory`
- **Простая интеграция**: Легко подключается к существующим обработчикам

## Использование

### Подключение middleware

```python
from middlewares import DialogHistoryMiddleware

dp = Dispatcher()
dp.message.middleware(DialogHistoryMiddleware())
```

### В обработчиках

```python
@router.message()
async def message_handler(
    message: types.Message, 
    user_memory: Optional[Union[ConversationBufferMemory, ConversationBufferWindowMemory]] = None,
    update_memory: Optional[Callable[[str, str], None]] = None
):
    # Используем память пользователя
    response = process_message(message.text, user_memory)
    
    # Обновляем память после получения ответа
    if update_memory:
        update_memory(message.text, response)
    
    await message.answer(response)
```

## Конфигурация

Настройки можно задать через переменные окружения в `.env`:

```env
# Максимальное количество токенов для памяти
MEMORY_MAX_TOKENS=2000

# Размер окна для ConversationBufferWindowMemory (0 = использовать ConversationBufferMemory)
MEMORY_WINDOW=10

# Возвращать ли сообщения в формате Message
MEMORY_RETURN_MESSAGES=true
```

## Команды бота

- `/start` - Начать работу с ботом
- `/help` - Показать справку
- `/clear` - Очистить историю диалога текущего пользователя
- `/stats` - Показать статистику использования памяти

## API методы

### DialogHistoryMiddleware

- `clear_user_memory(user_id: int)` - Очистить память пользователя
- `get_user_memory(user_id: int)` - Получить память пользователя
- `get_memory_stats()` - Получить статистику использования памяти

## Примеры

### Очистка памяти пользователя

```python
middleware = DialogHistoryMiddleware()
middleware.clear_user_memory(user_id=12345)
```

### Получение статистики

```python
stats = middleware.get_memory_stats()
print(f"Всего пользователей: {stats['total_users']}")
```
