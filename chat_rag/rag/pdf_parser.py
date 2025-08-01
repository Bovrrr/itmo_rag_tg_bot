"""
Модуль для парсинга PDF-файлов учебных программ и сохранения информации о дисциплинах в формате JSON.
"""

import json
import re

import pdfplumber


def parse_pdf_to_chunks(pdf_path, output_json, program_name):
    """
    Парсит PDF-файл с учебной программой и сохраняет найденные дисциплины в JSON.

    Аргументы:
        pdf_path (str): Путь к PDF-файлу.
        output_json (str): Путь к выходному JSON-файлу.
        program_name (str): Название программы (например, 'ai', 'ai_product').
    """
    chunks = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # регулярка для поиска строк с дисциплинами
            for line in text.split("\n"):
                # пример: 1 Воркшоп ... 3 108
                match = re.match(r"([\d,\s]+)\s+(.+?)\s+(\d+)\s+(\d+)", line)
                if match:
                    semesters_str = match.group(1)
                    semesters = [
                        int(s) for s in semesters_str.split(",") if s.strip().isdigit()
                    ]
                    name = match.group(2).strip()
                    course_credits = int(match.group(3))
                    hours = int(match.group(4))
                    chunks.append(
                        {
                            "semesters": semesters,
                            "name": name,
                            "credits": course_credits,
                            "hours": hours,
                            "program": program_name,
                        }
                    )
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def main():
    """
    Основная функция для парсинга двух учебных программ и сохранения результатов.
    """
    # Парсинг обеих программ
    parse_pdf_to_chunks(
        "data/ai.pdf",
        "data/chunks/ai_courses_chunks.json",
        "ai",
    )
    parse_pdf_to_chunks(
        "data/ai_product.pdf",
        "data/chunks/ai_product_courses_chunks.json",
        "ai_product",
    )


if __name__ == "__main__":
    main()
