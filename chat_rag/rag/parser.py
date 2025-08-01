"""
Модуль для извлечения и парсинга структурированных данных с веб-страниц магистерских программ ИТМО
через JSON, встроенный в тег <script id="__NEXT_DATA__" type="application/json">.
Содержит утилиты для получения всех ключей вложенного JSON и извлечения основных полей:
название программы, даты экзаменов, квоты, дисциплины и полезные ссылки.

Функции:
    get_next_data_json(url): Загружает веб-страницу по URL и парсит JSON из __NEXT_DATA__.
    flatten_json_keys(d, prefix=""): Рекурсивно собирает все ключи из вложенного JSON.
    extract_fields(page_props): Извлекает основные поля из словаря pageProps: название, даты экзаменов,
        квоты, дисциплины и важные ссылки.

Константы:
    URLS: Список URL магистерских программ ИТМО для парсинга.
"""

import json
import os

import requests
from bs4 import BeautifulSoup

URLS = [
    "https://abit.itmo.ru/program/master/ai",
    "https://abit.itmo.ru/program/master/ai_product",
]


def get_next_data_json(url):
    """
    Загружает веб-страницу по указанному URL и извлекает JSON из тега <script id="__NEXT_DATA__">.
    Возвращает распарсенный объект JSON.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CopilotBot/1.0)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not script_tag:
        print(html[:1000])  # Выводим первые 1000 символов для диагностики
        raise ValueError(f"__NEXT_DATA__ script not found for {url}")
    script_content = script_tag.get_text()
    if script_content is None:
        raise ValueError(f"__NEXT_DATA__ script content is empty for {url}")
    return json.loads(script_content)


def extract_and_save_documents(url, output_dir="data"):
    """
    Извлекает нужные поля из JSON по url, формирует документы-чанки и сохраняет их в output_dir.
    """
    data = get_next_data_json(url)
    page_props = data["props"]["pageProps"]
    api_program = page_props.get("apiProgram", {})
    json_program = page_props.get("jsonProgram", {})

    # Документы из apiProgram
    api_docs = []
    api_docs.append({"type": "title", "text": api_program["title"], "source": url})
    api_docs.append(
        {"type": "faculties", "text": str(api_program["faculties"]), "source": url}
    )
    api_docs.append(
        {
            "type": "educationCost",
            "text": str(api_program["educationCost"]),
            "source": url,
        }
    )
    # directions[0]['disciplines']
    directions = api_program.get("directions", [])
    if directions and isinstance(directions, list) and "disciplines" in directions[0]:
        api_docs.append(
            {
                "type": "disciplines",
                "text": str(directions[0]["disciplines"]),
                "source": url,
            }
        )
    if "hasAccreditation" in api_program:
        api_docs.append(
            {
                "type": "hasAccreditation",
                "text": str(api_program["hasAccreditation"]),
                "source": url,
            }
        )

    # Документы из jsonProgram
    json_docs = []
    about_desc = json_program.get("about", {}).get("desc")
    if about_desc:
        json_docs.append({"type": "about_desc", "text": about_desc, "source": url})
    career_lead = json_program.get("career", {}).get("lead")
    if career_lead:
        json_docs.append({"type": "career_lead", "text": career_lead, "source": url})
    achievements = json_program.get("achievements")
    if achievements:
        json_docs.append(
            {"type": "achievements", "text": str(achievements), "source": url}
        )

    # FAQ: каждая пара вопрос-ответ отдельный документ
    faq = json_program.get("faq", [])
    faq_docs = []
    for item in faq:
        question = item.get("question")
        answer = item.get("answer")
        if question and answer:
            faq_docs.append(
                {"type": "faq", "question": question, "answer": answer, "source": url}
            )

    # Сохраняем все чанки по одной программе в один файл
    os.makedirs(output_dir, exist_ok=True)
    # Имя файла: <program>_chunks.json, где <program> - последний сегмент url
    program_name = url.rstrip("/").split("/")[-1]
    fname = os.path.join(output_dir, f"{program_name}_chunks.json")

    # Добавляем поле 'program' в каждый чанк
    def add_program_field(docs):
        return [dict(doc, program=program_name) for doc in docs]

    all_docs = (
        add_program_field(api_docs)
        + add_program_field(json_docs)
        + add_program_field(faq_docs)
    )
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("Запуск парсинга и сохранения документов...")
    for url in URLS:
        try:
            print(f"Обработка: {url}")
            extract_and_save_documents(url, output_dir="data/chunks")
            print(f"Документы для {url} сохранены в папку data/chunks.")
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            print(f"Ошибка при обработке {url}: {e}")
