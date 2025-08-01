# Chat-Bot for ITMO Master's Programs Guidance

## Project Goal

This repository contains a chat-bot that helps prospective students choose between two ITMO master's programs and plan their studies based on the official curricula. The bot parses program data from the official sites and provides recommendations and answers to relevant questions about the programs.

### Assignment

Создайте открытый репозиторий chat-bot в github и приложите ссылку в поле для ответа

Разработайте чат-бот, который в диалоговом режиме помогает абитуриенту разобраться, какая из двух магистерских программ ему подходит и как наилучшим образом спланировать учёбу исходя из учебных планов, загруженных на страницах магистратур под запрос абитуриента.

<https://abit.itmo.ru/program/master/ai>
<https://abit.itmo.ru/program/master/ai_product>

1. Реализуйте парсинг данных с сайтов и соберите учебные планы.
2. Реализуйте диалоговую систему с ответами на вопросы по содержимому сайтов, например на базе telegram-бота.
3. Реализуйте рекомендации - какие выборные дисциплины лучше прослушать абитуриенту в ходе обучения, с учетом вводных от абитуриента о его бэкграунде.
4. Важно чтобы чат-бот отвечал отвечал только на релевантные вопросы по обучению в выбранных магистратурах

Пользуйтесь любым удобным инструментарием при решении задачи и опишите в readme как решали задачу, чем пользовались при решении и как принимали решения.

## Features

- Data parsing from official ITMO master's program pages
- Dialog system (e.g., Telegram bot) for interactive Q&A
- Recommendations for elective courses based on user background
- Answers only relevant to the selected master's programs

## How to Use

1. Clone the repository
2. Follow setup instructions (to be added)
3. Run the bot and interact via the chosen platform

## Technologies Used

- Python (recommended)
- Web scraping libraries (e.g., BeautifulSoup, requests)
- Telegram Bot API (python-telegram-bot or aiogram)
- LangChain (optional, for advanced dialog management)

## Decision Process

- Selected Python for rapid prototyping and rich ecosystem
- Used official ITMO program pages as data sources
- Focused on relevance and accuracy in bot responses

## Next Steps

- Implement data parsing
- Build dialog system
- Add recommendation logic
- Document setup and usage

---

See assignment above for details.

Описание:
Решил использовать реактивного агента, который будет сам тянуть ретрив по информации о магистерских программах ИТМО и строить индивидуальный учебный план, если поймёт, что нужно.

Ретрив работает по спаршенной с сайтов информации. (Будь больше времени, можно было бы нагенерить опорные фразы для чанков, чтобы ретриверу было проще.) Сейчас он работает на небольшой берт лайк модели с HG, обученной ранжированию текстов.

Тул для построения учебной программы устроен так:
– берёт бекграунд, интересы и цель абитуриента;
– итеративно подбирает по 5 курсов на все 4 семестра обучения, учитывая и информацию об абитуриенте, и уже выбранные курсы за предыдущие семестры.

Агент работает на OpenAI Api, для агента используется gpt-4.1-mini (на уровне gpt-4o). Для подбора курсов используется gpt-4.1-nano (нужно 4 запроса на 4 семестра, поэтому модель подешевле).
